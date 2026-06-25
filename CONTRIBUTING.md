# Contributing

## Getting Started

```bash
git clone https://github.com/FritzHeider/Fal.ai.mcp.git
cd Fal.ai.mcp
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your FAL_API_KEY
```

## Making Changes

1. Fork the repo and create a branch from `main`
2. Keep changes focused — one feature or fix per PR
3. Test your changes: `python -c "import fal_mcp; print('OK')"`
4. Open a pull request with a clear description of what changed and why

## Adding a Tool

1. Add the input model to `models.py`
2. Add the API call to `fal_api_client.py`
3. Register the tool with `@mcp.tool()` in `fal_mcp.py`

## Reporting Issues

Open a GitHub issue with:
- What you did
- What you expected
- What actually happened
- Python version and OS
