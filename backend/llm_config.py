"""
LLM Configuration Management for Admin Interface
Supports multiple LLM vendors through LangChain integration
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = "/data/llm_config.json"

# Supported LLM vendors and their default configurations
SUPPORTED_VENDORS = {
    "openai": {
        "name": "OpenAI",
        "description": "OpenAI GPT models",
        "requires_api_key": True,
        "default_base_url": "https://api.openai.com/v1",
        "default_models": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "langchain_class": "ChatOpenAI"
    },

    "meta": {
        "name": "Meta (via Ollama)",
        "description": "Meta Llama models via Ollama",
        "requires_api_key": False,
        "default_base_url": "http://host.docker.internal:11434",
        "default_models": [
            "llama3.1:70b",
            "llama3.1:8b",
            "llama3.2:3b",
            "llama3.2:1b"
        ],
        "langchain_class": "ChatOllama"
    },
    "ollama": {
        "name": "Ollama",
        "description": "Local Ollama models",
        "requires_api_key": False,
        "default_base_url": "http://host.docker.internal:11434",
        "default_models": [
            "gemma3:27b",
            "deepseek-r1:14b",
            "qwen2.5:14b",
            "mistral:7b",
            "codellama:13b"
        ],
        "langchain_class": "ChatOllama"
    },
    "lmstudio": {
        "name": "LM Studio",
        "description": "LM Studio local models",
        "requires_api_key": False,
        "default_base_url": "http://host.docker.internal:1234/v1",
        "default_models": [
            "deepseek-r1-0528-qwen3-8b-mlx",
            "llama-3.1-8b-instruct",
            "mistral-7b-instruct",
            "qwen2.5-7b-instruct"
        ],
        "langchain_class": "ChatOpenAI"  # LM Studio uses OpenAI-compatible API
    }
}

def get_default_config():
    """Get default LLM configuration."""
    return {
        "vendor": "openai",
        "api_key": None,
        "base_url": SUPPORTED_VENDORS["openai"]["default_base_url"],
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 2000,
        "timeout": 300
    }

def load_llm_config() -> Dict[str, Any]:
    """Load LLM configuration from file."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all required fields exist
                default_config = get_default_config()
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            return get_default_config()
    except Exception as e:
        logger.error(f"Error loading LLM config: {e}")
        return get_default_config()

def save_llm_config(config: Dict[str, Any]) -> bool:
    """Save LLM configuration to file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"LLM configuration saved: {config}")
        return True
    except Exception as e:
        logger.error(f"Error saving LLM config: {e}")
        return False

def get_vendor_models(vendor: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> List[str]:
    """Get available models for a vendor."""
    if vendor not in SUPPORTED_VENDORS:
        return []
    
    vendor_config = SUPPORTED_VENDORS[vendor]
    
    # For Ollama and LM Studio, try to fetch models dynamically
    if vendor in ["ollama", "meta"]:
        return get_ollama_models(base_url or vendor_config["default_base_url"])
    elif vendor == "lmstudio":
        return get_lmstudio_models(base_url or vendor_config["default_base_url"])
    else:
        # For cloud providers, return default models
        return vendor_config["default_models"]

def get_ollama_models(base_url: str) -> List[str]:
    """Get available models from Ollama."""
    try:
        import requests
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model.get("name", "") for model in models if model.get("name")]
        else:
            logger.warning(f"Could not fetch Ollama models: {response.status_code}")
            return SUPPORTED_VENDORS["ollama"]["default_models"]
    except Exception as e:
        logger.warning(f"Error fetching Ollama models: {e}")
        return SUPPORTED_VENDORS["ollama"]["default_models"]

def get_lmstudio_models(base_url: str) -> List[str]:
    """Get available models from LM Studio."""
    try:
        import requests
        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code == 200:
            models_data = response.json()
            if "data" in models_data:
                return [model.get("id", "") for model in models_data["data"] if model.get("id")]
            else:
                return SUPPORTED_VENDORS["lmstudio"]["default_models"]
        else:
            logger.warning(f"Could not fetch LM Studio models: {response.status_code}")
            return SUPPORTED_VENDORS["lmstudio"]["default_models"]
    except Exception as e:
        logger.warning(f"Error fetching LM Studio models: {e}")
        return SUPPORTED_VENDORS["lmstudio"]["default_models"]

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate LLM configuration."""
    result = {"valid": True, "errors": []}
    
    # Check vendor
    if config.get("vendor") not in SUPPORTED_VENDORS:
        result["valid"] = False
        result["errors"].append(f"Unsupported vendor: {config.get('vendor')}")
    
    # Check API key for vendors that require it
    vendor = config.get("vendor")
    if vendor in SUPPORTED_VENDORS:
        vendor_config = SUPPORTED_VENDORS[vendor]
        if vendor_config["requires_api_key"] and not config.get("api_key"):
            result["valid"] = False
            result["errors"].append(f"API key required for {vendor_config['name']}")
    
    # Check model
    if not config.get("model"):
        result["valid"] = False
        result["errors"].append("Model is required")
    
    return result

def test_llm_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test LLM connection with given configuration."""
    try:
        vendor = config.get("vendor")
        if vendor not in SUPPORTED_VENDORS:
            return {"success": False, "error": f"Unsupported vendor: {vendor}"}
        
        vendor_config = SUPPORTED_VENDORS[vendor]
        
        # Test based on vendor type
        if vendor == "openai":
            return test_openai_connection(config)
        elif vendor in ["ollama", "meta"]:
            return test_ollama_connection(config)
        elif vendor == "lmstudio":
            return test_lmstudio_connection(config)
        else:
            return {"success": False, "error": f"Testing not implemented for {vendor}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_openai_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test OpenAI connection."""
    try:
        from langchain_openai import ChatOpenAI
        
        chat = ChatOpenAI(
            model=config.get("model", "gpt-3.5-turbo"),
            openai_api_key=config.get("api_key"),
            openai_api_base=config.get("base_url"),
            max_tokens=10,
            temperature=0.1,
            request_timeout=10
        )
        
        # Test with a simple message
        from langchain_core.messages import HumanMessage
        response = chat.invoke([HumanMessage(content="Hello")])
        
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "error": str(e)}



def test_ollama_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test Ollama connection."""
    try:
        import requests
        base_url = config.get("base_url", "http://host.docker.internal:11434")
        
        # Test if Ollama is running
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code != 200:
            return {"success": False, "error": "Ollama server not accessible"}
        
        # Check if model exists
        models = response.json().get("models", [])
        model_names = [model.get("name") for model in models]
        if config.get("model") not in model_names:
            return {"success": False, "error": f"Model {config.get('model')} not found in Ollama"}
        
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_lmstudio_connection(config: Dict[str, Any]) -> Dict[str, Any]:
    """Test LM Studio connection."""
    try:
        import requests
        base_url = config.get("base_url", "http://host.docker.internal:1234/v1")
        
        # Test if LM Studio is running
        response = requests.get(f"{base_url}/models", timeout=5)
        if response.status_code != 200:
            return {"success": False, "error": "LM Studio server not accessible"}
        
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "error": str(e)}
