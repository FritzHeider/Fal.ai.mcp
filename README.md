# fal.ai MCP Server

MCP server for interacting with the [fal.ai](https://fal.ai) API — run AI models, submit jobs, and manage media generation workflows from Claude or any MCP-compatible client.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your API key (get one at [fal.ai/dashboard/keys](https://www.fal.ai/dashboard/keys)):

```
FAL_API_KEY=your-api-key-here
```

## Running

```bash
# stdio (default, for Claude Desktop / MCP clients)
python fal_mcp.py

# HTTP transport
python fal_mcp.py --transport streamable_http --port 8000
```

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fal": {
      "command": "/path/to/venv/bin/python",
      "args": ["/path/to/fal_mcp.py"],
      "env": { "FAL_API_KEY": "your-api-key-here" }
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_applications` | Browse available AI models and apps |
| `get_application` | Get schema and details for a specific app |
| `submit_job` | Queue a job with input parameters |
| `poll_job_status` | Check job status (QUEUED / IN_PROGRESS / COMPLETED / FAILED) |
| `get_job_result` | Retrieve output from a completed job |
| `cancel_job` | Cancel a queued or in-progress job |
| `list_queue_items` | List jobs in an application's queue |
| `get_job_logs` | Get execution logs for a job |
| `submit_batch_job` | Submit multiple jobs in parallel |
| `get_account_info` | View subscription and credit balance |
| `get_usage_stats` | View usage over the last N days |

## Typical Workflow

```
list_applications (search: "image")
  → submit_job (application_id, input_data)
  → poll_job_status (request_id) [repeat until COMPLETED]
  → get_job_result (request_id)
```

## Project Structure

```
fal_mcp.py          # MCP server + tool definitions
fal_api_client.py   # HTTP client for fal.ai API
models.py           # Pydantic input/output models
requirements.txt    # Dependencies
```

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `FAL_API_KEY` | Yes | — |
| `FAL_API_URL` | No | `https://api.fal.ai` |
