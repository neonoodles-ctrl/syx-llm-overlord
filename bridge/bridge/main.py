"""Main entry point for the Syx LLM Overlord bridge service."""
from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

from .config import load_config, Config
from .game_client import GameClient
from .llm_brain import LLMBrain
from .models import GameState, TickRecord, LLMDecision, CommandResult
from . import dashboard as dash_module

logger = logging.getLogger("syx-overlord")

# Global state for the decision loop
config: Config | None = None
game_client: GameClient | None = None
llm_brain: LLMBrain | None = None
tick_history: list[TickRecord] = []
ws_clients: set[WebSocket] = set()
running = False
current_state: GameState | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global config, game_client, llm_brain, running

    config = load_config()
    game_client = GameClient(config.game.mod_url)
    llm_brain = LLMBrain(config.llm)

    logging.basicConfig(
        level=getattr(logging, "INFO"),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger.info("Syx LLM Overlord bridge starting...")
    logger.info(f"LLM: {config.llm.provider}/{config.llm.model}")
    logger.info(f"Game API: {config.game.mod_url}")
    logger.info(f"Dashboard: http://localhost:{config.dashboard.port}")

    running = True
    loop_task = asyncio.create_task(decision_loop())

    yield

    running = False
    loop_task.cancel()
    if game_client:
        game_client.close()
    if llm_brain:
        llm_brain.close()


app = FastAPI(title="Syx LLM Overlord", lifespan=lifespan)

# Serve dashboard static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


async def broadcast_ws(data: dict):
    """Send data to all connected WebSocket clients."""
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.add(ws)
    ws_clients -= dead


async def decision_loop():
    """Main loop: poll game state -> LLM decides -> send commands."""
    global current_state
    tick = 0
    recent_history: list[str] = []

    while running:
        try:
            # 1. Fetch game state
            try:
                state = await asyncio.get_event_loop().run_in_executor(
                    None, game_client.get_state
                )
                current_state = state
            except Exception as e:
                logger.warning(f"Cannot reach game API: {e}")
                await broadcast_ws({"type": "error", "message": f"Game API unreachable: {e}"})
                await asyncio.sleep(config.game.poll_interval_seconds)
                continue

            # 2. Get LLM decision
            tick += 1
            logger.info(f"Tick {tick}: Getting LLM decision...")
            decision = await asyncio.get_event_loop().run_in_executor(
                None, llm_brain.decide, state, recent_history
            )
            logger.info(f"Tick {tick}: LLM mood={decision.mood}, commands={len(decision.commands)}")
            logger.info(f"Tick {tick}: Reasoning: {decision.reasoning}")

            # 3. Execute commands
            results: list[CommandResult] = []
            for cmd in decision.commands[:config.game.command_rate_limit]:
                try:
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, game_client.send_command, cmd
                    )
                    results.append(result)
                    logger.info(f"  Command '{cmd.action}': {'OK' if result.success else 'FAIL'} - {result.message}")
                except Exception as e:
                    results.append(CommandResult(success=False, message=str(e)))
                    logger.error(f"  Command '{cmd.action}' error: {e}")

            # 4. Record tick
            record = TickRecord(
                tick_number=tick,
                game_state=state,
                llm_decision=decision,
                command_results=results,
            )
            tick_history.append(record)
            if len(tick_history) > 500:
                tick_history.pop(0)

            # Format history for next prompt
            recent_history.append(
                f"Tick {tick}: {decision.mood} - {decision.reasoning} "
                f"-> {[c.action for c in decision.commands]}"
            )
            recent_history = recent_history[-10:]

            # 5. Broadcast to dashboard
            await broadcast_ws({
                "type": "tick",
                "tick": tick,
                "state": state.model_dump(),
                "decision": {
                    "reasoning": decision.reasoning,
                    "mood": decision.mood,
                    "commands": [c.model_dump(exclude_none=True) for c in decision.commands],
                },
                "results": [{"success": r.success, "message": r.message} for r in results],
            })

        except Exception as e:
            logger.error(f"Decision loop error: {e}", exc_info=True)

        await asyncio.sleep(config.game.poll_interval_seconds)


# --- API Routes ---

@app.get("/", response_class=HTMLResponse)
async def root():
    return dash_module.get_html()


@app.get("/api/health")
async def health():
    game_ok = game_client.health_check() if game_client else False
    return {"status": "ok", "game_connected": game_ok}


@app.get("/api/state")
async def get_state():
    if current_state:
        return current_state.model_dump()
    return {"error": "No state available"}


@app.get("/api/history")
async def get_history():
    return [r.model_dump() for r in tick_history[-50:]]


@app.get("/api/config")
async def get_config():
    if config:
        return {
            "llm_provider": config.llm.provider,
            "llm_model": config.llm.model,
            "poll_interval": config.game.poll_interval_seconds,
            "game_url": config.game.mod_url,
        }
    return {}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    logger.info(f"Dashboard client connected ({len(ws_clients)} total)")
    try:
        # Send current state immediately
        if current_state:
            await ws.send_json({"type": "state", "state": current_state.model_dump()})
        # Keep connection alive
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_clients.discard(ws)
        logger.info(f"Dashboard client disconnected ({len(ws_clients)} total)")


def main():
    import uvicorn
    cfg = load_config()
    uvicorn.run(
        "bridge.main:app",
        host="0.0.0.0",
        port=cfg.dashboard.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
