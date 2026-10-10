"""Service for parsing, validating, and sanitizing recipient CSV files."""
import io
import re
from typing import Dict, Any, List, Optional
import pandas as pd
from email_validator import validate_email, EmailNotValidError
from backend.config import get_settings

settings = get_settings()

COMMON_EMAIL_COLUMN_NAMES = [
    "email",
    "email_address",
    "emailaddress",
    "recipient",
    "recipients",
    "mail",
    "target_email",
    "contact_email",
]


def detect_email_column(df: pd.DataFrame, preferred_column: Optional[str] = None) -> Optional[str]:
    """Identify the column holding email addresses."""
    if preferred_column and preferred_column in df.columns:
        return preferred_column

    # Normalize existing column names for matching
    col_map = {str(col).strip().lower(): col for col in df.columns}

    for candidate in COMMON_EMAIL_COLUMN_NAMES:
        if candidate in col_map:
            return col_map[candidate]

    # If no exact match, inspect columns whose names contain 'email' or 'mail'
    for col_lower, original in col_map.items():
        if "email" in col_lower or "mail" in col_lower:
            return original

    # Fallback to the first column if dataframe has columns
    if len(df.columns) > 0:
        return df.columns[0]

    return None


def parse_and_validate_csv(
    file_content: bytes,
    preferred_column: Optional[str] = None,
    deduplicate: bool = True,
) -> Dict[str, Any]:
    """
    Parse a CSV byte stream, identify recipients, validate formatting,
    and produce structured validation analytics.
    """
    # 1. Enforce max file size check
    max_bytes = settings.MAX_CSV_SIZE_MB * 1024 * 1024
    if len(file_content) > max_bytes:
        raise ValueError(f"CSV file exceeds maximum allowed size of {settings.MAX_CSV_SIZE_MB}MB.")

    # 2. Decode text safely (utf-8 with fallback)
    text = None
    for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            text = file_content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise ValueError("Unable to decode CSV file. Please provide a standard UTF-8 encoded CSV.")

    # Count empty raw lines in CSV
    raw_lines = text.splitlines()
    empty_rows_count = sum(1 for line in raw_lines if not line.strip())

    # 3. Read into Pandas
    try:
        df = pd.read_csv(io.StringIO(text), skip_blank_lines=True, dtype=str)
    except Exception as exc:
        raise ValueError(f"Failed to parse CSV format: {str(exc)}")

    total_rows = len(df)
    if total_rows == 0:
        return {
            "total_rows": 0,
            "empty_rows_count": empty_rows_count,
            "detected_column": None,
            "valid_recipients": [],
            "invalid_recipients": [],
            "duplicate_count": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "preview_data": [],
        }

    detected_column = detect_email_column(df, preferred_column)
    if not detected_column:
        raise ValueError("Could not find an email column in the uploaded CSV.")

    valid_recipients: List[str] = []
    invalid_recipients: List[Dict[str, Any]] = []
    seen_normalized: set = set()
    duplicate_count = 0

    for idx, row in df.iterrows():
        row_number = idx + 2  # 1-indexed including header
        raw_val = row.get(detected_column)

        if pd.isna(raw_val) or str(raw_val).strip() == "":
            invalid_recipients.append({
                "row": row_number,
                "email": "",
                "reason": "Missing / empty email address in row",
            })
            continue

        candidate_email = str(raw_val).strip()

        # Validate with email-validator
        try:
            # check_deliverability=False avoids DNS lookups in unit tests & offline envs
            validated = validate_email(candidate_email, check_deliverability=False)
            normalized_email = validated.normalized

            if normalized_email in seen_normalized:
                duplicate_count += 1
                if not deduplicate:
                    valid_recipients.append(normalized_email)
            else:
                seen_normalized.add(normalized_email)
                valid_recipients.append(normalized_email)

        except EmailNotValidError as err:
            invalid_recipients.append({
                "row": row_number,
                "email": candidate_email,
                "reason": str(err),
            })
        except Exception as exc:
            invalid_recipients.append({
                "row": row_number,
                "email": candidate_email,
                "reason": f"Invalid syntax: {str(exc)}",
            })

    # Enforce campaign recipients limit
    if len(valid_recipients) > settings.MAX_CAMPAIGN_RECIPIENTS:
        raise ValueError(
            f"Campaign contains {len(valid_recipients)} valid recipients, which exceeds the limit of {settings.MAX_CAMPAIGN_RECIPIENTS}."
        )

    # Convert preview data safely to dicts for UI
    preview_data = df.head(10).fillna("").to_dict(orient="records")

    return {
        "total_rows": total_rows,
        "empty_rows_count": empty_rows_count,
        "detected_column": str(detected_column),
        "valid_recipients": valid_recipients,
        "invalid_recipients": invalid_recipients,
        "duplicate_count": duplicate_count,
        "valid_count": len(valid_recipients),
        "invalid_count": len(invalid_recipients),
        "preview_data": preview_data,
    }
