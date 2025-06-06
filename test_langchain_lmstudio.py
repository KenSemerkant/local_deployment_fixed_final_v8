#!/usr/bin/env python3
"""
Test script to verify LangChain integration with LM Studio
"""

import os
import sys

def test_langchain_lmstudio():
    """Test LangChain integration with LM Studio."""
    try:
        print("Testing LangChain integration with LM Studio...")
        
        # Import LangChain components
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # Configuration
        base_url = "http://localhost:1234/v1"
        api_key = "lm-studio"
        model = "deepseek-r1-0528-qwen3-8b-mlx"
        
        print(f"Base URL: {base_url}")
        print(f"Model: {model}")
        
        # Create ChatOpenAI instance
        chat = ChatOpenAI(
            model=model,
            openai_api_base=base_url,
            openai_api_key=api_key,
            max_tokens=100,
            temperature=0.3,
            request_timeout=60
        )
        
        print("ChatOpenAI instance created successfully")
        
        # Create test messages
        messages = [
            SystemMessage(content="You are a helpful financial analyst assistant."),
            HumanMessage(content="What is the purpose of a financial statement?")
        ]
        
        print("Sending test message to LM Studio...")
        
        # Make the API call
        response = chat(messages)
        
        print("✅ SUCCESS! LangChain successfully connected to LM Studio")
        print(f"Response: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_langchain_lmstudio()
    sys.exit(0 if success else 1)
