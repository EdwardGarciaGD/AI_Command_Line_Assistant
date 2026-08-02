# AI Command-Line Assistant

Simple CLI tool to ask questions to an LLM and receive text responses.

Files and what they do:

main.py: The program you run. Shows a welcome message, asks you to type a question, sends that question to the AI client, prints the AI's reply, and lets you quit.

ai_client.py: Handles talking to the AI provider. It sends your question over HTTP, retries on temporary failures, and returns the model's text. All API details live here so the rest of the app stays clean.

config.py: Loads configuration like the API key, base URL, model name, and timeout from environment variables. It validates these settings so the app fails early if something is missing.

requirements.txt: Lists the Python packages the project needs (for example, `requests`). Use it to install dependencies.

.env: Local file for environment variables during development (contains secrets locally; do not commit to version control).

.gitignore: Tells Git which files or folders to ignore (for example `.env`, virtual environments, and temporary files).

Quick start (local development):

1. Create a Python 3.11 virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set required environment variables (for local dev you can use `.env`):

- `AI_API_KEY` - your API key
- `AI_API_BASE_URL` - the provider HTTP endpoint
- `AI_MODEL_NAME` - the model identifier to use

4. Run the assistant:

```bash
python main.py
```

Notes:
Secrets must never be hardcoded; use environment variables or a secrets manager.

ai_client.py contains retry and error-handling logic so main.py stays simple and focused on I/O.
