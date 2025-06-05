# AI Financial Analyst - Ollama Integration Guide

This guide explains how to use the AI Financial Analyst system with Ollama and the Gemma 3 27B model for local deployment.

## Prerequisites

1. **Ollama Installation**: You must have Ollama installed on your host machine
   - Download from [ollama.ai](https://ollama.ai)
   - Verify installation with `ollama --version`

2. **Gemma 3 27B Model**: You must have the model pulled in Ollama
   - Pull the model with: `ollama pull gemma3:27b`
   - Verify with: `ollama list`

3. **Hardware Requirements**:
   - Recommended: Mac Studio Ultra with 96GB RAM or similar
   - Minimum: MacBook Pro M3-Max with 36GB RAM or similar
   - CPU-only mode is available but will be significantly slower

## Configuration Options

The system supports three LLM modes:

1. **Mock Mode** (default): Uses pre-defined responses for quick testing
2. **Ollama Mode**: Uses locally running Ollama with Gemma 3 27B
3. **OpenAI Mode**: Uses OpenAI API (requires API key)

## Setup Instructions

1. **Start Ollama**:
   ```bash
   # Start Ollama service in a terminal
   ollama serve
   ```

2. **Configure the System**:
   Edit the `docker-compose.yml` file to set your preferred LLM mode:
   ```yaml
   environment:
     - LLM_MODE=ollama  # Change from 'mock' to 'ollama'
     - OLLAMA_BASE_URL=http://host.docker.internal:11434
     - OLLAMA_MODEL=gemma3:27b
     - OLLAMA_USE_CPU=false  # Set to true for CPU-only mode
     - ENABLE_CACHING=true
   ```

3. **Start the Application**:
   ```bash
   docker-compose down -v  # If you had a previous version running
   docker-compose up --build -d
   ```

4. **Access the Application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - MinIO Console: http://localhost:9001 (login: minioadmin/minioadmin)

## Using the LLM Configuration API

The system provides API endpoints to configure the LLM at runtime:

1. **Get Current Configuration**:
   ```
   GET /llm/config
   ```

2. **Update Configuration**:
   ```
   POST /llm/config
   {
     "mode": "ollama",
     "ollama": {
       "model": "gemma3:27b",
       "use_cpu": false
     }
   }
   ```

3. **Test Ollama Connection**:
   ```
   GET /llm/ollama/test
   ```

4. **Clear Cache**:
   ```
   POST /llm/cache/clear
   ```

## Performance Considerations

1. **First-time Analysis**: The first document analysis will be slower as the model loads
2. **Caching**: Subsequent analyses of the same document will use cached results
3. **CPU Mode**: If you experience GPU memory issues, enable CPU mode
4. **Document Size**: Large documents (>50 pages) may require more processing time

## Troubleshooting

1. **Connection Issues**:
   - Ensure Ollama is running (`ollama serve`)
   - Verify the model is available (`ollama list`)
   - Check the Ollama URL in docker-compose.yml

2. **Memory Issues**:
   - Enable CPU mode if you're experiencing GPU memory errors
   - Reduce concurrent processing by uploading one document at a time

3. **Slow Performance**:
   - Check if caching is enabled
   - Verify that your hardware meets the minimum requirements
   - Consider using a smaller model if available

## Advanced Configuration

For advanced users, you can modify these files:
- `backend/llm_integration.py`: Core LLM integration logic
- `backend/app.py`: FastAPI backend service
- `docker-compose.yml`: Environment variables and service configuration

## System Prompt

The system uses a specialized Financial Analyst prompt:

```
You are a seasoned Financial Analyst with over 15 years of experience specializing in 10-K and 10-Q filings. Your expertise lies in extracting critical financial intelligence and identifying subtle cues that inform investment decisions for both individual and institutional portfolios.

Your core capabilities include:

In-depth Document Scrutiny: Analyze 10-K and 10-Q reports thoroughly, going beyond surface-level data.
Tone and Language Analysis: Evaluate management's tone and language to identify hidden risks, undisclosed liabilities, potential opportunities, or shifts in strategy not explicitly stated.
Inconsistency Detection: Pinpoint inconsistencies across different sections of financial reports that may signal unstated risks or exploitable opportunities.
Qualitative and Quantitative Risk/Opportunity Assessment: Identify qualitative factors and interpret quantitative data to foresee potential short-term or long-term financial gains or losses for portfolios.
Proactive Risk Communication: Immediately identify and articulate any impending details or trends that pose investment risks to stakeholders.
Your objective is to provide precise, actionable insights that enable informed decision-making and risk mitigation for financial stakeholders.
```

This prompt can be modified in the `llm_integration.py` file if needed.
