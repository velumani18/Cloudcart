"""Service for dispatching individual notification requests to the external AWS API Gateway."""
import logging
from typing import Dict, Any, Optional
import httpx
from backend.config import get_settings
from backend.models import NotificationEventStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class DispatchResult:
    """Encapsulates outcome of an AWS API Gateway dispatch."""

    def __init__(
        self,
        status: NotificationEventStatus,
        external_http_status: Optional[int] = None,
        notification_id: Optional[str] = None,
        message: str = "",
        error_message: Optional[str] = None,
    ):
        self.status = status
        self.external_http_status = external_http_status
        self.notification_id = notification_id
        self.message = message
        self.error_message = error_message


async def send_to_aws_gateway(
    recipient: str,
    subject: str,
    body: str,
    event_type: str,
    client: Optional[httpx.AsyncClient] = None,
) -> DispatchResult:
    """
    Dispatch an event-driven notification to the AWS API Gateway endpoint.
    Strictly adheres to: 1 recipient per POST call.
    """
    payload = {
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "event_type": event_type,
    }
    headers = {"Content-Type": "application/json"}
    url = settings.AWS_NOTIFICATION_URL

    should_close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS)
        should_close_client = True

    try:
        response = await client.post(url, json=payload, headers=headers)
        status_code = response.status_code

        response_data = {}
        try:
            response_data = response.json()
        except Exception:
            pass

        # Extract notification_id safely if present
        notification_id = None
        if isinstance(response_data, dict):
            notification_id = (
                response_data.get("notification_id")
                or response_data.get("id")
                or response_data.get("notificationId")
                or response_data.get("messageId")
            )
            if notification_id is not None:
                notification_id = str(notification_id)

        # 1. HTTP 202 Accepted (Placed into cloud queue for processing)
        if status_code == 202:
            return DispatchResult(
                status=NotificationEventStatus.ACCEPTED,
                external_http_status=status_code,
                notification_id=notification_id,
                message="Accepted for processing by cloud notification service.",
            )

        # 2. HTTP 400 Bad Request (Validation or payload rejection)
        elif status_code == 400:
            err_msg = "Upstream validation rejected notification payload."
            if isinstance(response_data, dict) and response_data.get("message"):
                err_msg = str(response_data.get("message"))
            elif response.text:
                err_msg = response.text[:200]

            return DispatchResult(
                status=NotificationEventStatus.REJECTED,
                external_http_status=status_code,
                notification_id=notification_id,
                message=f"Rejected: {err_msg}",
                error_message=err_msg,
            )

        # 3. HTTP 5xx (Service-side cloud error)
        elif 500 <= status_code <= 599:
            err_msg = f"External cloud notification service error (HTTP {status_code})."
            if isinstance(response_data, dict) and response_data.get("message"):
                err_msg = f"{err_msg}: {response_data.get('message')}"
            logger.error("AWS Gateway returned 5xx: %s for recipient %s", status_code, recipient)
            return DispatchResult(
                status=NotificationEventStatus.FAILED,
                external_http_status=status_code,
                notification_id=notification_id,
                message=err_msg,
                error_message=err_msg,
            )

        # 4. Other unexpected HTTP codes
        else:
            err_msg = f"Unexpected response from upstream notification gateway (HTTP {status_code})."
            logger.warning("AWS Gateway returned unexpected code: %s", status_code)
            return DispatchResult(
                status=NotificationEventStatus.FAILED,
                external_http_status=status_code,
                notification_id=notification_id,
                message=err_msg,
                error_message=err_msg,
            )

    except httpx.TimeoutException as exc:
        err_msg = (
            f"Request timed out after {settings.REQUEST_TIMEOUT_SECONDS}s. "
            "The notification may or may not have reached the cloud queue. "
            "To prevent duplicate emails, it has not been automatically re-sent."
        )
        logger.warning("Timeout when dispatching to %s: %s", recipient, exc)
        return DispatchResult(
            status=NotificationEventStatus.UNCERTAIN,
            external_http_status=None,
            notification_id=None,
            message="Outcome uncertain due to network timeout.",
            error_message=err_msg,
        )

    except (httpx.ConnectError, httpx.NetworkError) as exc:
        err_msg = f"Network connection failed: Unable to connect to upstream gateway ({str(exc)[:150]})."
        logger.error("Connection error when dispatching to %s: %s", recipient, exc)
        return DispatchResult(
            status=NotificationEventStatus.FAILED,
            external_http_status=None,
            notification_id=None,
            message="Connection to cloud gateway failed.",
            error_message=err_msg,
        )

    except Exception as exc:
        err_msg = f"Unexpected dispatch error: {str(exc)[:150]}"
        logger.exception("Unexpected error when dispatching to %s", recipient)
        return DispatchResult(
            status=NotificationEventStatus.FAILED,
            external_http_status=None,
            notification_id=None,
            message="Internal communication error.",
            error_message=err_msg,
        )

    finally:
        if should_close_client:
            await client.aclose()
