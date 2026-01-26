"""
Village WebSocket Routes

Real-time communication between backend and Village GUI frontend.
Enables visual representation of agent activity.

"The window into the Village"
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.village_events import get_village_broadcaster

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Village WebSocket"])


@router.websocket("/village")
async def village_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for Village GUI.

    Connect: ws://host/ws/village

    Events sent to client:
    - tool_start: Agent started executing a tool (walks to zone)
    - tool_complete: Tool finished (agent returns to square)
    - tool_error: Tool execution failed
    - connection: Initial connection confirmation
    - approval_needed: Agent needs user approval (clickable bubble)
    - input_needed: Agent needs user input (popup on click)

    Events received from client:
    - approval_response: User approved/rejected
    - input_response: User provided input
    - zone_click: User clicked a zone
    - agent_click: User clicked an agent
    """
    await websocket.accept()
    broadcaster = get_village_broadcaster()
    await broadcaster.connect(websocket)

    try:
        while True:
            # Receive messages from frontend
            data = await websocket.receive_text()
            logger.debug(f"Village GUI message: {data}")

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    # Keepalive
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif msg_type == "approval_response":
                    # User responded to approval request
                    # TODO: Route to approval handler
                    logger.info(f"Approval response: {message}")

                elif msg_type == "input_response":
                    # User provided input
                    # TODO: Route to input handler
                    logger.info(f"Input response: {message}")

                elif msg_type == "zone_click":
                    # User clicked a zone
                    zone = message.get("zone")
                    logger.debug(f"Zone clicked: {zone}")

                elif msg_type == "agent_click":
                    # User clicked an agent
                    agent_id = message.get("agent_id")
                    logger.debug(f"Agent clicked: {agent_id}")

                elif msg_type == "set_agent":
                    # Frontend requests agent change
                    agent_id = message.get("agent_id", "CLAUDE")
                    broadcaster.set_current_agent(agent_id)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from Village GUI: {data}")

    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
        logger.info("Village GUI disconnected")
    except Exception as e:
        logger.error(f"Village WebSocket error: {e}")
        broadcaster.disconnect(websocket)


@router.get("/village/status")
async def village_status():
    """Get Village WebSocket connection status."""
    broadcaster = get_village_broadcaster()
    return {
        "connections": broadcaster.connection_count,
        "current_agent": broadcaster._current_agent,
    }
