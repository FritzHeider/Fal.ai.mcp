# fal.ai MCP Server - Testing & Configuration Guide

## Configuration Template

### .env File Template

Create a `.env` file in the project root with the following template:

```bash
# fal.ai API Configuration
# Get your key from: https://www.fal.ai/dashboard/keys
FAL_API_KEY=key_your_actual_key_here

# API URL (optional, defaults to https://api.fal.ai)
FAL_API_URL=https://api.fal.ai

# Logging Configuration (optional)
LOG_LEVEL=INFO
DEBUG=false
```

### Configuration by Environment

#### Development
```bash
FAL_API_KEY=key_dev_xxxxx
FAL_API_URL=https://api.fal.ai
LOG_LEVEL=DEBUG
DEBUG=true
```

#### Staging
```bash
FAL_API_KEY=key_staging_xxxxx
FAL_API_URL=https://api.fal.ai
LOG_LEVEL=INFO
DEBUG=false
```

#### Production
```bash
FAL_API_KEY=key_prod_xxxxx
FAL_API_URL=https://api.fal.ai
LOG_LEVEL=WARNING
DEBUG=false
```

## Testing Guide

### Test 1: Environment Setup

```bash
#!/bin/bash
# verify_setup.sh

echo "Checking fal.ai MCP Setup..."

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Python: $python_version"

# Check dependencies
echo "Checking dependencies..."
python3 -c "import mcp; print('✓ mcp')" || exit 1
python3 -c "import httpx; print('✓ httpx')" || exit 1
python3 -c "import pydantic; print('✓ pydantic')" || exit 1

# Check API key
if [ -z "$FAL_API_KEY" ]; then
    echo "✗ FAL_API_KEY not set"
    exit 1
fi
echo "✓ FAL_API_KEY is set"

# Check files exist
for file in fal_mcp.py fal_api_client.py models.py; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
        exit 1
    fi
done

echo ""
echo "Setup verification complete! ✓"
```

### Test 2: API Connection

```python
#!/usr/bin/env python3
# test_connection.py

import asyncio
import os

async def test_connection():
    """Test connection to fal.ai API."""
    
    # Check API key
    api_key = os.environ.get("FAL_API_KEY")
    if not api_key:
        print("✗ FAL_API_KEY not set")
        return False
    
    print(f"✓ API key found (length: {len(api_key)})")
    
    try:
        from fal_api_client import list_applications
        
        print("Testing API connection...")
        result = await list_applications(limit=1)
        
        if result:
            print("✓ Connected to fal.ai API")
            print(f"✓ Retrieved {len(result.get('items', []))} application(s)")
            return True
        else:
            print("✗ No response from API")
            return False
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    exit(0 if success else 1)
```

### Test 3: Tool Execution

```python
#!/usr/bin/env python3
# test_tools.py

import asyncio
from models import ListApplicationsInput, ResponseFormat
from fal_mcp import list_applications

async def test_tools():
    """Test all tool functions."""
    
    tests = [
        {
            "name": "list_applications",
            "input": ListApplicationsInput(
                limit=5,
                response_format=ResponseFormat.MARKDOWN
            )
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"Testing: {test['name']}...")
            result = await list_applications(test['input'])
            
            if result and not result.startswith("Error"):
                print(f"  ✓ Passed")
                passed += 1
            else:
                print(f"  ✗ Failed: {result[:100]}")
                failed += 1
                
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(test_tools())
    exit(0 if success else 1)
```

### Test 4: Server Startup

```bash
#!/bin/bash
# test_server.sh

echo "Testing fal.ai MCP Server Startup..."
echo ""

# Test import
python3 -c "from fal_mcp import mcp; print('✓ Server module imports correctly')" || exit 1

# Test with timeout
echo "Starting server (10 second timeout)..."
timeout 10s python3 fal_mcp.py > /dev/null 2>&1 &
server_pid=$!

# Give it a moment to start
sleep 2

# Check if running
if ps -p $server_pid > /dev/null; then
    echo "✓ Server started successfully"
    kill $server_pid 2>/dev/null
    exit 0
else
    echo "✗ Server failed to start"
    exit 1
fi
```

### Test 5: Comprehensive Integration Test

```python
#!/usr/bin/env python3
# integration_test.py

import asyncio
import os
from typing import List, Tuple

async def run_test(name: str, test_func):
    """Run a single test."""
    try:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print('='*60)
        result = await test_func()
        if result:
            print(f"✓ {name} PASSED")
            return True
        else:
            print(f"✗ {name} FAILED")
            return False
    except Exception as e:
        print(f"✗ {name} FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_applications():
    """Test listing applications."""
    from fal_api_client import list_applications
    
    result = await list_applications(limit=5)
    assert result is not None
    assert "items" in result or "applications" in result
    print(f"Found {len(result.get('items', []))} applications")
    return True


async def test_get_application():
    """Test getting application details."""
    from fal_api_client import list_applications, get_application
    
    # First list to get an ID
    apps = await list_applications(limit=1)
    app_id = apps.get("items", [{}])[0].get("id")
    
    if not app_id:
        print("No application found to test")
        return False
    
    result = await get_application(app_id)
    assert result is not None
    print(f"Retrieved details for app: {app_id}")
    return True


async def test_account_info():
    """Test getting account info."""
    from fal_api_client import get_account_info
    
    result = await get_account_info()
    assert result is not None
    assert "user_id" in result or "email" in result
    print(f"Account info retrieved")
    return True


async def test_usage_stats():
    """Test getting usage stats."""
    from fal_api_client import get_usage_stats
    
    result = await get_usage_stats(days=7)
    assert result is not None
    print(f"Usage stats retrieved")
    return True


async def main():
    """Run all tests."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║           fal.ai MCP Server - Integration Tests                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Check API key
    if not os.environ.get("FAL_API_KEY"):
        print("✗ FAL_API_KEY not set")
        print("Please set your API key before running tests:")
        print("  export FAL_API_KEY='your-key-here'")
        exit(1)
    
    tests: List[Tuple[str, callable]] = [
        ("List Applications", test_list_applications),
        ("Get Application", test_get_application),
        ("Account Info", test_account_info),
        ("Usage Stats", test_usage_stats),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = await run_test(test_name, test_func)
        results.append((test_name, result))
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
```

## Running Tests

### Quick Test

```bash
# Test setup
bash test_setup.sh

# Test connection
python3 test_connection.py

# Test tools
python3 test_tools.py
```

### Full Integration Test

```bash
# Set up environment
export FAL_API_KEY="key_your_key_here"

# Run comprehensive tests
python3 integration_test.py
```

### Server Test

```bash
# Start server and verify it runs
bash test_server.sh

# Or run directly and check manually
export FAL_API_KEY="key_your_key_here"
python3 fal_mcp.py
```

## Troubleshooting Tests

### Module Not Found

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Verify installation
python3 -c "import mcp; import httpx; import pydantic; print('OK')"
```

### Connection Refused

```bash
# Check API key
echo $FAL_API_KEY

# Check internet connection
ping api.fal.ai

# Check fal.ai status
curl https://status.fal.ai
```

### Timeout Errors

```bash
# May need to increase timeout
# Edit fal_api_client.py:
# DEFAULT_TIMEOUT = 60.0  # Increase from 30.0
```

### Authentication Failed

```bash
# Regenerate API key at https://www.fal.ai/dashboard/keys
# Ensure key is set correctly without extra spaces
echo "Key length: ${#FAL_API_KEY}"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: fal.ai MCP Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        FAL_API_KEY: ${{ secrets.FAL_API_KEY }}
      run: |
        python3 integration_test.py
```

## Performance Benchmarking

```python
#!/usr/bin/env python3
# benchmark.py

import asyncio
import time
from fal_api_client import list_applications, get_account_info

async def benchmark_operation(name: str, operation, *args):
    """Benchmark a single operation."""
    start = time.time()
    result = await operation(*args)
    elapsed = time.time() - start
    
    print(f"{name:30} {elapsed*1000:8.2f}ms")
    return elapsed

async def main():
    """Run performance benchmarks."""
    print("fal.ai MCP - Performance Benchmarks\n")
    
    benchmarks = [
        ("list_applications", list_applications, 10),
        ("get_account_info", get_account_info),
    ]
    
    total_time = 0
    for test in benchmarks:
        elapsed = await benchmark_operation(*test)
        total_time += elapsed
    
    print(f"\nTotal time: {total_time*1000:.2f}ms")

if __name__ == "__main__":
    asyncio.run(main())
```

## Monitoring

### Log Monitoring

```bash
# View real-time logs
tail -f /var/log/fal-mcp.log

# Search for errors
grep ERROR /var/log/fal-mcp.log

# Count operations by type
grep "submit_job" /var/log/fal-mcp.log | wc -l
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "Checking fal.ai MCP Health..."

# Check process
if pgrep -f "fal_mcp.py" > /dev/null; then
    echo "✓ Server process running"
else
    echo "✗ Server process not running"
    exit 1
fi

# Check API connectivity
if python3 -c "import asyncio; asyncio.run(__import__('fal_api_client').get_account_info())" 2>/dev/null; then
    echo "✓ API connectivity OK"
else
    echo "✗ API connectivity failed"
    exit 1
fi

echo "Health check passed ✓"
```
