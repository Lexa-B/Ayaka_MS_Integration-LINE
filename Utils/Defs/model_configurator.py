from typing import List, Union, Dict, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from langchain_openai import ChatOpenAI  # Add OpenAI import
import hjson
import json
import re
# Add ChatAyaka import
from Utils.Classes.ChatAyaka import ChatAyaka
from dotenv import load_dotenv  # Add this import
import os  # Add this if not already imported

# Load environment variables from .env file
load_dotenv()

def _load_jsonc(file_path: str) -> dict:
    """
    Load a JSONC file and return a Python dictionary.
    Uses hjson library which is more robust with comments and special characters.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # hjson handles comments, trailing commas, and multi-byte characters well
            return hjson.load(f)
    except Exception as e:
        raise ValueError(f"Error parsing JSONC file {file_path}: {str(e)}")

def apply_model_configs(
    models: List[Union[ChatNVIDIA, NVIDIAEmbeddings, ChatAyaka, ChatOpenAI]], 
    config_file: str = "./Configs/TC3.ModelConfig.jsonc"
) -> List[Union[ChatNVIDIA, NVIDIAEmbeddings, ChatAyaka, ChatOpenAI]]:
    """
    Apply configurations from a JSONC file to a list of models.
    Only applies parameters that are supported by the model.
    """
    
    # Read and parse the config file
    config = _load_jsonc(config_file)

    # Configure each model
    configured_models = []
    
    for model in models:
        # Determine model type and name from the instance
        if isinstance(model, (ChatNVIDIA, ChatAyaka, ChatOpenAI)):
            model_type = "llm"
            # Get model name based on model type
            if isinstance(model, ChatOpenAI):
                model_attr = model.model_name
            else:
                model_attr = model.model

            # Determine if it's chat, instruct, reasoning, or deep_context
            if model_attr == config["LLM_Models"]["llm_chat_model"]:
                model_name = "chat"
            elif model_attr == config["LLM_Models"]["llm_instruct_model"]:
                model_name = "instruct"
            elif model_attr == config["LLM_Models"].get("llm_reasoning_model"):
                model_name = "reasoning"
            elif model_attr == config["LLM_Models"].get("llm_deep_context_model"):
                model_name = "deep_context"
            else:
                raise ValueError(f"Unknown LLM model: {model_attr}")
                
            # Apply LLM configurations
            model_config = config["LLM_Generation_Hyperparameters"]
            prefix = f"llm_{model_name}_"
            
            # Only set parameters that are supported by the model
            supported_params = {
                'temperature': 'temperature',
                'top_p': 'top_p',
                'max_tokens': 'max_tokens',
                'stop_sequences': 'stop'  # Note: API uses 'stop' instead of 'stop_sequences'
            }
            
            for config_name, model_name in supported_params.items():
                config_value = model_config.get(f"{prefix}{config_name}")
                if config_value is not None:
                    setattr(model, model_name, config_value)
                
        elif isinstance(model, NVIDIAEmbeddings):
            # Determine if it's Japanese or English embedder
            if model.model == config["Embedder_Models"]["embedder_model_jp"]:
                model_name = "jp"
            elif model.model == config["Embedder_Models"]["embedder_model_eng"]:
                model_name = "eng"
            else:
                raise ValueError(f"Unknown Embeddings model: {model.model}")
                
            # Currently no additional configurations for embedders
            pass
            
        else:
            raise ValueError(f"Unsupported model type: {type(model)}")
            
        configured_models.append(model)
        
    return configured_models

def get_configured_model(
    model_type: str,
    config_file: str = "./Configs/Default.ModelConfig.jsonc"
) -> Union[ChatNVIDIA, NVIDIAEmbeddings, ChatAyaka, ChatOpenAI]:
    """
    Create and configure a new model instance.
    
    Args:
        model_type: Type of model to create ("chat", "instruct", "reasoning", "deep_context", "embedder_jp", "embedder_eng")
        config_file: Path to the configuration file
    
    Returns:
        Configured model instance
    """
    
    # Read config file
    config = _load_jsonc(config_file)
    
    # Create and configure model based on type
    if model_type in ["chat", "instruct", "reasoning", "deep_context"]:
        model_function = config["Model_Functions"][f"llm_{model_type}"]
        model_name = config["LLM_Models"][f"llm_{model_type}_model"]
        
        if model_function == "ChatAyaka":
            model = ChatAyaka(
                nvidia_api_url=config["NetLocations"][f"llm_{model_type}_base_url"],
                model=model_name
            )
        elif model_function == "ChatOpenAI":
            # For OpenAI, we use api_key from environment variable OPENAI_API_KEY
            model = ChatOpenAI(
                model=model_name,
                api_key=config.get("API_Keys", {}).get("openai_api_key")  # Optional from config
            )
        else:  # Default to ChatNVIDIA
            model = ChatNVIDIA(
                base_url=config["NetLocations"][f"llm_{model_type}_base_url"],
                model=model_name
            )
        # Apply configuration using the main function
        return apply_model_configs([model], config_file)[0]
        
    elif model_type in ["embedder_jp", "embedder_eng"]:
        lang = model_type.split('_')[1]
        model = NVIDIAEmbeddings(
            base_url=config["NetLocations"][f"embedder_base_url_{lang}"],
            model=config["Embedder_Models"][f"embedder_model_{lang}"],
            truncate="NONE"
        )
        return apply_model_configs([model], config_file)[0]
        
    else:
        raise ValueError(f"Unknown model type: {model_type}") 