from typing import Dict, Any
from dramatic_logger import DramaticLogger
from linebot.v3.webhooks import (
    MessageEvent, 
    TextMessageContent,
    ImageMessageContent,
    VideoMessageContent,
    AudioMessageContent,
    LocationMessageContent,
    StickerMessageContent,
    FileMessageContent
)
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from fastapi import HTTPException
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.schema.runnable.passthrough import RunnableAssign
from datetime import datetime
from .models import (
    ProviderMessage, 
    TextContent,
    ImageContent,
    VideoContent,
    AudioContent,
    LocationContent,
    StickerContent,
    FileContent
)

from Utils.Runnables.RPrint import RPrint
import httpx
import os

def parse_line_message(message_event: MessageEvent) -> ProviderMessage:
    """Convert LINE message to standardized format"""
    base_content = {
        "raw_content": message_event.message.dict()
    }
    
    # Parse different message types
    if isinstance(message_event.message, TextMessageContent):
        content = TextContent(
            **base_content,
            text=message_event.message.text
        )
    elif isinstance(message_event.message, ImageContent):
        content = ImageContent(
            **base_content,
            content_provider=message_event.message.content_provider.dict(),
            url=None  # LINE doesn't provide direct URLs
        )
    elif isinstance(message_event.message, VideoMessageContent):
        content = VideoContent(
            **base_content,
            content_provider=message_event.message.content_provider.dict(),
            duration=message_event.message.duration,
            url=None
        )
    elif isinstance(message_event.message, AudioMessageContent):
        content = AudioContent(
            **base_content,
            content_provider=message_event.message.content_provider.dict(),
            duration=message_event.message.duration,
            url=None
        )
    elif isinstance(message_event.message, LocationMessageContent):
        content = LocationContent(
            **base_content,
            title=message_event.message.title,
            address=message_event.message.address,
            latitude=message_event.message.latitude,
            longitude=message_event.message.longitude
        )
    elif isinstance(message_event.message, StickerMessageContent):
        content = StickerContent(
            **base_content,
            package_id=message_event.message.package_id,
            sticker_id=message_event.message.sticker_id,
            keywords=message_event.message.keywords
        )
    elif isinstance(message_event.message, FileMessageContent):
        content = FileContent(
            **base_content,
            filename=message_event.message.file_name,
            file_size=message_event.message.file_size
        )
    else:
        raise ValueError(f"Unsupported message type: {type(message_event.message)}")

    # Create standardized message
    return ProviderMessage(
        provider="line",
        message_id=message_event.message.id,
        user_id=message_event.source.user_id,
        reply_token=message_event.reply_token,
        timestamp=datetime.fromtimestamp(message_event.timestamp / 1000),
        content=content,
        thread_id=None,  # LINE doesn't have thread IDs
        metadata={
            "source_type": message_event.source.type,
            "mode": message_event.mode
        }
    )

class SendMessageTextV2:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api

    def __call__(self, provider_message: ProviderMessage) -> ProviderMessage:
        """Send message back to LINE using V2 API"""
        try:
            # Extract the text from the standardized message
            if isinstance(provider_message.content, TextContent):
                text = provider_message.content.text
            else:
                text = f"Received {provider_message.content.type} message"

            self.line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=provider_message.reply_token,
                    messages=[TextMessage(text=f"Echo: {text}")]
                )
            )
            return provider_message
        except Exception as e:
            DramaticLogger["Dramatic"]["error"](f"Error sending LINE message:", str(e))
            raise HTTPException(status_code=500, detail=f"Error sending LINE message: {str(e)}")

async def send_to_orchestrator(provider_message: ProviderMessage) -> ProviderMessage:
    """Send message to orchestrator and get response"""
    try:
        # Convert to dict and ensure datetime is serialized
        message_dict = provider_message.dict()
        # Convert datetime to ISO format string
        message_dict["timestamp"] = provider_message.timestamp.isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:40443/process",  # Orchestrator endpoint
                json=message_dict,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Parse response back into ProviderMessage
            response_data = response.json()
            # Convert ISO string back to datetime
            response_data["timestamp"] = datetime.fromisoformat(response_data["timestamp"])
            return ProviderMessage.parse_obj(response_data)
            
    except Exception as e:
        DramaticLogger["Dramatic"]["error"](f"Error communicating with orchestrator:", str(e))
        # For now, just echo back the original message if orchestrator fails
        return provider_message

def create_receive_chain(line_bot_api):
    """Chain for receiving messages from LINE and sending to orchestrator"""
    return (
        # Parse LINE message to standard format
        RunnableLambda(parse_line_message)
        | RPrint(preface="Parsed LINE message:")
        # Send to orchestrator
        | RunnableLambda(send_to_orchestrator)
    )

def create_send_chain(line_bot_api):
    """Chain for receiving orchestrator response and sending to LINE"""
    return (
        RPrint(preface="Orchestrator response:")
        # Send response back to LINE using V2 API
        | RunnableLambda(SendMessageTextV2(line_bot_api))
    )

async def route_line_message(message_event: MessageEvent, line_bot_api) -> Dict[str, Any]:
    """Route incoming LINE message to orchestrator"""
    try:
        # Parse LINE message to standard format
        provider_message = parse_line_message(message_event)
        DramaticLogger["Normal"]["info"](f"Parsed LINE message from user {message_event.source.user_id}")
        
        # Convert to dict and ensure datetime is serialized
        message_dict = provider_message.dict(exclude_none=True)
        message_dict["timestamp"] = provider_message.timestamp.isoformat()
        
        # Send to orchestrator with longer timeout
        async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout
            try:
                response = await client.post(
                    "http://127.0.0.1:40443/process",
                    json=message_dict
                )
                response.raise_for_status()
                
                return {"status": "success", "message": "Message routed to orchestrator"}
                
            except httpx.TimeoutException:
                DramaticLogger["Normal"]["info"]("Orchestrator processing message (timeout is expected)")
                return {"status": "success", "message": "Message sent to orchestrator for processing"}
            
    except Exception as e:
        DramaticLogger["Dramatic"]["error"](f"Error routing message:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def send_line_message(provider_message: ProviderMessage) -> Dict[str, Any]:
    """Send message from orchestrator to LINE user"""
    try:
        line_bot_api = MessagingApi(ApiClient(Configuration(
            access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        )))
        
        # Extract text from standardized message
        if isinstance(provider_message.content, TextContent):
            text = provider_message.content.text
        else:
            text = f"Received {provider_message.content.type} message"

        # Send to LINE
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=provider_message.reply_token,
                messages=[TextMessage(text=text)]
            )
        )
        return {"status": "success", "message": "Message sent to LINE"}
        
    except Exception as e:
        DramaticLogger["Dramatic"]["error"](f"Error sending LINE message:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
