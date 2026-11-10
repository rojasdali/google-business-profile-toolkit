"""Google Business Profile Toolkit — Agnostic SDK for local posts, hours, reviews, and insights."""

from typing import Optional

from gbp_toolkit.client import GBPClient, GBPClientError, GBPQuotaExceededError
from gbp_toolkit.hours import HoursService
from gbp_toolkit.locations import LocationService, LocationsService
from gbp_toolkit.performance import PerformanceService
from gbp_toolkit.posts import PostsService
from gbp_toolkit.reviews import ReviewsService
from gbp_toolkit.types import (
    CallToAction,
    LocalPostPayload,
    LocalPostResult,
    LocationDetails,
    PostActionType,
    PostTopicType,
    ReviewItem,
    SpecialHoursDay,
)

__version__ = "0.2.0"


class GBPToolkit:
    """Unified façade for Google Business Profile automation and management."""

    def __init__(self, client: GBPClient):
        self.client = client
        self.posts = PostsService(client)
        self.hours = HoursService(client)
        self.locations = LocationsService(client)
        self.reviews = ReviewsService(client)
        self.performance = PerformanceService(client)

    @classmethod
    def from_env(cls, env_path: Optional[str] = None, dry_run: bool = False) -> "GBPToolkit":
        """Instantiate complete toolkit from environment credentials."""
        client = GBPClient.from_env(env_path=env_path, dry_run=dry_run)
        return cls(client)


__all__ = [
    "__version__",
    "GBPToolkit",
    "GBPClient",
    "GBPClientError",
    "GBPQuotaExceededError",
    "PostsService",
    "HoursService",
    "LocationService",
    "LocationsService",
    "ReviewsService",
    "PerformanceService",
    "CallToAction",
    "LocalPostPayload",
    "LocalPostResult",
    "LocationDetails",
    "PostActionType",
    "PostTopicType",
    "ReviewItem",
    "SpecialHoursDay",
]
