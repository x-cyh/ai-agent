from __future__ import annotations

import asyncio
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

import chainlit as cl


WORKSPACE = Path(__file__).resolve().parent
os.chdir(WORKSPACE)
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from agent_core import Agent, get_token_budget  # noqa: E402


UPLOAD_DIR = WORKSPACE / ".chainlit_uploads"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def element_path(element: Any) -> Path | None:
    path_text = str(getattr(element, "path", "") or "").strip()
    if not path_text:
        return None
    return Path(path_text).resolve()


def is_image_element(element: Any) -> bool:
    source = element_path(element)
    if source is None:
        return False

    mime = str(getattr(element, "mime", "") or "").lower()
    element_type = str(getattr(element, "type", "") or "").lower()
    suffix = source.suffix.lower()
    return mime.startswith("image/") or element_type == "image" or suffix in IMAGE_EXTENSIONS


def save_uploaded_image(element: Any) -> str:
    source = element_path(element)
    if source is None:
        raise FileNotFoundError("uploaded image has no local path")
    if not source.is_file():
        raise FileNotFoundError(f"image not found: {source}")

    UPLOAD_DIR.mkdir(exist_ok=True)
    suffix = source.suffix.lower()
    if suffix not in IMAGE_EXTENSIONS:
        suffix = ".png"

    target = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    shutil.copy2(source, target)
    return str(target.relative_to(WORKSPACE))


def uploaded_image_path(message: cl.Message) -> str | None:
    for element in message.elements or []:
        if is_image_element(element):
            return save_uploaded_image(element)
    return None


async def make_agent() -> Agent | None:
    try:
        return await asyncio.to_thread(Agent.from_env)
    except RuntimeError as exc:
        await cl.Message(content=str(exc), author="System").send()
        return None


def run_agent_chat(
    agent: Agent,
    user_text: str,
    image_path: str | None,
    queue: asyncio.Queue[tuple[str, Any]],
    loop: asyncio.AbstractEventLoop,
) -> None:
    def on_token(token: str) -> None:
        if token:
            loop.call_soon_threadsafe(queue.put_nowait, ("token", token))

    try:
        reply = agent.chat(user_text, image_path=image_path, on_token=on_token)
    except Exception as exc:
        loop.call_soon_threadsafe(queue.put_nowait, ("error", exc))
        return

    loop.call_soon_threadsafe(queue.put_nowait, ("done", reply))


@cl.on_chat_start
async def on_chat_start() -> None:
    agent = await make_agent()
    cl.user_session.set("agent", agent)

    if agent is None:
        return

    await cl.Message(
        content=(
            "# Agent ready\n\n"
            f"- `TOKEN_BUDGET={get_token_budget()}`\n"
            f"- `session={agent.session_path}`\n\n"
            "Send text, or upload an image with a question. Type `clear` to reset.\n\n"
            "$$\\text{LaTeX 已啟用}$$"
        ),
        author="System",
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent = cl.user_session.get("agent")
    if agent is None:
        agent = await make_agent()
        cl.user_session.set("agent", agent)
        if agent is None:
            return

    user_text = (message.content or "").strip()
    if user_text.lower() == "clear":
        await asyncio.to_thread(agent.clear)
        await cl.Message(content="Session cleared.", author="System").send()
        return

    try:
        image_path = uploaded_image_path(message)
    except Exception as exc:
        await cl.Message(content=f"Image upload failed: {exc}", author="System").send()
        return

    if not user_text:
        if image_path is None:
            await cl.Message(
                content="Please type a message, or upload an image with a question.",
                author="System",
            ).send()
            return
        user_text = "Please analyze this image."

    queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    response = cl.Message(content="")
    await response.send()

    worker = asyncio.create_task(
        asyncio.to_thread(run_agent_chat, agent, user_text, image_path, queue, loop)
    )

    streamed = []
    while True:
        event, payload = await queue.get()

        if event == "token":
            token = str(payload)
            streamed.append(token)
            await response.stream_token(token)
            continue

        if event == "error":
            response.content = f"Error: {payload}"
            await response.update()
            break

        if event == "done":
            response.content = "".join(streamed) or str(payload)
            await response.update()
            break

    await worker
