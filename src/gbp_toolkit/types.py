"""Domain data types and Pydantic schemas for Google Business Profile."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class PostTopicType(str, Enum):
    STANDARD = "STANDARD"
    OFFER = "OFFER"
    EVENT = "EVENT"


class PostActionType(str, Enum):
    LEARN_MORE = "LEARN_MORE"
    CALL = "CALL"
    BOOK = "BOOK"
    SIGN_UP = "SIGN_UP"
    ORDER = "ORDER"


@dataclass
class CallToAction:
    action_type: PostActionType
    url: str


@dataclass
class LocalPostPayload:
    summary: str
    language_code: str = "es"
    topic_type: PostTopicType = PostTopicType.STANDARD
    call_to_action: Optional[CallToAction] = None
    media_url: Optional[str] = None
    coupon_code: Optional[str] = None
    redeem_url: Optional[str] = None
    terms: Optional[str] = None


@dataclass
class LocalPostResult:
    post_id: str
    name: str
    state: str
    create_time: str
    summary: str
    search_url: Optional[str] = None


@dataclass
class TimeRange:
    open_time: str  # "08:00"
    close_time: str  # "21:00"


@dataclass
class SpecialHoursDay:
    date_val: date
    is_closed: bool = False
    open_time: Optional[str] = None
    close_time: Optional[str] = None


@dataclass
class LocationDetails:
    location_id: str
    title: str
    phone: str
    address_lines: List[str]
    locality: str
    administrative_area: str
    postal_code: str
    website_url: Optional[str] = None


@dataclass
class ReviewItem:
    review_id: str
    reviewer_name: str
    star_rating: int
    comment: Optional[str] = None
    create_time: Optional[datetime] = None
    reply_comment: Optional[str] = None
    reply_update_time: Optional[datetime] = None


@dataclass
class PostHistoryEntry:
    post_hash: str
    topic_slug: str
    summary_preview: str
    published_date: str
    cta_url: str
