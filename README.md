# Gmail MCP Server (FastAPI + Claude Desktop)

This project is a minimal Gmail **MCP server** built with FastAPI. It exposes a `/api/v1/send-email` HTTP endpoint and an MCP tool that can be called from MCP‑aware clients like Claude Desktop, so you can send real Gmail emails just by chatting with an AI assistant.

The flow is:

1. FastAPI app provides a `POST /api/v1/send-email` endpoint that sends email via the Gmail API.
2. MCP integration wraps the app and exposes an MCP endpoint at `/mcp`.
3. Claude Desktop connects to the MCP server and calls the email tool when you ask it to send an email.

---

## 1. Project structure

The project follows a clean architecture with separation of concerns:

```
MCP/
├── main.py                 # Application entry point
├── controllers/            # HTTP request handlers
│   ├── __init__.py
│   └── email_controller.py
├── services/              # Business logic layer
│   ├── __init__.py
│   ├── email_service.py   # Email business logic
│   └── gmail_service.py  # Gmail API operations
├── models/                # Data models (Pydantic)
│   ├── __init__.py
│   └── email_models.py
├── mcp_integration/       # MCP protocol integration
│   ├── __init__.py
│   └── tools.py
├── test_gmail_auth.py     # OAuth setup script
└── requirements.txt       # Python dependencies
```

Key files:

* `main.py` – Application entry point with FastAPI app factory and MCP integration.
* `controllers/email_controller.py` – HTTP endpoint handlers for email operations.
* `services/email_service.py` – Business logic for email operations.
* `services/gmail_service.py` – Gmail API service (OAuth, MIME message creation, sending).
* `models/email_models.py` – Pydantic models for request/response validation.
* `mcp_integration/tools.py` – MCP tool definitions for Claude Desktop integration.
* `test_gmail_auth.py` – One‑time script to perform Gmail OAuth and create `token.json`.
* `requirements.txt` – Python dependencies.

**Not in Git (must be provided by each user):**

* `credentials.json` – Google OAuth client secrets downloaded from Google Cloud.
* `token.json` – Gmail access/refresh tokens generated locally after you run `test_gmail_auth.py`.

---

## 2. Prerequisites

Before you start, install:

* **Python 3.11+**
* **Node.js** (for `npx` – used by Claude Desktop to run the MCP bridge)
* **Claude Desktop** (latest version from Anthropic's website)
* A Google account with access to Gmail

Clone the repo:
```bash
git clone <repository-url>
cd MCP
```

---

## 3. Set up Python environment

Create and activate a virtual environment:

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source venv/bin/activate  # macOS/Linux
```

Install dependencies:
```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, Gmail API libraries, `mcp`, etc.

---

## 4. Enable Gmail API and get credentials

1. Go to the **Google Cloud Console** and create a project (or use an existing one).
2. In **APIs & Services → Library**, enable the **Gmail API** for your project.
3. In **APIs & Services → Credentials**, create credentials:  
   * Type: **OAuth client ID**  
   * Application type: **Desktop app**
4. Download the `credentials.json` file and place it in the **root** of this project (same folder as `main.py`).
5. Make sure `credentials.json` is **not** committed to Git; it is in `.gitignore`.

---

## 5. Run Gmail OAuth once (`test_gmail_auth.py`)

With the venv active and `credentials.json` in place:

```bash
python test_gmail_auth.py
```

What this does:

* If `token.json` does not exist, it opens a browser window for Google login and consent.
* After you approve access, it saves `token.json` in the project root.
* Subsequent runs reuse or refresh this token without asking you to log in again.

Both `credentials.json` and `token.json` are local to your machine and should never be committed.

---

## 6. Start the Gmail MCP server

Start the FastAPI + MCP server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

Where `app` is the FastAPI instance created in `main.py`.

By default this runs on `http://127.0.0.1:8000`.

### 6.1 Test the HTTP API (optional but recommended)

Open Swagger UI:

* Go to `http://localhost:8000/docs` in your browser.
* Find `POST /api/v1/send-email`.
* Click **Try it out** and use a JSON body like:

```json
{
  "to_email": "your-recipient@example.com",
  "subject": "MCP Gmail test",
  "body": "Hello from the Gmail MCP FastAPI server!"
}
```

Click **Execute**. You should see a success response and receive an email at the target address.

You can do the same from `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/send-email" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "your-recipient@example.com",
    "subject": "MCP Gmail test via curl",
    "body": "Hello from the Gmail MCP FastAPI server (curl)."
  }'
```

---

## 7. MCP endpoint

The MCP server is exposed at:

```
http://localhost:8000/mcp
```

If you open that URL in a browser, you will see a JSON‑RPC error like:

```json
{"jsonrpc":"2.0","id":"server-error","error":{"code":-32600,"message":"Not Acceptable: Client must accept text/event-stream"}}
```

This is expected. MCP over HTTP uses **Server‑Sent Events**, so it requires special headers. MCP clients (like Claude Desktop) handle this for you.

---

## 8. Connect to Claude Desktop

Claude Desktop needs a **local MCP process** that speaks MCP over stdio. We use a small bridge called `mcp-remote` (run via `npx`) which forwards between Claude Desktop and your HTTP MCP server.

### 8.1 Install Node.js

If you don't have Node.js, install the latest LTS from the official website. This gives you `npm` and `npx`.

### 8.2 Edit `claude_desktop_config.json`

Claude Desktop stores its config in `claude_desktop_config.json`. On Windows it is typically located at:

```
C:\Users\<YourUsername>\AppData\Roaming\Claude\claude_desktop_config.json
```

In Claude Desktop:

1. Open **Settings → Developer → Edit Config** to open this file.
2. Add the following block under `"mcpServers"` (merge with existing content if needed):

```json
{
  "mcpServers": {
    "gmail-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8000/mcp",
        "--transport",
        "http-only"
      ]
    }
  }
}
```

* `gmail-mcp` is the name of this MCP server as seen by Claude.
* `command` and `args` start a local bridge process that connects Claude Desktop to your HTTP MCP endpoint.

Save the file.

### 8.3 Restart Claude Desktop

1. Quit Claude Desktop completely (including tray icon).
2. Start Claude Desktop again so it reloads the config.
3. Ensure your FastAPI server is still running (`python main.py` or `uvicorn main:app --reload`).

In a new chat, Claude should now be able to use the `gmail-mcp` server.

---

## 9. Using the Gmail MCP tool from Claude

With everything running:

1. Open a new Claude Desktop chat.
2. Ask something like:

> "Use the gmail-mcp server to send an email to `your-recipient@example.com` with subject `Test from Claude MCP` and body `Hello from my local Gmail MCP server`."

Claude will:

* Discover the `gmail-mcp` tools.
* Call the tool that maps to `POST /api/v1/send-email` with `to_email`, `subject`, and `body`.
* Your FastAPI logs should show the email being sent.
* You should receive the email at the recipient address.

---

## 10. Security notes

* **Do not commit** `credentials.json` or `token.json` to Git.
* Only run this server on your own machine or in a secure environment; it has the power to send email from your Gmail account.
* For demos, use a dedicated Gmail account if possible.

---

## API Reference

### POST `/api/v1/send-email`

Send an email via Gmail API.

**Request Body:**
```json
{
  "to_email": "recipient@example.com",
  "subject": "Email Subject",
  "body": "Email body content",
  "is_html": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully to recipient@example.com",
  "subject": "Email Subject"
}
```

## MCP Tools

### send_email

Send an email using Gmail API.

**Parameters:**
- `to_email` (required): Recipient email address
- `subject` (required): Email subject line
- `body` (required): Email body content
- `is_html` (optional): Whether the body is HTML formatted (default: false)

## Additional Endpoints

### GET `/api/v1/auth/status`

Check Gmail authentication status and get diagnostic information.

**Response:**
```json
{
  "authenticated": true,
  "credentials_file_exists": true,
  "token_file_exists": true,
  "message": "Authentication successful",
  "instructions": []
}
```

## Troubleshooting

1. **Authentication errors:**
   - Ensure `credentials.json` is in the project root
   - Run `test_gmail_auth.py` to generate `token.json`
   - Check that Gmail API is enabled in Google Cloud Console
   - Visit `http://localhost:8000/api/v1/auth/status` to check authentication status

2. **Connection errors:**
   - Verify the FastAPI server is running on port 8000
   - Check that `mcp-remote` can be found by `npx`
   - Ensure Node.js is installed

3. **MCP server not loading:**
   - Verify the path in Claude Desktop config
   - Check that all dependencies are installed
   - Restart Claude Desktop after configuration changes
   - Check Claude Desktop logs for errors

## License

MIT
