"""
FastAPI routes for the React frontend API.
These wrap the existing backend logic without modifying it.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import JSONResponse

from src.api.models import (
    ChatRequest,
    ChatResponse,
    ChatResponseMetadata,
    Message,
    DeliberationRequest,
    DeliberationResponse,
    DeliberationMetadata,
    PhaseEntry,
    CycleSummary,
    FinalSummary,
    HealthResponse,
    CharactersResponse,
    CharacterInfo,
    WSChatMessage,
    WSDeliberationMessage,
)
from src.characters import get_all_characters, REGISTRY
from src.gradio.app import (
    parse_mentions,
    get_character_response_stream,
    deliberate,
    CHARACTERS as CHARACTER_LIST,
    sanitize_tool_calls,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# Health / Meta
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint."""
    gradio_available = any(getattr(route, "path", None) == "/gradio" for route in request.app.routes)
    return HealthResponse(
        status="ok" if gradio_available else "degraded",
        gradio_available=gradio_available,
        timestamp=_now_iso(),
    )


@router.get("/characters", response_model=CharactersResponse)
async def list_characters():
    """List available characters."""
    characters = [
        CharacterInfo(
            name=char.name,
            emoji=getattr(char, "emoji", "💬"),
            color=getattr(char, "color", "#121314"),
        )
        for char in CHARACTER_LIST
    ]
    return CharactersResponse(characters=characters)


# =============================================================================
# Chat API (REST)
# =============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Send a message and get responses from the council.
    Non-streaming version - returns complete responses.
    """
    start_time = time.perf_counter()
    
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Determine which characters should respond
    if req.mentions:
        mentioned_names = req.mentions
    else:
        mentioned_names = parse_mentions(req.message)
        if not mentioned_names:
            mentioned_names = [char.name for char in CHARACTER_LIST]
    
    # Resolve characters
    responding_chars = []
    for name in mentioned_names:
        char = REGISTRY.get(name.lower())
        if char:
            responding_chars.append(char)
    
    if not responding_chars:
        raise HTTPException(status_code=400, detail="No valid characters mentioned")
    
    # Build LLM history from request history
    llm_history = [
        {"role": msg.role, "content": msg.content}
        for msg in req.history[-5:]  # Last 5 messages for context
    ]
    
    # Collect responses
    user_message = Message(
        role="user",
        content=req.message,
        timestamp=_now_iso(),
    )
    new_messages: list[Message] = []
    
    for char in responding_chars:
        try:
            full_response = ""
            async for chunk in get_character_response_stream(
                char, req.message, llm_history, user_key=req.api_key
            ):
                full_response += chunk
            
            new_messages.append(Message(
                role="assistant",
                content=sanitize_tool_calls(full_response.strip()),
                speaker=char.name,
                emoji=getattr(char, "emoji", "💬"),
                timestamp=_now_iso(),
            ))
            
            await asyncio.sleep(0.5)  # Rate limiting between characters
            
        except Exception as e:
            logger.error(f"Error getting response from {char.name}: {e}")
            new_messages.append(Message(
                role="assistant",
                content=f"*{char.name} seems distracted*",
                speaker=char.name,
                emoji=getattr(char, "emoji", "💬"),
                timestamp=_now_iso(),
            ))
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Combine history with new messages
    full_history = list(req.history) + [user_message] + new_messages
    
    return ChatResponse(
        history=full_history,
        metadata=ChatResponseMetadata(
            responding_characters=[char.name for char in responding_chars],
            timestamp=_now_iso(),
            duration_ms=duration_ms,
        ),
    )


# =============================================================================
# Chat API (WebSocket Streaming)
# =============================================================================

@router.websocket("/chat/stream")
async def chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chat responses.
    
    Client sends: { message: string, history: Message[], apiKey?: string, mentions?: string[] }
    Server sends: WSChatMessage events
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message = data.get("message", "").strip()
            if not message:
                await websocket.send_json(
                    WSChatMessage(type="error", error="Message cannot be empty").model_dump()
                )
                continue
            
            history = data.get("history", [])
            api_key = data.get("apiKey")
            mentions = data.get("mentions")
            
            # Determine which characters should respond
            if mentions:
                mentioned_names = mentions
            else:
                mentioned_names = parse_mentions(message)
                if not mentioned_names:
                    mentioned_names = [char.name for char in CHARACTER_LIST]
            
            # Resolve characters
            responding_chars = []
            for name in mentioned_names:
                char = REGISTRY.get(name.lower())
                if char:
                    responding_chars.append(char)
            
            if not responding_chars:
                await websocket.send_json(
                    WSChatMessage(type="error", error="No valid characters mentioned").model_dump()
                )
                continue
            
            # Build LLM history
            llm_history = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in history[-5:]
            ]
            
            # Stream responses from each character
            for char in responding_chars:
                # Signal start of character response
                await websocket.send_json(
                    WSChatMessage(type="start", character=char.name).model_dump()
                )
                
                full_response = ""
                try:
                    async for chunk in get_character_response_stream(
                        char, message, llm_history, user_key=api_key
                    ):
                        if chunk:
                            full_response += chunk
                            await websocket.send_json(
                                WSChatMessage(type="chunk", character=char.name, content=chunk).model_dump()
                            )
                    
                    # Signal end of this character's response
                    sanitized = sanitize_tool_calls(full_response.strip())
                    await websocket.send_json(
                        WSChatMessage(type="done", character=char.name, content=sanitized).model_dump()
                    )
                    
                except Exception as e:
                    logger.error(f"Streaming error for {char.name}: {e}")
                    await websocket.send_json(
                        WSChatMessage(type="error", character=char.name, error="Streaming error").model_dump()
                    )
                
                await asyncio.sleep(0.3)  # Brief pause between characters
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json(
                WSChatMessage(type="error", error="WebSocket error").model_dump()
            )
        except Exception:
            pass


# =============================================================================
# Deliberation API (REST)
# =============================================================================

@router.post("/deliberate", response_model=DeliberationResponse)
async def deliberate_endpoint(req: DeliberationRequest):
    """
    Run a structured deliberation with the council.
    Returns structured data (not HTML).
    """
    start_time = time.perf_counter()
    
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = await deliberate(
            question=req.question,
            rounds=req.rounds,
            summariser=req.summariser,
            format="llm",  # Structured data, not HTML
            structure="nested",
            user_key=req.api_key,
        )
    except Exception as e:
        logger.error(f"Deliberation error: {e}")
        raise HTTPException(status_code=500, detail="Deliberation failed")
    
    duration_ms = (time.perf_counter() - start_time) * 1000
    
    # Transform the result to match our API contract
    phases = {"thesis": [], "antithesis": [], "synthesis": []}
    
    raw_phases = result.get("phases", {})
    for phase_name in ["thesis", "antithesis", "synthesis"]:
        for entry in raw_phases.get(phase_name, []):
            phases[phase_name].append(PhaseEntry(
                cycle=entry.get("cycle", 1),
                phase=phase_name,
                character=entry.get("name", "Unknown"),
                content=entry.get("content", ""),
                timestamp=_now_iso(),
            ))
    
    cycle_summaries = [
        CycleSummary(cycle=cs.get("cycle", 1), summary=cs.get("summary", ""))
        for cs in result.get("cycle_summaries", [])
    ]
    
    final = result.get("final_summary", {})
    final_summary = FinalSummary(
        by=final.get("by", "Moderator"),
        content=final.get("content", ""),
    )
    
    return DeliberationResponse(
        question=result.get("question", req.question),
        rounds=result.get("rounds", req.rounds),
        phases=phases,
        cycle_summaries=cycle_summaries,
        final_summary=final_summary,
        metadata=DeliberationMetadata(
            character_order=result.get("character_order", []),
            seed=result.get("seed", 0),
            duration_ms=duration_ms,
        ),
    )


# =============================================================================
# Deliberation API (WebSocket Streaming) - for Theater Mode
# =============================================================================

@router.websocket("/deliberate/stream")
async def deliberate_stream(websocket: WebSocket):
    """
    WebSocket endpoint for streaming deliberation.
    Enables Theater Mode with real-time phase/character updates.
    
    Client sends: { question: string, rounds: number, summariser: string, apiKey?: string }
    Server sends: WSDeliberationMessage events
    """
    await websocket.accept()
    
    try:
        data = await websocket.receive_json()
        
        question = data.get("question", "").strip()
        if not question:
            await websocket.send_json(
                WSDeliberationMessage(type="error", error="Question cannot be empty").model_dump()
            )
            await websocket.close()
            return
        
        rounds = min(3, max(1, data.get("rounds", 1)))
        summariser = data.get("summariser", "Moderator")
        api_key = data.get("apiKey")
        
        # Import what we need for streaming deliberation
        from src.gradio.app import (
            _build_phase_prompt,
            _history_text,
            _summarize_cycle,
            _neutral_summary,
            moderator_instance,
            sanitize_tool_calls,
        )
        import random
        
        # Setup
        seed = random.randint(0, 1_000_000)
        rng = random.Random(seed)
        char_order = list(CHARACTER_LIST)
        rng.shuffle(char_order)
        
        conversation_llm = []
        phases = ["thesis", "antithesis", "synthesis"]
        
        for cycle_idx in range(rounds):
            for phase in phases:
                # Signal phase start
                await websocket.send_json(
                    WSDeliberationMessage(
                        type="phase_start",
                        phase=phase,
                        cycle=cycle_idx + 1,
                    ).model_dump()
                )
                
                for char in char_order:
                    # Signal character start
                    await websocket.send_json(
                        WSDeliberationMessage(
                            type="character_start",
                            phase=phase,
                            cycle=cycle_idx + 1,
                            character=char.name,
                        ).model_dump()
                    )
                    
                    # Build prompt
                    history_excerpt = _history_text(conversation_llm)
                    prompt = _build_phase_prompt(
                        phase=phase,
                        char=char,
                        question=question,
                        history_snippet=history_excerpt,
                    )
                    
                    # Stream response
                    full_response = ""
                    try:
                        async for chunk in get_character_response_stream(
                            char, prompt, [], user_key=api_key
                        ):
                            if chunk:
                                full_response += chunk
                                await websocket.send_json(
                                    WSDeliberationMessage(
                                        type="chunk",
                                        phase=phase,
                                        cycle=cycle_idx + 1,
                                        character=char.name,
                                        content=chunk,
                                    ).model_dump()
                                )
                    except Exception as e:
                        logger.error(f"Deliberation stream error for {char.name}: {e}")
                        full_response = f"*{char.name} could not respond.*"
                    
                    # Sanitize and record
                    full_response = sanitize_tool_calls(full_response.strip())
                    conversation_llm.append(
                        f"[{phase.upper()} | Cycle {cycle_idx + 1}] {char.name}: {full_response}"
                    )
                    
                    # Signal character done
                    await websocket.send_json(
                        WSDeliberationMessage(
                            type="character_done",
                            phase=phase,
                            cycle=cycle_idx + 1,
                            character=char.name,
                            content=full_response,
                        ).model_dump()
                    )
                    
                    await asyncio.sleep(0.5)
                
                # Signal phase done
                await websocket.send_json(
                    WSDeliberationMessage(
                        type="phase_done",
                        phase=phase,
                        cycle=cycle_idx + 1,
                    ).model_dump()
                )
            
            # Cycle summary
            cycle_text = _history_text(conversation_llm, limit=36)
            summary = await _summarize_cycle(cycle_text, user_key=api_key)
            
            await websocket.send_json(
                WSDeliberationMessage(
                    type="summary",
                    cycle=cycle_idx + 1,
                    content=summary,
                ).model_dump()
            )
        
        # Final summary
        full_history_text = "\n".join(conversation_llm)
        summariser_normalized = summariser.strip().lower()
        
        if summariser_normalized == "moderator":
            final_summary = sanitize_tool_calls(
                (await _neutral_summary(full_history_text, user_key=api_key)).strip()
            )
            summary_author = "Moderator"
        else:
            name_map = {char.name.lower(): char for char in CHARACTER_LIST}
            selected = name_map.get(summariser_normalized, moderator_instance)
            summary_author = selected.name if selected != moderator_instance else "Moderator"
            
            summary_prompt = (
                "Provide a concise synthesis (3 sentences max) from your perspective, "
                f"referencing the discussion below.\n\n{full_history_text}"
            )
            full_summary = ""
            async for chunk in get_character_response_stream(
                selected, summary_prompt, [], user_key=api_key
            ):
                full_summary += chunk
            final_summary = sanitize_tool_calls(full_summary.strip())
        
        # Signal done with final summary
        await websocket.send_json(
            WSDeliberationMessage(
                type="done",
                character=summary_author,
                content=final_summary,
            ).model_dump()
        )
        
    except WebSocketDisconnect:
        logger.info("Deliberation WebSocket client disconnected")
    except Exception as e:
        logger.error(f"Deliberation WebSocket error: {e}")
        try:
            await websocket.send_json(
                WSDeliberationMessage(type="error", error="Deliberation failed").model_dump()
            )
        except Exception:
            pass
    finally:
        await websocket.close()
