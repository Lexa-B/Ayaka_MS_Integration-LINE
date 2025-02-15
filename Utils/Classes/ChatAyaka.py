from langchain.chat_models.base import BaseChatModel
from langchain.prompts.chat import ChatPromptTemplate, BaseMessagePromptTemplate
from langchain.schema import HumanMessage, BaseMessage, AIMessage
from langchain.schema.messages import BaseMessage
from langchain.schema.output import ChatGeneration, ChatResult
from typing import Any, List, Optional, Dict
from pydantic import Field
import requests

################################################################################
## Custom Classes

class AyakaClient:
    """Simple client for local Ayaka API."""
    
    def __init__(self, api_url: str):
        # Remove trailing slashes and /v1 if present
        self.api_url = api_url.rstrip('/').rstrip('/v1')
        
    def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """Send a chat completion request to the local API."""
        payload = {
            "messages": messages,
            **kwargs
        }
        response = requests.post(
            f"{self.api_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()

class ChatAyaka(BaseChatModel):
    """Custom chat model that supports our Ayaka models."""
    
    model: str = Field(default="ayaka-llm-jp-chat-v0")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4000)
    top_p: float = Field(default=0.95)
    nvidia_api_url: str = Field(default="http://127.0.0.1:41443")
    stop: Optional[List[str]] = Field(default_factory=list)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize with custom settings."""
        super().__init__(**kwargs)
        self._client = AyakaClient(api_url=self.nvidia_api_url)

    def _generate(
        self, messages: List[BaseMessage], stop: Optional[List[str]] = None
    ) -> ChatResult:
        """Generate chat completion."""
        message_dicts = self._create_message_dicts(messages)
        response = self._client.chat_completion(
            messages=message_dicts,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            stop=stop if stop else []
        )
        return ChatResult(generations=[
            ChatGeneration(
                message=AIMessage(content=response["choices"][0]["message"]["content"]),
                generation_info=dict(finish_reason=response["choices"][0]["finish_reason"])
            )
        ])

    def _create_message_dicts(self, messages: List[Any]) -> List[Dict[str, Any]]:
        """Convert messages to the format expected by the API."""
        message_dicts = []
        for message in messages:
            message_dict = {
                "role": message.type,
                "content": message.content
            }
            # Move additional_kwargs contents into the main dict
            if hasattr(message, "additional_kwargs") and message.additional_kwargs:
                message_dict.update(message.additional_kwargs)
            message_dicts.append(message_dict)
        return message_dicts

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "ayaka_chat"

class AyakaMessagePromptTemplate(BaseMessagePromptTemplate):
    """Template for Ayaka LLM messages that can include response marker control."""
    
    prompt_template: str = Field(..., description="The template string to format")
    add_response_marker: bool = Field(default=True, description="Whether to add the response marker")
    template_variables: List[str] = Field(default_factory=list, description="Input variables for the template")

    @property
    def template(self) -> str:
        """Get the template string."""
        return self.prompt_template

    @property
    def input_variables(self) -> List[str]:
        """Get input variables."""
        return self.template_variables

    def format(self, **kwargs: Any) -> Dict:
        """Format the template into a message dictionary."""
        text = self.template.format(**kwargs)
        return {
            "role": "user",
            "content": text,
            "additional_kwargs": {"add_response_marker": self.add_response_marker}
        }

    def format_messages(self, **kwargs: Any) -> List[BaseMessage]:
        """Format the template into a list of messages."""
        message_dict = self.format(**kwargs)
        return [HumanMessage(**message_dict)]

class ChatAyakaPromptTemplate(ChatPromptTemplate):
    """Custom chat template for Ayaka LLMs."""
    
    @classmethod
    def llm_jp_template(
        cls,
        template: str,
        add_response_marker: bool = True,
        input_variables: Optional[List[str]] = None
    ) -> "ChatAyakaPromptTemplate":
        """Create a template specifically for LLM-JP models."""
        if input_variables is None:
            # Extract variables from the template
            input_variables = []
            for part in template.split("{"):
                if "}" in part:
                    var_name = part.split("}")[0].strip()
                    if var_name:
                        input_variables.append(var_name)
        
        message_prompt = AyakaMessagePromptTemplate(
            prompt_template=template,
            add_response_marker=add_response_marker,
            template_variables=input_variables
        )
        
        return cls.from_messages([message_prompt])