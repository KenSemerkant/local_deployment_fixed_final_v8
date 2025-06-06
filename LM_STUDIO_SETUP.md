# LM Studio Configuration Guide

This guide explains how to configure the AI Financial Analyst application to use LM Studio with the DeepSeek R1 model instead of Ollama.

## What is LM Studio?

LM Studio is a desktop application that allows you to run large language models locally on your machine. It provides an OpenAI-compatible API, making it easy to integrate with applications that support OpenAI's API format.

## DeepSeek R1 Model

The `deepseek-r1-0528-qwen3-8b-mlx` model is a high-performance reasoning model that's excellent for financial analysis tasks. It provides strong analytical capabilities while being efficient enough to run locally.

## Prerequisites

1. **Download and Install LM Studio**
   - Visit [https://lmstudio.ai/](https://lmstudio.ai/)
   - Download LM Studio for your operating system
   - Install and launch the application

2. **Download the DeepSeek Model**
   - In LM Studio, go to the "Discover" tab
   - Search for `deepseek-r1-0528-qwen3-8b-mlx`
   - Click "Download" and wait for the model to download completely
   - Note: This model is approximately 8GB, so ensure you have sufficient disk space

3. **Start the Local Server**
   - In LM Studio, go to the "Local Server" tab
   - Select your downloaded model
   - Click "Start Server"
   - Note the server URL (usually `http://localhost:1234/v1`)

## Configuration Methods

### Method 1: Environment Variables (Recommended)

Update your `docker-compose.yml` file or set environment variables:

```yaml
version: '3.8'
services:
  backend:
    # ... other configuration
    environment:
      - LLM_MODE=openai
      - OPENAI_BASE_URL=http://host.docker.internal:1234/v1
      - OPENAI_API_KEY=lm-studio  # Can be anything for LM Studio
      - OPENAI_MODEL=deepseek-r1-0528-qwen3-8b-mlx  # Use the exact model name from LM Studio
```

For Docker on Linux, use `http://172.17.0.1:1234/v1` instead of `host.docker.internal`.

### Method 2: Runtime Configuration via API

You can also configure LM Studio at runtime using the application's API:

```bash
# Get current LLM status
curl -X GET "http://localhost:8000/llm/status" \
  -H "Authorization: Bearer your-token"

# Set LM Studio configuration
curl -X POST "http://localhost:8000/llm/mode" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "mode": "openai",
    "base_url": "http://host.docker.internal:1234/v1",
    "api_key": "lm-studio",
    "model": "deepseek-r1-0528-qwen3-8b-mlx"
  }'
```

### Method 3: Frontend Configuration (If Available)

If the frontend has an LLM configuration interface:

1. Log into the application
2. Navigate to Settings or LLM Configuration
3. Select "OpenAI" mode
4. Set Base URL to: `http://localhost:1234/v1`
5. Set API Key to: `lm-studio` (or leave empty)
6. Set Model to: `deepseek-r1-0528-qwen3-8b-mlx`
7. Save configuration

## Finding Your Model Name

To find the exact model name that LM Studio is using:

1. In LM Studio, go to the "Local Server" tab
2. Look at the model dropdown - the exact name shown there is what you need
3. Alternatively, you can query the LM Studio API:

```bash
curl http://localhost:1234/v1/models
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure LM Studio server is running
   - Check that the port (1234) is correct
   - For Docker: Use `host.docker.internal` on Mac/Windows, `172.17.0.1` on Linux

2. **Model Not Found**
   - Verify the model name exactly matches what's shown in LM Studio
   - Ensure the model is loaded in LM Studio's Local Server tab

3. **Slow Responses**
   - LM Studio performance depends on your hardware
   - Consider using a smaller model for faster responses
   - Ensure sufficient RAM and CPU resources

### Testing the Configuration

1. **Test LM Studio directly:**
```bash
curl -X POST "http://localhost:1234/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-0528-qwen3-8b-mlx",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

2. **Test through the application:**
   - Upload a document
   - Check if processing completes successfully
   - Try asking questions about the document

## Performance Considerations

- **Hardware Requirements:** LM Studio requires significant RAM and CPU
- **Model Size:** Larger models provide better results but are slower
- **Concurrent Requests:** LM Studio typically handles one request at a time
- **Timeout Settings:** The application uses a 5-minute timeout for LLM requests

## Switching Back to Ollama

To switch back to Ollama, either:

1. Set environment variables:
```yaml
environment:
  - LLM_MODE=ollama
  - OLLAMA_MODEL=gemma3:27b
```

2. Or use the API:
```bash
curl -X POST "http://localhost:8000/llm/mode" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"mode": "ollama", "model": "gemma3:27b"}'
```

## Security Notes

- LM Studio runs locally, so your data doesn't leave your machine
- The API key for LM Studio can be any string (it's not validated)
- Ensure LM Studio is only accessible from localhost for security
