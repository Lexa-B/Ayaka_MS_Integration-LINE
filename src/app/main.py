from fastapi import FastAPI, Request, HTTPException
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,  # This is the correct one
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.exceptions import InvalidSignatureError
import uvicorn
import logging
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv
import json
import ssl
import socket
from dramatic_logger import DramaticLogger

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# LINE API setup
configuration = Configuration(
    access_token=os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
)
client = ApiClient(configuration)
line_bot_api = MessagingApi(client)  # Initialize with API client
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

app = FastAPI()


## ========================================------------========================================
## ---------------------------------------- MIDDLEWARE ---------------------------------------
## ========================================------------========================================

# Middleware to log all requests and responses
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        DramaticLogger["Normal"]["info"](f"[LLM-Host] Request: {request.method} {request.url}")
        if request.method == "POST":
            body = await request.body()
            try:
                body_str = body.decode('utf-8')
                # Parse the JSON string back into a Python object
                body_obj = json.loads(body_str)
                # Convert back to JSON with ensure_ascii=False to preserve unicode
                pretty_body = json.dumps(body_obj, ensure_ascii=False, indent=2)
                DramaticLogger["Dramatic"]["debug"]("[LLM-Host] Request Body:", pretty_body)
            except UnicodeDecodeError:
                DramaticLogger["Dramatic"]["warning"]("[LLM-Host] Could not decode request body.")
            except json.JSONDecodeError:
                DramaticLogger["Dramatic"]["warning"]("[LLM-Host] Could not parse request body as JSON.")
            
            # Reassign the body so downstream can read it
            async def receive():
                return {"type": "http.request", "body": body, "more_body": False}
            request = Request(scope=request.scope, receive=receive)
        
        if request.method == "GET": # Development debugging only; avoid logging in production. This can reveal sensitive information, particularly API keys.
            headers = dict(request.headers)
            DramaticLogger["Dramatic"]["debug"]("[LLM-Host] GET Request Headers:", headers)  # Development debugging only; avoid logging in production
        
        response = await call_next(request)
        DramaticLogger["Normal"]["info"](f"[LLM-Host] Response: {response.status_code}")
        return response

app.add_middleware(LoggingMiddleware)

## ========================================--------------========================================
## ---------------------------------------- LINE WEBHOOK ---------------------------------------
## ========================================--------------========================================

@app.post("/")
async def webhook(request: Request):
    # Log request details
    DramaticLogger["Normal"]["info"](f"Received webhook request from {request.client.host}")
    
    # Get LINE signature
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        logger.error("No X-Line-Signature header found")
        raise HTTPException(status_code=401, detail="No signature")
    
    # Get request body
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        # Verify signature
        handler.handle(body_str, signature)
        
        # Parse webhook body
        body_json = json.loads(body_str)
        events = body_json.get("events", [])
        
        for event in events:
            if event["type"] == "message":
                message_event = MessageEvent.from_dict(event)
                if isinstance(message_event.message, TextMessageContent):
                    # Echo back the received message
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=message_event.reply_token,
                            messages=[TextMessage(text=message_event.message.text)]
                        )
                    )
        
        return {"status": "OK"}
        
    except InvalidSignatureError:
        raise HTTPException(status_code=401, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def handle_text_message(event):
    # Log message details
    print(f"Message: {event.message}")
    print(f"From user: {event.source.user_id}")
    print(f"Reply token: {event.reply_token}")
    print(f"Timestamp: {event.timestamp}")

    try:
        # Reply using v3 API
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=event.message.text, type="text")]
            )
        )
    except Exception as e:
        logger.error(f"Error sending reply: {e}")
        raise

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 50005))
    uvicorn.run(app, host="0.0.0.0", port=port) 