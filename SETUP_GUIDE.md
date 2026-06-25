# fal.ai MCP Server - Setup & Quick Start Guide

## Complete Setup Instructions

### Step 1: Prerequisites

- Python 3.8 or higher
- pip package manager
- fal.ai account with API key
- Claude.ai Pro or Enterprise (for MCP integration)

### Step 2: Get Your API Key

1. Visit [fal.ai Dashboard](https://www.fal.ai/dashboard)
2. Log in with your account
3. Go to Settings → API Keys
4. Copy your API key (looks like: `key_abc123...`)
5. Keep this private and secure

### Step 3: Install and Configure

#### Option A: Using Environment Variable (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd fal-mcp

# Install dependencies
pip install -r requirements.txt

# Set API key
export FAL_API_KEY="key_abc123..."

# Run server
python fal_mcp.py
```

#### Option B: Using .env File

```bash
# Clone and install as above
cd fal-mcp
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
FAL_API_KEY=key_abc123...
FAL_API_URL=https://api.fal.ai
EOF

# Run server
python fal_mcp.py
```

#### Option C: Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FAL_API_KEY=${FAL_API_KEY}
CMD ["python", "fal_mcp.py"]
```

Build and run:
```bash
docker build -t fal-mcp .
docker run -e FAL_API_KEY=key_abc123... fal-mcp
```

### Step 4: Verify Installation

Test that everything is working:

```bash
# Test import
python -c "from fal_mcp import mcp; print('✓ fal_mcp loaded')"
python -c "from fal_api_client import *; print('✓ fal_api_client loaded')"
python -c "from models import *; print('✓ models loaded')"

# Test server startup (Ctrl+C to exit)
export FAL_API_KEY="test"
python fal_mcp.py --help
```

### Step 5: Integrate with Claude

#### In Claude.ai

1. Open Claude.ai
2. Settings → Developer → MCP Servers
3. Click "Add MCP Server"
4. Configure:
   - **Name**: fal.ai
   - **Transport**: Command
   - **Command**: `python`
   - **Arguments**: `["/absolute/path/to/fal_mcp.py"]`
   - **Environment Variables**: `FAL_API_KEY=your-key-here`
5. Click "Connect"
6. Wait for status to show "Connected"

#### Testing Connection

In Claude chat:
```
Please list the first 5 available AI applications on fal.ai.
```

Claude should use the MCP server to respond with actual applications.

## Quick Start Examples

### Example 1: Generate an Image

**Conversation with Claude:**

> "Using fal.ai, generate an image with the prompt 'a cat wearing sunglasses'. Use the FLUX model and get me the result."

Claude will:
1. Search for image generation applications
2. Find the FLUX model
3. Submit a job with your prompt
4. Poll until completion
5. Return the generated image URL

### Example 2: Check Account Status

> "What's my current fal.ai account status and how many credits do I have left?"

Claude will:
1. Call `get_account_info`
2. Call `get_usage_stats` for the last 7 days
3. Provide a summary of credits and usage

### Example 3: Batch Process Images

> "I have 5 images I want to process with an ML model. Here are the URLs: [list]. Submit them all as a batch."

Claude will:
1. Search for appropriate application
2. Submit all 5 as a batch using `submit_batch_job`
3. Return request IDs for tracking
4. Offer to poll for results

### Example 4: Monitor Long-Running Job

> "I submitted a job earlier with ID req_abc123. What's its status?"

Claude will:
1. Poll the job status
2. Show current position in queue
3. Estimate time remaining
4. Offer to wait and check later

## Server Modes

### Stdio Transport (Default)

Best for: Local development, Claude.ai integration

```bash
python fal_mcp.py
```

- Runs in foreground
- Reads from stdin, writes to stdout
- Single connection per instance

### HTTP Transport

Best for: Server deployments, multiple clients

```bash
python fal_mcp.py --transport streamable_http --port 8000
```

- Listens on specified port
- Supports multiple concurrent connections
- Can be accessed from remote machines

### Custom Configuration

Edit `fal_mcp.py` line at end of file:

```python
if __name__ == "__main__":
    # Change transport or add configuration
    mcp.run(transport="streamable_http", port=8000)
```

## Troubleshooting

### Issue: "FAL_API_KEY is not set"

**Solution:**
```bash
# Verify key is set
echo $FAL_API_KEY

# If empty, set it
export FAL_API_KEY="your-key-here"

# Or create .env file
echo "FAL_API_KEY=your-key-here" > .env
```

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution:**
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or individual packages
pip install mcp httpx pydantic
```

### Issue: "Connection refused" or "Cannot connect to API"

**Solution:**
```bash
# Check internet connection
ping api.fal.ai

# Verify API URL
echo $FAL_API_URL

# Check fal.ai status
# Visit https://status.fal.ai
```

### Issue: Jobs timeout or fail

**Solution:**
1. Check job logs: Use `get_job_logs` with the request ID
2. Check account: Verify sufficient credits with `get_account_info`
3. Check status: Use `poll_job_status` to see current status
4. Review parameters: Ensure input_data matches application schema

### Issue: "Permission denied" or "Unauthorized"

**Solution:**
```bash
# Verify API key is correct
# Visit https://www.fal.ai/dashboard/keys

# Try regenerating key if needed
# Settings → API Keys → Regenerate

# Ensure key has necessary permissions
# Check subscription tier at https://www.fal.ai/pricing
```

## Performance Optimization

### For High-Volume Usage

1. **Increase HTTP timeout** in `fal_api_client.py`:
   ```python
   DEFAULT_TIMEOUT = 60.0  # Increase from 30.0
   ```

2. **Use batch operations** instead of individual jobs:
   ```python
   # Instead of multiple submit_job calls
   # Use submit_batch_job with list of inputs
   ```

3. **Implement polling backoff** in your script:
   ```python
   import time
   async def wait_for_completion(request_id, max_retries=360):
       for attempt in range(max_retries):
           status = await poll_job_status(request_id)
           if status["status"] == "COMPLETED":
               return status
           wait_time = min(2 ** (attempt // 10), 30)  # Exponential backoff
           await asyncio.sleep(wait_time)
   ```

### Monitoring

Track server performance:

```python
# In fal_mcp.py - add logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Before making API calls
logger.info(f"Submitting job to {application_id}")

# After completion
logger.info(f"Job {request_id} completed in {execution_time}ms")
```

## Production Deployment

### Using Systemd

Create `/etc/systemd/system/fal-mcp.service`:

```ini
[Unit]
Description=fal.ai MCP Server
After=network.target

[Service]
Type=simple
User=claude
WorkingDirectory=/home/claude/fal-mcp
Environment="FAL_API_KEY=your-key-here"
ExecStart=/usr/bin/python3 /home/claude/fal-mcp/fal_mcp.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fal-mcp
sudo systemctl start fal-mcp
sudo systemctl status fal-mcp
```

### Using Supervisor

Create `/etc/supervisor/conf.d/fal-mcp.conf`:

```ini
[program:fal-mcp]
command=/usr/bin/python3 /home/claude/fal-mcp/fal_mcp.py
directory=/home/claude/fal-mcp
user=claude
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/fal-mcp.log
environment=FAL_API_KEY="your-key-here"
```

Start:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fal-mcp
```

## Next Steps

1. **Explore Applications**: Use `list_applications` to find available AI models
2. **Read Documentation**: Visit [docs.fal.ai](https://docs.fal.ai) for detailed API docs
3. **Try Examples**: Start with simple image generation or analysis tasks
4. **Scale Up**: Use batch operations for production workloads
5. **Monitor Usage**: Check account info regularly to track credit usage

## Support & Resources

- **fal.ai Docs**: https://docs.fal.ai
- **Dashboard**: https://www.fal.ai/dashboard
- **Status**: https://status.fal.ai
- **API Playground**: https://www.fal.ai/dashboard/playground
- **Community**: https://discord.gg/fal-ai

## Version History

- **1.0.0** (2024): Initial release
  - All core tools implemented
  - Full async support
  - Comprehensive error handling
  - MCP protocol 1.0+ compatible
