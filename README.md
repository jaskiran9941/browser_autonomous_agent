# Browser MCP Agent

Control your web browser using natural language commands powered by GPT-4 and Playwright.

## What This Project Does

This agent lets you automate browser tasks using plain English:
- Navigate to websites
- Click buttons and links
- Fill out forms
- Scroll pages (up/down with custom amounts)
- Extract page content
- Execute multi-step workflows

**Features:**
- 🌐 **Streamlit Web UI** - Visual interface with real-time browser control
- 🤖 **GPT-4 Powered** - Natural language understanding for browser commands
- 🔄 **Thread-Safe** - Reliable async Playwright implementation
- 📸 **Live Browser Window** - Watch commands execute in real-time

## Tech Stack

- **OpenAI GPT-4** - Natural language command interpretation
- **Playwright (Async)** - Browser automation with thread-safe event loops
- **Streamlit** - Interactive web UI
- **Python 3.9+** - Modern async/await patterns

## Setup

### Prerequisites
- Python 3.9 or higher
- OpenAI API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jaskiran9941/browser_mcp_agent.git
   cd browser_mcp_agent
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

5. **Set up your OpenAI API key:**

   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your-api-key-here
   ```

   Or export it:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Usage

### Running the Streamlit Web UI

1. **Start the application:**
   ```bash
   ./run_streamlit.sh
   ```

   Or manually:
   ```bash
   source venv/bin/activate
   streamlit run streamlit_app.py
   ```

2. **Open in your browser:**
   - Navigate to http://localhost:8501

3. **Using the interface:**
   - Your OpenAI API key will be auto-loaded from `.env`
   - Enter a starting URL (e.g., https://github.com)
   - Click "Open Browser" - a Chrome window will appear
   - Type commands in the chat input
   - Watch commands execute live in the browser window

## Example Commands

**Navigation:**
- `go to reddit.com`
- `navigate to news.ycombinator.com`

**Interaction:**
- `click the search button`
- `scroll down`
- `scroll up 300px`
- `scroll down 1000px`

**Forms:**
- `fill the search box with "claude"`
- `type "hello" in the input field`

**Content:**
- `get the page content`

## How It Works

1. **You type a command** - Natural language like "scroll down" or "go to github.com"
2. **GPT-4 interprets it** - Converts your command to a structured action (navigate, click, fill, scroll, etc.)
3. **Playwright executes it** - Performs the action in the live browser window
4. **You see the result** - Both in the browser window and in the chat

## UI Features

- 💬 **Chat Interface** - Conversational command input
- 🟢 **Browser Status** - See if browser is running
- 📝 **Command History** - Track all executed commands
- 💡 **Example Commands** - Built-in command suggestions
- 🎯 **Error Handling** - Clear error messages with suggestions

## Project Structure

```
browser_mcp_agent/
├── streamlit_app.py            # Main Streamlit web UI with async Playwright
├── run_streamlit.sh            # Streamlit launcher script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
├── .env.example                # Example environment file
└── venv/                       # Python virtual environment
```

## Technical Implementation

### Thread-Safe Async Architecture

This project solves the common Streamlit + Playwright threading issue using:

- **Dedicated Event Loop Thread** - Persistent asyncio event loop runs in background thread
- **Async Playwright API** - All browser operations use `async_playwright()` instead of sync API
- **Thread-Safe Execution** - `asyncio.run_coroutine_threadsafe()` submits work from Streamlit to browser thread
- **Persistent Browser Objects** - Browser, page objects stay in same event loop across all operations

This ensures browser commands work reliably across Streamlit reruns without "different thread" or "different loop" errors.

### Command Processing Pipeline

1. User enters natural language command
2. GPT-4 converts to structured JSON action
3. Action validated and parsed
4. Async Playwright executes in dedicated thread
5. Result returned to Streamlit UI

## Troubleshooting

**Browser won't start:**
- Make sure Chromium is installed: `playwright install chromium`
- Check that your OpenAI API key is set

**Thread/loop errors:**
- Click "Close Browser" in sidebar
- Click "Open Browser" to restart with fresh connection

**Commands not working:**
- Try being more specific with selectors
- Check the browser window for actual page state
- Use simpler commands first (scroll, navigate) before complex clicks

## Requirements

The `requirements.txt` includes:
- `streamlit` - Web UI framework
- `playwright` - Browser automation
- `openai` - GPT-4 API client
- `anthropic` - (Optional) For future Claude integration
- `requests` - HTTP library

## Future Enhancements

- Add screenshot capture and display
- Support for multiple browser tabs
- Command history persistence
- Visual element selection
- Macro recording and playback
- Integration with Claude API for improved command understanding

## License

MIT
