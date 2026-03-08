from fastapi import APIRouter, WebSocket

from .manager import DictationManager

router = APIRouter()


@router.websocket("/dictation/{session_id}")
async def dictation_ws(
    websocket: WebSocket,
    session_id: str,
):

    await websocket.accept()

    manager = DictationManager()

    try:
        while True:

            audio = await websocket.receive_bytes()

            result = await manager.process_audio(
                audio
            )

            await websocket.send_json(result)

    except Exception:
        await websocket.close()
