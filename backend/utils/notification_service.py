"""
Basic Notification Service for Proposal Drafter

This service provides a simple interface for sending notifications to users.
Currently implements logging-based notifications that can be extended to
email, Slack, or other notification channels.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending user notifications."""

    @staticmethod
    def send_role_request_approval_notification(
        user_id: str, user_name: str, user_email: str, role_name: str, admin_note: str = None, approved_by: str = None
    ) -> Dict[str, Any]:
        """
        Send notification when a role request is approved.

        Args:
            user_id: ID of the user who requested the role
            user_name: Name of the user
            user_email: Email of the user
            role_name: Name of the approved role
            admin_note: Optional note from the admin
            approved_by: ID of the admin who approved the request

        Returns:
            Notification record
        """
        notification = {
            "notification_type": "role_request_approved",
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email,
            "role_name": role_name,
            "admin_note": admin_note,
            "approved_by": approved_by,
            "timestamp": datetime.utcnow().isoformat(),
            "delivered": False,
            "delivery_methods": [],
        }

        # Log the notification (basic implementation)
        logger.info(
            f"Role request approved notification for {user_name} ({user_email})",
            extra={
                "notification_type": "role_request_approved",
                "user_id": user_id,
                "user_email": user_email,
                "role_name": role_name,
                "admin_note": admin_note,
                "approved_by": approved_by,
            },
        )

        # TODO: Extend this to send actual email notifications
        # Example email implementation would go here:
        # if user_email:
        #     send_email(
        #         to=user_email,
        #         subject=f"Your role request for {role_name} has been approved",
        #         template="role_request_approved",
        #         context={
        #             "user_name": user_name,
        #             "role_name": role_name,
        #             "admin_note": admin_note,
        #             "approved_by": approved_by
        #         }
        #     )
        #     notification["delivery_methods"].append("email")
        #     notification["delivered"] = True

        return notification

    @staticmethod
    def send_role_request_rejection_notification(
        user_id: str, user_name: str, user_email: str, role_name: str, admin_note: str = None, rejected_by: str = None
    ) -> Dict[str, Any]:
        """
        Send notification when a role request is rejected.

        Args:
            user_id: ID of the user who requested the role
            user_name: Name of the user
            user_email: Email of the user
            role_name: Name of the rejected role
            admin_note: Optional note from the admin
            rejected_by: ID of the admin who rejected the request

        Returns:
            Notification record
        """
        notification = {
            "notification_type": "role_request_rejected",
            "user_id": user_id,
            "user_name": user_name,
            "user_email": user_email,
            "role_name": role_name,
            "admin_note": admin_note,
            "rejected_by": rejected_by,
            "timestamp": datetime.utcnow().isoformat(),
            "delivered": False,
            "delivery_methods": [],
        }

        # Log the notification (basic implementation)
        logger.info(
            f"Role request rejected notification for {user_name} ({user_email})",
            extra={
                "notification_type": "role_request_rejected",
                "user_id": user_id,
                "user_email": user_email,
                "role_name": role_name,
                "admin_note": admin_note,
                "rejected_by": rejected_by,
            },
        )

        # TODO: Extend this to send actual email notifications
        # Example email implementation would go here:
        # if user_email:
        #     send_email(
        #         to=user_email,
        #         subject=f"Your role request for {role_name} has been rejected",
        #         template="role_request_rejected",
        #         context={
        #             "user_name": user_name,
        #             "role_name": role_name,
        #             "admin_note": admin_note,
        #             "rejected_by": rejected_by
        #         }
        #     )
        #     notification["delivery_methods"].append("email")
        #     notification["delivered"] = True

        return notification

    @staticmethod
    def log_notification_delivery(
        notification_type: str, user_id: str, delivery_method: str, success: bool, details: Dict[str, Any] = None
    ) -> None:
        """
        Log the delivery status of a notification.

        Args:
            notification_type: Type of notification
            user_id: ID of the user
            delivery_method: Method used (email, slack, etc.)
            success: Whether delivery was successful
            details: Additional details about the delivery
        """
        status = "success" if success else "failed"
        logger.info(
            f"Notification {status}: {notification_type} to user {user_id} via {delivery_method}",
            extra={
                "notification_type": notification_type,
                "user_id": user_id,
                "delivery_method": delivery_method,
                "status": status,
                "details": details or {},
            },
        )


# Singleton instance for easy import
notification_service = NotificationService()
