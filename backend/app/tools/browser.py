"""
Tier 10: Browser Tools (The Exploring Hands)

Steel Browser integration for web automation.
"The hands that reach into any page"
"""

import base64
import logging
from typing import Optional
from uuid import uuid4

import httpx

from app.config import get_settings
from app.tools import registry
from app.tools.base import BaseTool, ToolSchema, ToolResult, ToolContext, ToolCategory

logger = logging.getLogger(__name__)
settings = get_settings()

# Steel Browser API client
STEEL_TIMEOUT = 60.0  # Seconds - browser operations can be slow


async def _steel_request(
    method: str,
    endpoint: str,
    json_data: Optional[dict] = None,
    expect_binary: bool = False,
) -> tuple[bool, any, Optional[str]]:
    """
    Make a request to the Steel Browser API.

    Returns: (success, result, error)
    """
    if not settings.steel_url:
        return False, None, "Steel Browser not configured (STEEL_URL not set)"

    url = f"{settings.steel_url.rstrip('/')}{endpoint}"

    try:
        async with httpx.AsyncClient(timeout=STEEL_TIMEOUT) as client:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=json_data or {})
            elif method == "DELETE":
                response = await client.delete(url)
            else:
                return False, None, f"Unsupported method: {method}"

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_data.get("error", str(error_data)))
                except Exception:
                    error_msg = response.text[:500]
                return False, None, f"Steel API error ({response.status_code}): {error_msg}"

            if expect_binary:
                return True, response.content, None
            else:
                return True, response.json(), None

    except httpx.TimeoutException:
        return False, None, "Steel Browser request timed out"
    except Exception as e:
        logger.exception(f"Steel Browser request failed: {e}")
        return False, None, str(e)


# ============================================================================
# Tool 1: browser_scrape - Quick page scraping (stateless)
# ============================================================================

class BrowserScrapeTool(BaseTool):
    """Scrape content from a web page."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="browser_scrape",
            description="""Fetch and extract content from a web page using a real browser.
Unlike simple HTTP fetch, this renders JavaScript and handles dynamic content.
Returns clean HTML, extracted text, links, and metadata.

Use cases:
- Extract content from SPAs (React, Vue, etc.)
- Get text from JavaScript-rendered pages
- Analyze page structure and links
- Extract metadata (title, description, Open Graph tags)

Example: browser_scrape(url="https://news.ycombinator.com")""",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to scrape"
                    },
                    "wait_for": {
                        "type": "integer",
                        "description": "Milliseconds to wait for page to load (default: 0)",
                        "default": 0
                    }
                },
                "required": ["url"]
            },
            category=ToolCategory.BROWSER,
            requires_auth=True,
            requires_confirmation=False,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        url = params["url"]
        wait_for = params.get("wait_for", 0)

        success, result, error = await _steel_request(
            "POST",
            "/v1/scrape",
            json_data={
                "url": url,
                "delay": wait_for,
            }
        )

        if not success:
            return ToolResult(success=False, error=error)

        # Extract useful parts from Steel response
        content = result.get("content", {})
        metadata = result.get("metadata", {})
        links = result.get("links", [])

        # Clean up HTML if present (truncate if too long)
        html = content.get("html", "")
        if len(html) > 50000:
            html = html[:50000] + "\n\n[... truncated ...]"

        return ToolResult(
            success=True,
            result={
                "url": metadata.get("urlSource", url),
                "title": metadata.get("title", ""),
                "description": metadata.get("description", ""),
                "html": html,
                "links": links[:50],  # Limit links
                "status_code": metadata.get("statusCode"),
                "language": metadata.get("language"),
                "og_title": metadata.get("ogTitle"),
                "og_description": metadata.get("ogDescription"),
                "og_image": metadata.get("ogImage"),
            }
        )


# ============================================================================
# Tool 2: browser_pdf - Generate PDF from page
# ============================================================================

class BrowserPdfTool(BaseTool):
    """Generate a PDF from a web page."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="browser_pdf",
            description="""Generate a PDF document from a web page.
The PDF captures the full rendered page including JavaScript content.
Returns a base64-encoded PDF that can be saved to the vault.

Use cases:
- Save articles for offline reading
- Archive web pages as documents
- Generate reports from web dashboards
- Create printable versions of web content

Example: browser_pdf(url="https://example.com/report")""",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to convert to PDF"
                    },
                    "save_to_vault": {
                        "type": "boolean",
                        "description": "Save the PDF to user's vault (default: false)",
                        "default": False
                    },
                    "filename": {
                        "type": "string",
                        "description": "Filename if saving to vault (default: auto-generated)"
                    }
                },
                "required": ["url"]
            },
            category=ToolCategory.BROWSER,
            requires_auth=True,
            requires_confirmation=False,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        url = params["url"]
        save_to_vault = params.get("save_to_vault", False)
        filename = params.get("filename")

        success, pdf_bytes, error = await _steel_request(
            "POST",
            "/v1/pdf",
            json_data={"url": url},
            expect_binary=True
        )

        if not success:
            return ToolResult(success=False, error=error)

        # Base64 encode for transport
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_size = len(pdf_bytes)

        result = {
            "url": url,
            "size_bytes": pdf_size,
            "pdf_base64": pdf_base64[:100] + "..." if len(pdf_base64) > 100 else pdf_base64,
            "full_pdf_base64": pdf_base64,  # Full data for saving
        }

        # Optionally save to vault
        if save_to_vault and context.user_id:
            try:
                from app.tools.vault import VaultWriteTool
                from pathlib import Path
                import re

                # Generate filename from URL if not provided
                if not filename:
                    # Extract domain and path for filename
                    clean_url = re.sub(r'[^\w\-_.]', '_', url.split("://")[-1])
                    filename = f"{clean_url[:50]}.pdf"

                # Save via vault - base64 decode first
                vault_tool = VaultWriteTool()
                vault_result = await vault_tool.execute(
                    {
                        "path": f"/browser/{filename}",
                        "content": pdf_base64,
                        "encoding": "base64",
                    },
                    context
                )

                if vault_result.success:
                    result["vault_path"] = f"/browser/{filename}"
                    result["saved_to_vault"] = True
                else:
                    result["vault_error"] = vault_result.error

            except Exception as e:
                logger.warning(f"Failed to save PDF to vault: {e}")
                result["vault_error"] = str(e)

        # Don't return full base64 in display result (too large)
        del result["full_pdf_base64"]

        return ToolResult(success=True, result=result)


# ============================================================================
# Tool 3: browser_session - Create/manage browser sessions
# ============================================================================

class BrowserSessionTool(BaseTool):
    """Create a browser session for multi-step interactions."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="browser_session",
            description="""Create or manage a persistent browser session.
Sessions maintain state (cookies, localStorage) across multiple actions.
Use for multi-step workflows like form filling, login flows, or complex navigation.

Actions:
- "create": Create a new browser session
- "list": List active sessions
- "close": Close a session by ID

Sessions auto-expire after 5 minutes of inactivity.
Maximum 2 concurrent sessions per user.

Example: browser_session(action="create")""",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "list", "close"],
                        "description": "Action to perform"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID (required for 'close' action)"
                    }
                },
                "required": ["action"]
            },
            category=ToolCategory.BROWSER,
            requires_auth=True,
            requires_confirmation=True,  # Sessions use resources
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        action = params["action"]
        session_id = params.get("session_id")

        if action == "create":
            success, result, error = await _steel_request(
                "POST",
                "/v1/sessions",
                json_data={}
            )

            if not success:
                return ToolResult(success=False, error=error)

            return ToolResult(
                success=True,
                result={
                    "session_id": result.get("id"),
                    "status": result.get("status"),
                    "websocket_url": result.get("websocketUrl"),
                    "dimensions": result.get("dimensions"),
                    "user_agent": result.get("userAgent"),
                    "created_at": result.get("createdAt"),
                    "message": "Session created. Use browser_action to interact with pages."
                }
            )

        elif action == "list":
            success, result, error = await _steel_request("GET", "/v1/sessions")

            if not success:
                return ToolResult(success=False, error=error)

            sessions = result if isinstance(result, list) else result.get("sessions", [])
            return ToolResult(
                success=True,
                result={
                    "sessions": [
                        {
                            "id": s.get("id"),
                            "status": s.get("status"),
                            "created_at": s.get("createdAt"),
                            "duration": s.get("duration"),
                        }
                        for s in sessions
                    ],
                    "count": len(sessions)
                }
            )

        elif action == "close":
            if not session_id:
                return ToolResult(success=False, error="session_id required for close action")

            success, result, error = await _steel_request(
                "DELETE",
                f"/v1/sessions/{session_id}"
            )

            if not success:
                # Session might already be closed
                if "not found" in str(error).lower():
                    return ToolResult(
                        success=True,
                        result={"message": "Session already closed or not found"}
                    )
                return ToolResult(success=False, error=error)

            return ToolResult(
                success=True,
                result={"message": f"Session {session_id} closed"}
            )

        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")


# ============================================================================
# Tool 4: browser_action - Interact with a page in a session
# ============================================================================

class BrowserActionTool(BaseTool):
    """Perform actions in a browser session."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="browser_action",
            description="""Perform actions in an existing browser session.
Requires an active session from browser_session(action="create").

Actions:
- "goto": Navigate to a URL
- "click": Click an element by CSS selector
- "type": Type text into an input field
- "screenshot": Take a screenshot (returns base64 PNG)
- "content": Get current page content

For advanced automation, combine multiple actions in sequence.

Example:
1. browser_session(action="create") -> get session_id
2. browser_action(session_id=..., action="goto", url="https://example.com")
3. browser_action(session_id=..., action="type", selector="input[name=q]", text="hello")
4. browser_action(session_id=..., action="click", selector="button[type=submit]")""",
            input_schema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from browser_session"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["goto", "click", "type", "screenshot", "content"],
                        "description": "Action to perform"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL for 'goto' action"
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for 'click' and 'type' actions"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text for 'type' action"
                    }
                },
                "required": ["session_id", "action"]
            },
            category=ToolCategory.BROWSER,
            requires_auth=True,
            requires_confirmation=True,  # Can interact with external sites
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        session_id = params["session_id"]
        action = params["action"]

        # Steel uses CDP (Chrome DevTools Protocol) for session actions
        # We need to connect via WebSocket, which is complex
        # For now, implement a simplified REST-based approach

        # Note: This is a simplified implementation
        # Full CDP support would require WebSocket connection management

        if action == "goto":
            url = params.get("url")
            if not url:
                return ToolResult(success=False, error="url required for goto action")

            # Use session context endpoint
            success, result, error = await _steel_request(
                "POST",
                f"/v1/sessions/{session_id}/context",
                json_data={"url": url}
            )

            if not success:
                return ToolResult(success=False, error=error)

            return ToolResult(
                success=True,
                result={"message": f"Navigated to {url}", "url": url}
            )

        elif action == "screenshot":
            # Session screenshot
            success, png_bytes, error = await _steel_request(
                "POST",
                f"/v1/sessions/{session_id}/screenshot",
                expect_binary=True
            )

            if not success:
                return ToolResult(success=False, error=error)

            screenshot_base64 = base64.b64encode(png_bytes).decode("utf-8")

            return ToolResult(
                success=True,
                result={
                    "screenshot_base64": screenshot_base64[:100] + "..." if len(screenshot_base64) > 100 else screenshot_base64,
                    "size_bytes": len(png_bytes),
                    "message": "Screenshot captured (base64 PNG)"
                }
            )

        elif action == "content":
            # Get page content
            success, result, error = await _steel_request(
                "GET",
                f"/v1/sessions/{session_id}/content"
            )

            if not success:
                return ToolResult(success=False, error=error)

            return ToolResult(success=True, result=result)

        elif action in ["click", "type"]:
            # These require CDP WebSocket - return informative error
            return ToolResult(
                success=False,
                error=f"Action '{action}' requires WebSocket CDP connection. "
                      f"Consider using browser_scrape for read-only operations, "
                      f"or the session's websocket_url for advanced automation."
            )

        else:
            return ToolResult(success=False, error=f"Unknown action: {action}")


# ============================================================================
# Tool 5: browser_screenshot - Quick screenshot (stateless)
# ============================================================================

class BrowserScreenshotTool(BaseTool):
    """Take a screenshot of a web page."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="browser_screenshot",
            description="""Take a screenshot of a web page.
Creates a temporary session, captures the screenshot, and cleans up.
Returns a base64-encoded PNG image.

Use for:
- Visual verification of page content
- Capturing dynamic/JavaScript content
- Creating visual records

Note: For multiple screenshots of the same page, use browser_session
with browser_action(action="screenshot") for better performance.

Example: browser_screenshot(url="https://example.com")""",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to screenshot"
                    },
                    "full_page": {
                        "type": "boolean",
                        "description": "Capture full page (default: true)",
                        "default": True
                    }
                },
                "required": ["url"]
            },
            category=ToolCategory.BROWSER,
            requires_auth=True,
            requires_confirmation=False,
        )

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        url = params["url"]
        full_page = params.get("full_page", True)

        # Create a temporary session
        success, session_result, error = await _steel_request(
            "POST",
            "/v1/sessions",
            json_data={}
        )

        if not success:
            return ToolResult(success=False, error=f"Failed to create session: {error}")

        session_id = session_result.get("id")

        try:
            # Navigate to URL
            success, _, error = await _steel_request(
                "POST",
                f"/v1/sessions/{session_id}/context",
                json_data={"url": url}
            )

            if not success:
                return ToolResult(success=False, error=f"Failed to navigate: {error}")

            # Wait a moment for page to render
            import asyncio
            await asyncio.sleep(2)

            # Take screenshot
            success, png_bytes, error = await _steel_request(
                "POST",
                f"/v1/sessions/{session_id}/screenshot",
                json_data={"fullPage": full_page},
                expect_binary=True
            )

            if not success:
                return ToolResult(success=False, error=f"Failed to capture screenshot: {error}")

            screenshot_base64 = base64.b64encode(png_bytes).decode("utf-8")

            return ToolResult(
                success=True,
                result={
                    "url": url,
                    "size_bytes": len(png_bytes),
                    "screenshot_base64": screenshot_base64,
                    "full_page": full_page,
                }
            )

        finally:
            # Clean up session
            await _steel_request("DELETE", f"/v1/sessions/{session_id}")


# ============================================================================
# Register all browser tools
# ============================================================================

def _register_tools():
    """Register all browser tools."""
    tools = [
        BrowserScrapeTool(),
        BrowserPdfTool(),
        BrowserSessionTool(),
        BrowserActionTool(),
        BrowserScreenshotTool(),
    ]

    for tool in tools:
        registry.register(tool)
        logger.debug(f"Registered browser tool: {tool.name}")


# Auto-register on import
_register_tools()
