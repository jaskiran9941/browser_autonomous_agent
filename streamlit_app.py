"""
Browser MCP Agent - Streamlit UI
Control your web browser using natural language commands through a web interface
"""

import streamlit as st
import subprocess
import os
import asyncio
import threading
from pathlib import Path
from openai import OpenAI
from playwright.async_api import async_playwright
from concurrent.futures import ThreadPoolExecutor

# Page configuration
st.set_page_config(
    page_title="Browser MCP Agent",
    page_icon="🌐",
    layout="wide"
)


class BrowserController:
    """Manages browser instance with dedicated event loop thread"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.is_running = False
        self.loop = None
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=1)

    def _run_event_loop(self, loop):
        """Run event loop in dedicated thread"""
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def _ensure_loop(self):
        """Ensure we have a running event loop"""
        if self.loop is None or not self.loop.is_running():
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._run_event_loop, args=(self.loop,), daemon=True)
            self.thread.start()

    def _run_async(self, coro):
        """Run coroutine in the dedicated event loop"""
        self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=30)

    async def _async_start_browser(self, url: str):
        """Async browser launch"""
        if not self.is_running:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            self.is_running = True

        if url:
            await self.page.goto(url)

    def start_browser(self, url: str = "https://google.com"):
        """Launch browser and navigate to URL"""
        try:
            self._run_async(self._async_start_browser(url))
            return "Browser launched and ready!"
        except Exception as e:
            return f"❌ Failed to start browser: {str(e)}"

    async def _async_execute_command(self, command: str, api_key: str) -> str:
        """Execute a browser command using Claude to interpret it (async)"""
        if not self.is_running:
            return "❌ Browser not started. Please enter a URL first!"

        try:
            # Validate API key
            if not api_key or not api_key.strip():
                return "❌ API key is missing. Please enter it in the sidebar."

            # Debug: print first 15 chars of API key
            print(f"DEBUG: Using API key: {api_key[:15]}...")
            print(f"DEBUG: API key length: {len(api_key)}")

            # Use OpenAI to interpret the command
            client = OpenAI(api_key=api_key.strip())
            print(f"DEBUG: OpenAI client created successfully")

            # Ask GPT to convert natural language to specific browser actions
            response = client.chat.completions.create(
                model="gpt-4",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Given this browser command: "{command}"

Convert it to ONE specific browser action. Respond with ONLY a JSON object in this format:
{{"action": "navigate|click|fill|scroll|get_content", "selector": "css_selector_if_needed", "value": "value_if_needed", "url": "url_if_navigate"}}

Examples:
- "go to github.com" → {{"action": "navigate", "url": "https://github.com"}}
- "click the search button" → {{"action": "click", "selector": "button[aria-label='Search']"}}
- "scroll down" → {{"action": "scroll", "value": "500"}}
- "scroll up" → {{"action": "scroll", "value": "-500"}}
- "scroll down 1000px" → {{"action": "scroll", "value": "1000"}}
- "fill the search box with hello" → {{"action": "fill", "selector": "input[type='search']", "value": "hello"}}

For scroll actions: use positive numbers for scrolling down, negative for scrolling up. Default to 500 for down, -500 for up.

Respond with ONLY the JSON, nothing else."""
                }]
            )

            # Extract the JSON response
            import json
            action_text = response.choices[0].message.content

            # Parse the action
            action_text = action_text.strip()
            # Remove markdown code blocks if present
            if action_text.startswith('```'):
                lines = action_text.split('\n')
                action_text = '\n'.join(lines[1:-1])

            action = json.loads(action_text)

            # Execute the action (async)
            result = await self._async_execute_action(action)
            return result

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def execute_command(self, command: str, api_key: str) -> str:
        """Execute command using dedicated event loop"""
        try:
            return self._run_async(self._async_execute_command(command, api_key))
        except Exception as e:
            return f"❌ Error: {str(e)}"

    async def _async_execute_action(self, action: dict) -> str:
        """Execute the browser action (async)"""
        try:
            action_type = action.get("action")

            if action_type == "navigate":
                url = action.get("url", "")
                if not url.startswith("http"):
                    url = "https://" + url
                await self.page.goto(url)
                return f"✅ Navigated to {url}"

            elif action_type == "click":
                selector = action.get("selector", "")
                await self.page.click(selector, timeout=5000)
                return f"✅ Clicked element: {selector}"

            elif action_type == "fill":
                selector = action.get("selector", "")
                value = action.get("value", "")
                await self.page.fill(selector, value)
                return f"✅ Filled '{selector}' with '{value}'"

            elif action_type == "scroll":
                value = action.get("value", "500")
                # Handle direction keywords or numeric values
                if isinstance(value, str):
                    if value.lower() == "down":
                        amount = 500
                    elif value.lower() == "up":
                        amount = -500
                    else:
                        try:
                            amount = int(value)
                        except ValueError:
                            amount = 500
                else:
                    amount = int(value)

                await self.page.evaluate(f"window.scrollBy(0, {amount})")
                direction = "down" if amount > 0 else "up"
                return f"✅ Scrolled {direction} {abs(amount)}px"

            elif action_type == "get_content":
                content = await self.page.text_content("body")
                return f"📄 Page content:\n{content[:500]}..."

            else:
                return f"❌ Unknown action: {action_type}"

        except Exception as e:
            return f"❌ Action failed: {str(e)}\nTry being more specific or use different selectors."

    async def _async_close(self):
        """Close browser (async)"""
        if self.is_running:
            try:
                if self.page:
                    await self.page.close()
            except:
                pass
            try:
                if self.browser:
                    await self.browser.close()
            except:
                pass
            try:
                if self.playwright:
                    await self.playwright.stop()
            except:
                pass
            self.is_running = False

    def close(self):
        """Close browser and cleanup"""
        try:
            if self.is_running:
                self._run_async(self._async_close())
        except:
            pass
        finally:
            # Stop the event loop
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop = None
            self.thread = None


# Initialize browser controller in session state
if 'browser' not in st.session_state:
    st.session_state.browser = BrowserController()
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Title and header
st.title("🌐 Browser MCP Agent")
st.markdown("Control your web browser using natural language commands")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # Initialize API key from environment if not in session
    if 'api_key' not in st.session_state:
        env_key = os.environ.get("OPENAI_API_KEY", "")
        st.session_state.api_key = env_key
        if env_key:
            st.success(f"✅ API key loaded ({env_key[:10]}...)")

    # API Key input
    api_key_input = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state.api_key,
        help="Enter your OpenAI API key (or loaded from .env)",
        key="api_key_input"
    )

    # Update session state if changed
    if api_key_input and api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        os.environ["ANTHROPIC_API_KEY"] = api_key_input

    # Use the session state value - CRITICAL: make sure we actually have it
    api_key = st.session_state.api_key if st.session_state.api_key else api_key_input

    # Debug: show if key is actually loaded
    if api_key:
        st.caption(f"🔑 Using key: {api_key[:15]}...")
    else:
        st.warning("⚠️ No API key detected")

    st.divider()

    # URL Input and Launch
    st.header("🚀 Launch Browser")
    url_input = st.text_input(
        "Enter URL to open",
        value="https://github.com",
        placeholder="https://example.com"
    )

    if st.button("🌐 Open Browser", type="primary"):
        if not api_key:
            st.error("⚠️ Please enter your API key first")
        else:
            with st.spinner("Launching browser..."):
                result = st.session_state.browser.start_browser(url_input)
                st.success(result)
                st.session_state.messages.append({
                    "role": "system",
                    "content": f"🚀 Browser opened at {url_input}"
                })

    # Browser status
    status_color = "🟢" if st.session_state.browser.is_running else "🔴"
    status_text = "Running" if st.session_state.browser.is_running else "Not Started"
    st.markdown(f"{status_color} **Browser:** {status_text}")

    st.divider()

    # Example commands
    st.header("💡 Example Commands")
    st.markdown("""
    - **Navigation:**
      - go to reddit.com
      - navigate to news.ycombinator.com

    - **Interaction:**
      - click the search button
      - scroll down
      - scroll up 300px

    - **Forms:**
      - fill the search box with "claude"
      - type "hello" in the input field

    - **Content:**
      - get the page content
    """)

    st.divider()

    # Close browser button
    if st.button("🗑️ Close Browser"):
        st.session_state.browser.close()
        st.session_state.messages = []
        st.rerun()

# Main content area - Chat interface
st.header("💬 Command Interface")

# Display chat history
for msg in st.session_state.messages:
    role = "assistant" if msg["role"] in ["assistant", "system"] else msg["role"]
    with st.chat_message(role):
        st.markdown(msg["content"])

# Command input
if prompt := st.chat_input("Enter a browser command...", key="command_input"):
    # Get API key from session state
    current_api_key = st.session_state.get('api_key', '')

    if not current_api_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar")
    elif not st.session_state.browser.is_running:
        st.error("⚠️ Please launch the browser first using the sidebar")
    else:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Execute command with agent
        with st.chat_message("assistant"):
            with st.spinner("🤖 Executing command..."):
                # Pass API key from session state
                result = st.session_state.browser.execute_command(prompt, current_api_key)
                st.markdown(result)
                st.session_state.messages.append({"role": "assistant", "content": result})

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 10px;'>
    <strong>How it works:</strong> Enter a URL in the sidebar → Click "Open Browser" →
    A Chrome window opens → Type commands below → Watch them execute live!
</div>
""", unsafe_allow_html=True)
