"""Compatibility module for the canonical access-management router.

Team membership endpoints are owned by ``backend.api.access_management``.
Keeping this module avoids breaking imports while preventing duplicate routes.
"""

from backend.api.access_management import router


__all__ = ["router"]
