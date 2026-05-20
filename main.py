import base64
import copy
import json
import os
import platform
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    message_chunk_to_message,
)
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI


WORKSPACE = Path.cwd().resolve()
MEMORY_DIR = WORKSPACE / "memory"
MEMORY_PATH = MEMORY_DIR / "MEMORY.md"
MEMORY_HISTORY_PATH = MEMORY_DIR / "HISTORY.md"
COMPACTABLE_TOOL_NAMES = {
    "read_file",
    "exec",
    "grep",
    "glob",
    "web_search",
    "web_fetch",
    "list_dir",
}


def runtime_env_note() -> str:
    sys_name = platform.system()
    if os.name == "nt":
        shell_hint = "This is Windows. Use PowerShell-compatible one-line commands; do not use Bash heredoc syntax such as <<EOF."
    else:
        shell_hint = "This is a Unix-like environment. Use POSIX shell-compatible one-line commands unless a project script says otherwise."
    return (
        f"【執行環境】platform.system()={sys_name}; os.name={os.name}. "
        f"{shell_hint}"
    )


def get_identity() -> str:
    """WG-12: classroom rules, display name, runtime OS, and exec guidance."""
    system_text = (
        "你是課堂練習用的 Agent。請使用繁體中文回答，保持清楚、務實、可驗收。"
        "遇到需要精確讀檔、寫檔、列目錄、替換內容、執行指令、計算或查驗專案狀態時，必須優先使用工具，不要只憑印象猜測。"
    )
    nick = "法鬥超人"
    exec_note = (
        "【exec 注意】請先依【執行環境】選擇 shell 寫法，不要假設一定是 Linux Bash。"
        "若要執行多行 Python，先用 write_file 寫成 .py，再用 exec 執行 `uv run python 相對路徑`。"
        "不要用 exec 代替 read_file/write_file/edit_file 來讀寫 workspace 檔案。"
    )
    return f"{system_text}\n\n本場次顯示名稱：{nick}\n\n{runtime_env_note()}\n\n{exec_note}"


def resolve_workspace_path(path: str | Path) -> Path:
    raw = Path(path)
    if raw.is_absolute():
        raise PermissionError("absolute paths are not allowed")
    target = (WORKSPACE / raw).resolve()
    try:
        target.relative_to(WORKSPACE)
    except ValueError as exc:
        raise PermissionError(f"path is outside workspace: {path}") from exc
    return target


@tool("read_file")
def read_file(path: str, offset: int = 1, limit: int = 200) -> str:
    """Read a UTF-8 text file inside the workspace and return numbered lines."""
    try:
        target = resolve_workspace_path(path)
        if not target.is_file():
            return f"Error: not a file: {path}"
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(offset - 1, 0)
        end = min(start + max(limit, 1), len(lines))
        return "\n".join(f"{i + 1}| {line}" for i, line in enumerate(lines[start:end], start))
    except Exception as exc:
        return f"Error: {exc}"


@tool("write_file")
def write_file(path: str, content: str) -> str:
    """Write UTF-8 text to a file inside the workspace."""
    try:
        target = resolve_workspace_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} characters to {path}"
    except Exception as exc:
        return f"Error: {exc}"


@tool("edit_file")
def edit_file(path: str, old_text: str, new_text: str, replace_all: bool = False) -> str:
    """Replace exact text in a UTF-8 workspace file."""
    try:
        target = resolve_workspace_path(path)
        text = target.read_text(encoding="utf-8", errors="replace")
        count = text.count(old_text)
        if count == 0:
            return "Error: old_text not found"
        if count > 1 and not replace_all:
            return "Error: old_text appears multiple times; set replace_all=true to replace all matches"
        target.write_text(text.replace(old_text, new_text, -1 if replace_all else 1), encoding="utf-8")
        return f"edited {path}; replacements={count if replace_all else 1}"
    except Exception as exc:
        return f"Error: {exc}"


@tool("list_dir")
def list_dir(path: str = ".", recursive: bool = False, max_entries: int = 200) -> str:
    """List files and directories inside the workspace."""
    try:
        root = resolve_workspace_path(path)
        if not root.is_dir():
            return f"Error: not a directory: {path}"
        iterator = root.rglob("*") if recursive else root.iterdir()
        entries = [str(item.relative_to(WORKSPACE)) for item in iterator][: max(max_entries, 1)]
        return "\n".join(entries) if entries else "(empty)"
    except Exception as exc:
        return f"Error: {exc}"


@tool("exec")
def exec_workspace(command: str, timeout: int = 30) -> str:
    """Run one shell command in the workspace and return exit code plus captured output."""
    blocked = ("rm -rf", "del /f", "rmdir /s", "format ", "shutdown", "git reset --hard")
    lowered = command.lower()
    if any(part in lowered for part in blocked):
        return "Error: blocked dangerous command"

    child_env = os.environ.copy()
    child_env.setdefault("PYTHONUTF8", "1")
    child_env.setdefault("PYTHONIOENCODING", "utf-8")
    run_kwargs: dict[str, Any] = {
        "cwd": str(WORKSPACE),
        "shell": True,
        "capture_output": True,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "timeout": max(1, min(timeout, 120)),
        "env": child_env,
    }
    if os.name == "nt":
        run_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(command, **run_kwargs)
        output = ((result.stdout or "") + (result.stderr or "")).strip()
        if len(output) > 4000:
            output = output[:4000] + "\n\n[truncated]"
        if not output:
            output = "(no stdout or stderr)"
        return f"exit_code={result.returncode}\n{output}"
    except Exception as exc:
        return f"Error: {exc}"


@tool("add_numbers")
def add_numbers(a: float, b: float) -> float:
    """Add two numbers. Any arithmetic addition request should use this tool."""
    return a + b


TOOLS: list[BaseTool] = [read_file, write_file, edit_file, list_dir, exec_workspace, add_numbers]
TOOL_BY_NAME: dict[str, BaseTool] = {t.name: t for t in TOOLS}


def tool_parameters(tool_obj: BaseTool) -> dict[str, Any]:
    schema_obj = getattr(tool_obj, "args_schema", None)
    if schema_obj and hasattr(schema_obj, "model_json_schema"):
        return schema_obj.model_json_schema()
    return {"type": "object", "properties": getattr(tool_obj, "args", {}) or {}}


def cast_params(schema: dict[str, Any], params: dict[str, Any]) -> dict[str, Any]:
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    out = dict(params)
    for key, spec in props.items():
        if key not in out or not isinstance(spec, dict):
            continue
        typ = spec.get("type")
        value = out[key]
        try:
            if typ == "integer" and isinstance(value, str):
                out[key] = int(value)
            elif typ == "number" and isinstance(value, str):
                out[key] = float(value)
            elif typ == "boolean" and isinstance(value, str):
                if value.lower() in ("true", "1", "yes", "y"):
                    out[key] = True
                elif value.lower() in ("false", "0", "no", "n"):
                    out[key] = False
        except ValueError:
            pass
    return out


def validate_params(schema: dict[str, Any], params: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    props = schema.get("properties", {}) if isinstance(schema, dict) else {}
    for required in schema.get("required", []) or []:
        if required not in params:
            errors.append(f"missing required parameter: {required}")
    for key, value in params.items():
        spec = props.get(key)
        if not isinstance(spec, dict):
            continue
        typ = spec.get("type")
        if typ == "integer" and not isinstance(value, int):
            errors.append(f"{key} must be integer")
        elif typ == "number" and not isinstance(value, (int, float)):
            errors.append(f"{key} must be number")
        elif typ == "boolean" and not isinstance(value, bool):
            errors.append(f"{key} must be boolean")
        elif typ == "string" and not isinstance(value, str):
            errors.append(f"{key} must be string")
    return errors


def prepare_tool_call(name: str, raw_args: Any) -> tuple[BaseTool | None, dict[str, Any], str | None]:
    tool_obj = TOOL_BY_NAME.get(name)
    if tool_obj is None:
        return None, {}, f"unknown tool: {name}"
    if raw_args is None:
        args: dict[str, Any] = {}
    elif isinstance(raw_args, dict):
        args = dict(raw_args)
    else:
        return tool_obj, {}, "tool arguments must be a JSON object"
    schema = tool_parameters(tool_obj)
    args = cast_params(schema, args)
    errors = validate_params(schema, args)
    return tool_obj, args, "; ".join(errors) if errors else None


def image_bytes_to_data_url(data: bytes, media_type: str) -> str:
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{b64}"


def guess_media_type(path: Path, fallback: str = "image/png") -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    if ext == ".gif":
        return "image/gif"
    return fallback


def parse_user_input(raw: str) -> tuple[str, Path | None, str | None]:
    if not raw.startswith("/image "):
        return raw, None, None
    rest = raw.removeprefix("/image ").strip()
    if not rest:
        return "", None, None
    path_text, _, text = rest.partition(" ")
    try:
        full = resolve_workspace_path(path_text)
    except Exception as exc:
        print(f"[warn] image rejected: {exc}")
        return text.strip(), None, None
    if not full.is_file():
        print(f"[warn] missing image for current turn: {path_text}")
        return text.strip(), None, None
    media_type = guess_media_type(full)
    rel = full.relative_to(WORKSPACE)
    return text.strip() or "請描述這張圖片。", rel, media_type


def build_human_message_for_current_turn(text: str, image_rel: Path | None, media_type: str | None) -> HumanMessage:
    if image_rel is None:
        return HumanMessage(content=text)
    full = resolve_workspace_path(image_rel)
    url = image_bytes_to_data_url(full.read_bytes(), media_type or guess_media_type(full))
    return HumanMessage(
        content=[
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": url}},
        ]
    )


def persistent_human_message(text: str, image_rel: Path | None, media_type: str | None) -> HumanMessage:
    kwargs: dict[str, Any] = {"plain_text": text}
    if image_rel is not None:
        kwargs["image_path"] = str(image_rel)
        kwargs["media_type"] = media_type
    return HumanMessage(content=text, additional_kwargs=kwargs)


def history_user_placeholder(text: str, image_path: str, media_type: str | None = None) -> str:
    extra = f"[此回合曾附圖，路徑：{image_path}]"
    if media_type:
        extra += f" [media_type={media_type}]"
    return f"{text}\n\n{extra}".strip()


def human_to_text_only(message: HumanMessage) -> HumanMessage:
    content = message.content
    if isinstance(content, str):
        return message
    text_parts: list[str] = []
    for block in content if isinstance(content, list) else []:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(str(block.get("text", "")))
    body = "\n".join(part for part in text_parts if part).strip() or "[歷史多模態訊息已省略圖像內容]"
    return HumanMessage(content=body + "\n\n[歷史附圖未重送，僅保留文字占位]")


def messages_for_model(
    system_message: SystemMessage,
    history: list[BaseMessage],
    human_message: HumanMessage,
) -> list[BaseMessage]:
    out: list[BaseMessage] = [copy.deepcopy(system_message)]
    for item in history:
        copied = copy.deepcopy(item)
        if isinstance(copied, HumanMessage) and not isinstance(copied.content, str):
            copied = human_to_text_only(copied)
        out.append(copied)
    out.append(copy.deepcopy(human_message))
    return out


def default_metadata(created_at: str | None = None) -> dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "_type": "metadata",
        "key": "session",
        "created_at": created_at or now,
        "updated_at": now,
        "metadata": {},
        "last_consolidated": 0,
    }


def load_session_jsonl(path: str) -> tuple[list[BaseMessage], dict[str, Any] | None]:
    if not os.path.exists(path):
        return [], None

    messages: list[BaseMessage] = []
    meta: dict[str, Any] | None = None
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            if obj.get("_type") == "metadata":
                meta = obj
                continue

            role = obj.get("role")
            if role == "user":
                text = str(obj.get("content", ""))
                image_path = obj.get("image_path")
                media_type = obj.get("media_type")
                if image_path:
                    placeholder = history_user_placeholder(text, str(image_path), str(media_type) if media_type else None)
                    messages.append(
                        HumanMessage(
                            content=placeholder,
                            additional_kwargs={
                                "plain_text": text,
                                "image_path": str(image_path),
                                "media_type": media_type,
                            },
                        )
                    )
                else:
                    messages.append(HumanMessage(content=text, additional_kwargs={"plain_text": text}))
            elif role == "assistant":
                content = str(obj.get("content", ""))
                tool_calls = obj.get("tool_calls")
                messages.append(AIMessage(content=content, tool_calls=tool_calls) if tool_calls else AIMessage(content=content))
            elif role == "tool":
                messages.append(ToolMessage(content=str(obj.get("content", "")), tool_call_id=str(obj.get("tool_call_id") or "")))
    return messages, meta


def save_session_jsonl(
    path: str,
    messages: list[BaseMessage],
    existing_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    now = datetime.now().isoformat()
    meta = default_metadata(created_at=now) if existing_meta is None else dict(existing_meta)
    meta["_type"] = "metadata"
    meta["key"] = meta.get("key", "session")
    meta.setdefault("created_at", now)
    meta["updated_at"] = now
    meta.setdefault("metadata", {})
    meta.setdefault("last_consolidated", 0)

    lines = [json.dumps(meta, ensure_ascii=False)]
    for message in messages:
        timestamp = datetime.now().isoformat()
        if isinstance(message, HumanMessage):
            text = str(message.additional_kwargs.get("plain_text") or message.content)
            row: dict[str, Any] = {"role": "user", "content": text, "timestamp": timestamp}
            image_path = message.additional_kwargs.get("image_path")
            if image_path:
                row["image_path"] = image_path
                row["media_type"] = message.additional_kwargs.get("media_type")
        elif isinstance(message, AIMessage):
            row = {"role": "assistant", "content": message.content, "timestamp": timestamp}
            tool_calls = getattr(message, "tool_calls", None)
            if tool_calls:
                row["tool_calls"] = tool_calls
        elif isinstance(message, ToolMessage):
            row = {
                "role": "tool",
                "content": message.content,
                "tool_call_id": message.tool_call_id,
                "timestamp": timestamp,
            }
        else:
            continue
        lines.append(json.dumps(row, ensure_ascii=False))

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return meta


def estimate_message_tokens(message: BaseMessage) -> int:
    content = message.content
    if isinstance(content, str):
        cost = len(content)
    else:
        cost = len(json.dumps(content, ensure_ascii=False, default=str))
    if isinstance(message, AIMessage) and getattr(message, "tool_calls", None):
        cost += len(json.dumps(message.tool_calls, ensure_ascii=False, default=str))
    return cost


def message_cost(messages: list[BaseMessage]) -> int:
    return sum(estimate_message_tokens(message) for message in messages)


def pick_consolidation_boundary(
    messages: list[BaseMessage],
    last_consolidated: int,
    tokens_to_remove: int,
) -> tuple[int, int] | None:
    start = last_consolidated
    if start >= len(messages) or tokens_to_remove <= 0:
        return None

    removed_tokens = 0
    last_boundary: tuple[int, int] | None = None
    for idx in range(start, len(messages)):
        message = messages[idx]
        if idx > start and isinstance(message, HumanMessage):
            last_boundary = (idx, removed_tokens)
            if removed_tokens >= tokens_to_remove:
                return last_boundary
        removed_tokens += estimate_message_tokens(message)
    return last_boundary


def memory_block_for_system() -> str:
    if not MEMORY_PATH.exists():
        return ""
    max_chars = int(os.getenv("MEMORY_MAX_CHARS", "6000"))
    text = MEMORY_PATH.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return ""
    if len(text) > max_chars:
        text = text[-max_chars:]
    return f"## Long-term Memory\n\n{text}"


def append_memory_history(label: str, body: str) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(MEMORY_HISTORY_PATH, "a", encoding="utf-8") as handle:
        handle.write(f"\n[{stamp}] {label}\n{body.strip()}\n")


def messages_to_plain_transcript(messages: list[BaseMessage]) -> str:
    rows: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, ToolMessage):
            role = "tool"
        else:
            role = message.type
        rows.append(f"{role}: {message.content}")
    return "\n\n".join(rows)


def consolidate_memory(
    llm: ChatOpenAI,
    chunk: list[BaseMessage],
    previous_memory: str,
    target_chars: int,
) -> str | None:
    prompt = (
        "請用繁體中文更新長期記憶。只保留未來對話需要的使用者偏好、決策、專案狀態與重要約束；"
        "不要逐字抄對話，不要保存冗長 tool 輸出，不要重複 skill 流程。\n\n"
        f"既有 MEMORY.md:\n{previous_memory or '(empty)'}\n\n"
        f"要整併的舊對話:\n{messages_to_plain_transcript(chunk)}\n\n"
        f"請輸出新的 MEMORY.md 內容，控制在約 {target_chars} 字以內。"
    )
    try:
        response = llm.invoke([SystemMessage(content="You update concise long-term memory."), HumanMessage(content=prompt)])
    except Exception as exc:
        append_memory_history("[CONSOLIDATION-FAILED]", str(exc))
        return None
    text = str(response.content).strip()
    if not text:
        append_memory_history("[CONSOLIDATION-FAILED]", "empty consolidation response")
        return None
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_PATH.write_text(text, encoding="utf-8")
    append_memory_history("[CONSOLIDATED]", text)
    return text


def ensure_budget_and_maybe_consolidate(
    llm: ChatOpenAI,
    system_text: str,
    history: list[BaseMessage],
    human_message: HumanMessage,
    session_meta: dict[str, Any] | None,
) -> tuple[list[BaseMessage], dict[str, Any] | None]:
    budget = int(os.getenv("TOKEN_BUDGET", "8000"))
    meta = default_metadata() if session_meta is None else dict(session_meta)
    last_consolidated = int(meta.get("last_consolidated", 0) or 0)
    past0 = history[last_consolidated:]
    cost = len(system_text) + message_cost([*past0, human_message])
    if cost <= budget:
        return past0, meta

    tokens_to_remove = max(0, cost - budget // 2)
    boundary = pick_consolidation_boundary(history, last_consolidated, tokens_to_remove)
    if boundary is None:
        return past0, meta

    idx, _removed = boundary
    chunk = history[last_consolidated:idx]
    previous_memory = MEMORY_PATH.read_text(encoding="utf-8", errors="replace") if MEMORY_PATH.exists() else ""
    updated = consolidate_memory(llm, chunk, previous_memory, budget // 2)
    if updated is not None:
        meta["last_consolidated"] = idx
        return history[idx:], meta
    return past0, meta


def message_to_dict(message: BaseMessage) -> dict[str, Any]:
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    if isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    if isinstance(message, AIMessage):
        row: dict[str, Any] = {"role": "assistant", "content": message.content}
        if getattr(message, "tool_calls", None):
            row["tool_calls"] = message.tool_calls
        return row
    if isinstance(message, ToolMessage):
        return {
            "role": "tool",
            "tool_call_id": message.tool_call_id,
            "name": getattr(message, "name", None) or "",
            "content": message.content,
        }
    return {"role": message.type, "content": str(message.content)}


def dict_cost(row: dict[str, Any]) -> int:
    return len(str(row.get("content", ""))) + len(json.dumps(row.get("tool_calls", ""), ensure_ascii=False, default=str))


def build_messages_for_model(
    messages: list[dict[str, Any]],
    *,
    max_chars: int,
    max_tool_chars: int,
    keep_recent_tools: int,
) -> list[dict[str, Any]]:
    out = [dict(row) for row in messages]

    assistant_tool_ids = {
        call.get("id")
        for row in out
        if row.get("role") == "assistant"
        for call in (row.get("tool_calls") or [])
        if isinstance(call, dict) and call.get("id")
    }
    out = [row for row in out if row.get("role") != "tool" or row.get("tool_call_id") in assistant_tool_ids]

    present_tool_ids = {row.get("tool_call_id") for row in out if row.get("role") == "tool"}
    fixed: list[dict[str, Any]] = []
    for row in out:
        fixed.append(row)
        if row.get("role") == "assistant":
            for call in row.get("tool_calls") or []:
                call_id = call.get("id") if isinstance(call, dict) else None
                if call_id and call_id not in present_tool_ids:
                    fixed.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": call.get("name", "") if isinstance(call, dict) else "",
                            "content": "[Tool result unavailable; call was interrupted or lost]",
                        }
                    )
    out = fixed

    for row in out:
        if row.get("role") == "tool":
            content = str(row.get("content", ""))
            if len(content) > max_tool_chars:
                row["content"] = content[:max_tool_chars] + "\n\n[truncated]"

    compactable_indexes = [
        i
        for i, row in enumerate(out)
        if row.get("role") == "tool" and str(row.get("name") or "") in COMPACTABLE_TOOL_NAMES
    ]
    for idx in compactable_indexes[:-keep_recent_tools]:
        content = str(out[idx].get("content", ""))
        if len(content) >= 500:
            name = out[idx].get("name") or "tool"
            out[idx]["content"] = f"[{name} result omitted from context]"

    while sum(dict_cost(row) for row in out) > max_chars:
        user_indexes = [i for i, row in enumerate(out) if row.get("role") == "user"]
        if len(user_indexes) <= 1:
            break
        start = user_indexes[0]
        end = user_indexes[1]
        del out[start:end]
        if not out or out[0].get("role") != "system":
            out.insert(0, {"role": "user", "content": "(conversation continued)"})
    return out


@dataclass
class SkillEntry:
    name: str
    path: Path
    source: str
    description: str
    always: bool
    body: str


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return {}, text
    meta: dict[str, str] = {}
    for raw in lines[1:end]:
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1 :]).strip()


class SkillsLoader:
    def __init__(self, workspace: Path, builtin_skills_dir: Path) -> None:
        self.workspace_skills = workspace / "skills"
        self.builtin_skills = builtin_skills_dir

    def entries_from_dir(self, root: Path, source: str, skip: set[str]) -> list[SkillEntry]:
        if not root.exists():
            return []
        entries: list[SkillEntry] = []
        for skill_dir in sorted(root.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_file.exists() or skill_dir.name in skip:
                continue
            text = skill_file.read_text(encoding="utf-8", errors="replace")
            meta, body = split_frontmatter(text)
            entries.append(
                SkillEntry(
                    name=skill_dir.name,
                    path=skill_file,
                    source=source,
                    description=meta.get("description") or skill_dir.name,
                    always=meta.get("always", "false").lower() == "true",
                    body=body,
                )
            )
        return entries

    def list_skills(self) -> list[SkillEntry]:
        workspace_entries = self.entries_from_dir(self.workspace_skills, "workspace", set())
        workspace_names = {entry.name for entry in workspace_entries}
        builtin_entries = self.entries_from_dir(self.builtin_skills, "builtin", workspace_names)
        return workspace_entries + builtin_entries

    def load_skill(self, name: str) -> str | None:
        for root in (self.workspace_skills, self.builtin_skills):
            path = root / name / "SKILL.md"
            if path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
        return None


def build_skills_summary(entries: list[SkillEntry]) -> str:
    summarized = [entry for entry in entries if not entry.always]
    if not summarized:
        return ""
    return "\n".join(f"- **{entry.name}**：{entry.description} `{entry.path}`" for entry in summarized)


def build_system_prompt(loader: SkillsLoader) -> str:
    parts = [get_identity()]
    memory = memory_block_for_system()
    if memory:
        parts.append(memory)

    entries = loader.list_skills()
    active = [entry for entry in entries if entry.always]
    if active:
        body = "\n\n---\n\n".join(f"### Skill: {entry.name}\n\n{entry.body}" for entry in active)
        parts.append(f"# Active Skills\n\n{body}")

    summary = build_skills_summary(entries)
    if summary:
        intro = (
            "可用技能如下。當任務需要某項技能時，請先用 read_file 讀取該路徑的 SKILL.md，"
            "再依內容執行；若需要依賴或工具，先說明並使用合適的 workspace 工具確認。\n\n"
        )
        parts.append("# Skills\n\n" + intro + summary)
    return "\n\n---\n\n".join(parts)


def stream_ai_message(llm_with_tools: Any, messages: list[BaseMessage], stream_stdout: bool) -> AIMessage:
    acc: AIMessageChunk | None = None
    for chunk in llm_with_tools.stream(messages):
        acc = chunk if acc is None else acc + chunk
        if stream_stdout and chunk.content:
            print(chunk.content, end="", flush=True)
    if acc is None:
        raise RuntimeError("model returned no chunks")
    response = message_chunk_to_message(acc)
    if not isinstance(response, AIMessage):
        return AIMessage(content=str(response.content))
    return response


def run_react_turn(
    llm_with_tools: Any,
    system_message: SystemMessage,
    past: list[BaseMessage],
    stored_human_message: HumanMessage,
    model_human_message: HumanMessage,
    *,
    stream_stdout: bool = True,
) -> tuple[str, list[BaseMessage]]:
    model_messages = messages_for_model(system_message, past, model_human_message)
    turn_messages: list[BaseMessage] = [stored_human_message]

    while True:
        response = stream_ai_message(llm_with_tools, model_messages, stream_stdout)
        tool_calls = getattr(response, "tool_calls", None) or []
        if tool_calls:
            if stream_stdout:
                print()
            model_messages.append(response)
            turn_messages.append(response)
            for call in tool_calls:
                name = call.get("name")
                call_id = call.get("id") or name or "tool-call"
                tool_obj, args, error = prepare_tool_call(str(name), call.get("args"))
                if error or tool_obj is None:
                    result = f"Error: {error}"
                else:
                    try:
                        result = tool_obj.invoke(args)
                    except Exception as exc:
                        result = f"Error: {exc}"
                tool_message = ToolMessage(content=str(result), tool_call_id=str(call_id), name=str(name))
                model_messages.append(tool_message)
                turn_messages.append(tool_message)
            continue
        model_messages.append(response)
        turn_messages.append(response)
        final_text = str(response.content or "").strip()
        return final_text, turn_messages


def main() -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("BASE_URL") or None
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    session_path = os.getenv("SESSION_JSONL_PATH", "session.jsonl")

    if not api_key:
        print("找不到 OPENAI_API_KEY，請先在 .env 設定後再執行。")
        return

    loader = SkillsLoader(WORKSPACE, WORKSPACE / "builtin_skills")
    history, session_meta = load_session_jsonl(session_path)
    llm = ChatOpenAI(api_key=api_key, base_url=base_url, model=model_name, temperature=0.2)
    llm_with_tools = llm.bind_tools(TOOLS)

    print("法鬥超人已啟動。輸入 exit / quit / q 結束；輸入 clear 可清空本次 JSONL 歷史。")
    print("附圖格式：/image 相對路徑 你的問題")

    while True:
        raw = input("\n你：").strip()
        if not raw:
            continue
        if raw.lower() in ("exit", "quit", "q"):
            print("法鬥超人：下次見。")
            break
        if raw.lower() == "clear":
            history = []
            session_meta = default_metadata()
            save_session_jsonl(session_path, history, session_meta)
            print("法鬥超人：已清空對話紀錄。")
            continue

        user_text, image_rel, media_type = parse_user_input(raw)
        if not user_text:
            continue

        system_text = build_system_prompt(loader)
        system_message = SystemMessage(content=system_text)
        model_human = build_human_message_for_current_turn(user_text, image_rel, media_type)
        stored_human = persistent_human_message(user_text, image_rel, media_type)
        past, session_meta = ensure_budget_and_maybe_consolidate(llm, system_text, history, model_human, session_meta)

        print("法鬥超人：", end="", flush=True)
        try:
            _reply, turn_messages = run_react_turn(
                llm_with_tools,
                system_message,
                past,
                stored_human,
                model_human,
            )
            print()
        except Exception as exc:
            print(f"\n發生錯誤：{exc}")
            continue

        history.extend(turn_messages)
        session_meta = save_session_jsonl(session_path, history, session_meta)


if __name__ == "__main__":
    main()
