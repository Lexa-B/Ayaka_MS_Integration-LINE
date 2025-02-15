from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

class MessageContent(BaseModel):
    """Base content that all message types must provide"""
    type: str
    raw_content: Dict[str, Any] = Field(description="Original provider-specific content")

class TextContent(MessageContent):
    type: str = "text"
    text: str

class ImageContent(MessageContent):
    type: str = "image"
    url: Optional[str] = None
    content_provider: Dict[str, Any]
    preview_url: Optional[str] = None

class VideoContent(MessageContent):
    type: str = "video"
    url: Optional[str] = None
    content_provider: Dict[str, Any]
    duration: Optional[int] = None
    preview_url: Optional[str] = None

class AudioContent(MessageContent):
    type: str = "audio"
    url: Optional[str] = None
    content_provider: Dict[str, Any]
    duration: int

class LocationContent(MessageContent):
    type: str = "location"
    title: Optional[str] = None
    address: Optional[str] = None
    latitude: float
    longitude: float

class StickerContent(MessageContent):
    type: str = "sticker"
    package_id: str
    sticker_id: str
    keywords: Optional[List[str]] = None

class FileContent(MessageContent):
    type: str = "file"
    filename: str
    file_size: int
    file_type: Optional[str] = None

class ProviderMessage(BaseModel):
    """Standardized message format for all providers"""
    provider: str = Field(description="Message provider (e.g., 'line', 'discord')")
    message_id: str = Field(description="Provider's message ID")
    user_id: str = Field(description="User ID in provider's system")
    reply_token: Optional[str] = None
    timestamp: datetime
    content: Union[
        TextContent,
        ImageContent,
        VideoContent,
        AudioContent,
        LocationContent,
        StickerContent,
        FileContent
    ]
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    mentions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None 