from __future__ import annotations

import hashlib
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHELL_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import (
    format_extra_context,
    inject_style,
    load_page_data,
    save_page_data,
    shared_data_path,
)

PAGE_NAME = "人生故事書"
OUTPUT_DIR = Path("story_outputs")
STORIES_DIR_NAME = "life_stories"

st.set_page_config(page_title="人生故事書", page_icon="📖", layout="wide")
inject_style()


PARENT_STORY_HINT = """
### 採訪流程提示

用「採訪式引導」幫您把一段人生故事整理成可以留給孩子的文字。

**左欄三個區塊**

- **故事主線**：一句話寫下最想留下的那段故事。
- **訪談進度筆記**：AI 每輪會自動 append 進度；您也可以手動補充關鍵字或場景。
- **已蒐集事實**：每行一筆 `key：value`（例如 `主角：媽媽`），AI 會自動 merge；您也可以手動編輯。

**右欄採訪流程**

1. 先確認主線：最想留下的那段故事。
2. 沿主線依序追問：背景 → 開端 → 衝突 → 決定 → 結果 → 意義 → 留給孩子的話。
3. 回答太短時，AI 會溫和補問細節；太抽象時，會拉回具體事件。
4. 資訊足夠後，跟 Agent 說「可以整理成故事了」，會產出 `.md` 檔到 `story_outputs/`。

**AI 自動紀錄格式**

Agent 每輪回應結尾會輸出兩個區塊，系統會自動寫進左欄：

- `【NOTES】...【/NOTES】` → append 到「訪談進度筆記」
- `【FACTS】...【/FACTS】` → merge 到「已蒐集事實」

**按鈕與功能**

- **選擇故事（下拉選單）**：切換到列表中的其他故事；切換後左欄三個區塊會自動載入該故事的內容。
- **➕ 新故事**：建立一個全新的空白故事，並自動切換為目前編輯對象。
- **💾 存為快照**：把目前故事「凍結」複製一份（標題加「（快照）」、狀態設為已完成），原故事不動，可繼續編輯。
- **✅ 標記完成 / ↩️ 標記進行中**：切換目前故事的狀態（採訪中 ↔ 已完成），內容不變。
- **🗑️ 刪除**：刪除目前故事（連同狀態檔）；刪除後會自動切到第一個剩下的故事。
- **故事標題**：可隨時改名；改完會自動同步到索引檔。
- **故事主線**：一句話寫下最想留下的那段故事。
- **訪談進度筆記**：AI 每輪會自動 append 進度；您也可以手動補充關鍵字或場景。
- **已蒐集事實**：每行一筆 `key：value`（例如 `主角：媽媽`），AI 會自動 merge；您也可以手動編輯。
- **訪談時間軸**：顯示最近 10 輪的對話摘要（時間、使用者訊息、筆記、事實）。
- **📄 匯出 Word / 📕 匯出 PDF**：把目前故事匯出成 `.docx` 或 `.pdf`，存到 `story_outputs/`。
- **⬇️ 下載 Word / ⬇️ 下載 PDF**：把剛匯出的檔案下載到本機。
- **給 Agent 的摘要**：把目前故事的狀態打包成一段文字，貼給 Agent 讓它接續採訪。

**狀態檔位置**

- 索引檔：`studio_shell/data/人生故事書.json`（故事列表 + 目前選擇）
- 每個故事：`studio_shell/data/life_stories/story_<id>.json`
""".strip()


# Agent 回應裡的結構化標記區塊（用正則解析）
NOTES_RE = re.compile(r"【NOTES】(.*?)【/NOTES】", re.DOTALL)
FACTS_RE = re.compile(r"【FACTS】(.*?)【/FACTS】", re.DOTALL)


# ─────────────────────────────────────────────────────────────
# 匯出：Word / PDF
# ─────────────────────────────────────────────────────────────

def _safe_filename(title: str) -> str:
    """把故事標題轉成檔名安全字串。"""
    name = re.sub(r"[\\/:*?\"<>|]", "_", title or "未命名故事")
    name = name.strip().strip(".")
    return name or "未命名故事"


def _build_story_sections(story: dict) -> list[tuple[str, str]]:
    """把故事切成 (heading, body) 段落，給 docx/pdf 共用。"""
    sections: list[tuple[str, str]] = []

    title = story.get("title") or "未命名故事"
    sections.append(("標題", title))

    seed = story.get("story_seed", "")
    if seed:
        sections.append(("故事主線", seed))

    facts = story.get("collected_facts", {})
    if isinstance(facts, dict) and facts:
        lines = [f"{k}：{v}" for k, v in facts.items()]
        sections.append(("已蒐集事實", "\n".join(lines)))

    notes = story.get("progress_notes", "")
    if notes:
        sections.append(("訪談進度筆記", notes))

    timeline = story.get("timeline", [])
    if isinstance(timeline, list) and timeline:
        lines = []
        for entry in timeline:
            ts = entry.get("ts", "")
            user = entry.get("user", "")
            notes_added = entry.get("notes_added", "")
            facts_added = entry.get("facts_added", [])
            line = f"[{ts}] 使用者：{user}"
            if notes_added:
                line += f"\n　→ 筆記：{notes_added}"
            if facts_added:
                line += f"\n　→ 事實：{', '.join(facts_added)}"
            lines.append(line)
        sections.append(("訪談時間軸", "\n\n".join(lines)))

    return sections


def _export_to_docx(story: dict, output_path: Path) -> None:
    """把故事匯出成 .docx。"""
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # 標題
    title_para = doc.add_heading(story.get("title") or "未命名故事", level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 中繼資訊
    meta = doc.add_paragraph()
    meta_run = meta.add_run(
        f"建立：{story.get('created_at', '')}　·　"
        f"更新：{story.get('updated_at', '')}　·　"
        f"狀態：{'已完成' if story.get('status') == 'completed' else '採訪中'}"
    )
    meta_run.font.size = Pt(9)

    doc.add_paragraph()  # 空行

    for heading, body in _build_story_sections(story):
        if heading == "標題":
            continue  # 已加過
        doc.add_heading(heading, level=1)
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            doc.add_paragraph(line)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


def _export_to_pdf(story: dict, output_path: Path) -> None:
    """把故事匯出成 .pdf（支援中文：使用 reportlab + CID 字型）。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    # 註冊繁體中文 CID 字型（reportlab 內建，不需要外部 ttf）
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=story.get("title") or "未命名故事",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCN",
        parent=styles["Title"],
        fontName="STSong-Light",
        fontSize=22,
        leading=28,
        alignment=1,  # CENTER
        spaceAfter=12,
    )
    h1_style = ParagraphStyle(
        "H1CN",
        parent=styles["Heading1"],
        fontName="STSong-Light",
        fontSize=16,
        leading=22,
        spaceBefore=14,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyCN",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=11,
        leading=18,
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "MetaCN",
        parent=styles["BodyText"],
        fontName="STSong-Light",
        fontSize=9,
        leading=14,
        alignment=1,
        textColor="#666666",
        spaceAfter=12,
    )

    story_flow = []

    title = story.get("title") or "未命名故事"
    story_flow.append(Paragraph(_escape_xml(title), title_style))

    meta_text = (
        f"建立：{story.get('created_at', '')}　·　"
        f"更新：{story.get('updated_at', '')}　·　"
        f"狀態：{'已完成' if story.get('status') == 'completed' else '採訪中'}"
    )
    story_flow.append(Paragraph(_escape_xml(meta_text), meta_style))
    story_flow.append(Spacer(1, 0.5 * cm))

    for heading, body in _build_story_sections(story):
        if heading == "標題":
            continue
        story_flow.append(Paragraph(_escape_xml(heading), h1_style))
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            # 把換行轉成 <br/>
            line_xml = _escape_xml(line).replace("\n", "<br/>")
            story_flow.append(Paragraph(line_xml, body_style))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story_flow)


def _escape_xml(text: str) -> str:
    """Escape XML special chars for reportlab Paragraph."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ─────────────────────────────────────────────────────────────
# 資料層：故事索引 + 每個故事一份檔
# ─────────────────────────────────────────────────────────────

def _stories_dir(shell_root: Path) -> Path:
    return shell_root / "data" / STORIES_DIR_NAME


def _new_story_id() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:6]
    return f"story_{stamp}_{short}"


def _story_path(story_id: str, shell_root: Path) -> Path:
    return _stories_dir(shell_root) / f"{story_id}.json"


def _load_index(shell_root: Path) -> dict:
    """讀取索引檔，自動 migrate 舊格式。"""
    index_path = shared_data_path(PAGE_NAME, shell_root=shell_root)
    if not index_path.is_file():
        return {"current_story_id": "", "stories": []}

    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"current_story_id": "", "stories": []}

    if not isinstance(raw, dict):
        return {"current_story_id": "", "stories": []}

    # 已是新格式
    if "stories" in raw and isinstance(raw["stories"], list):
        return raw

    # 舊格式 migrate：把現有資料包成一個 story
    legacy_id = f"story_legacy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    legacy_story = {
        "id": legacy_id,
        "title": str(raw.get("story_seed", "") or "未命名故事")[:50] or "未命名故事",
        "story_seed": str(raw.get("story_seed", "") or ""),
        "progress_notes": str(raw.get("progress_notes", "") or ""),
        "collected_facts": raw.get("collected_facts", {}) if isinstance(raw.get("collected_facts"), dict) else {},
        "timeline": raw.get("timeline", []) if isinstance(raw.get("timeline"), list) else [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "in_progress",
        "migrated_from_legacy": True,
    }
    _stories_dir(shell_root).mkdir(parents=True, exist_ok=True)
    _story_path(legacy_id, shell_root).write_text(
        json.dumps(legacy_story, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    new_index = {
        "current_story_id": legacy_id,
        "stories": [{
            "id": legacy_id,
            "title": legacy_story["title"],
            "created_at": legacy_story["created_at"],
            "updated_at": legacy_story["updated_at"],
            "status": "in_progress",
        }],
    }
    index_path.write_text(
        json.dumps(new_index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return new_index


def _save_index(index: dict, shell_root: Path) -> None:
    index_path = shared_data_path(PAGE_NAME, shell_root=shell_root)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_story(story_id: str, shell_root: Path) -> dict | None:
    path = _story_path(story_id, shell_root)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _save_story(story: dict, shell_root: Path) -> None:
    story["updated_at"] = datetime.now().isoformat(timespec="seconds")
    _stories_dir(shell_root).mkdir(parents=True, exist_ok=True)
    _story_path(story["id"], shell_root).write_text(
        json.dumps(story, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _create_story(title: str, shell_root: Path) -> dict:
    now = datetime.now().isoformat(timespec="seconds")
    story = {
        "id": _new_story_id(),
        "title": title or "未命名故事",
        "story_seed": "",
        "progress_notes": "",
        "collected_facts": {},
        "timeline": [],
        "created_at": now,
        "updated_at": now,
        "status": "in_progress",
    }
    _save_story(story, shell_root)
    return story


def _delete_story(story_id: str, shell_root: Path) -> None:
    path = _story_path(story_id, shell_root)
    if path.is_file():
        path.unlink()


# ─────────────────────────────────────────────────────────────
# 解析 Agent 回應
# ─────────────────────────────────────────────────────────────

def _parse_facts_block(block: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or "：" not in line:
            continue
        key, value = line.split("：", 1)
        key = key.strip()
        value = value.strip()
        if key:
            facts[key] = value
    return facts


def _on_agent_reply(answer: str, user_text: str) -> None:
    """Agent 回應後自動更新「目前選擇的故事」。"""
    sig = hashlib.md5(answer.encode("utf-8")).hexdigest()
    if st.session_state.get("_life_story_last_sig") == sig:
        return
    st.session_state["_life_story_last_sig"] = sig

    notes_match = NOTES_RE.search(answer)
    facts_match = FACTS_RE.search(answer)
    new_notes = notes_match.group(1).strip() if notes_match else ""
    new_facts = _parse_facts_block(facts_match.group(1)) if facts_match else {}

    if not new_notes and not new_facts:
        return

    index = _load_index(SHELL_ROOT)
    story_id = index.get("current_story_id", "")
    if not story_id:
        return

    story = _load_story(story_id, SHELL_ROOT)
    if story is None:
        return

    existing_notes = str(story.get("progress_notes", "") or "")
    if new_notes:
        merged_notes = (existing_notes + "\n\n" + new_notes).strip() if existing_notes else new_notes
    else:
        merged_notes = existing_notes

    existing_facts = story.get("collected_facts", {})
    if not isinstance(existing_facts, dict):
        existing_facts = {}
    merged_facts = {**existing_facts, **new_facts}

    timeline = story.get("timeline", [])
    if not isinstance(timeline, list):
        timeline = []
    timeline.append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "user": user_text[:200],
        "agent_excerpt": answer[:200],
        "notes_added": new_notes[:200],
        "facts_added": list(new_facts.keys()),
    })

    story["progress_notes"] = merged_notes
    story["collected_facts"] = merged_facts
    story["timeline"] = timeline
    _save_story(story, SHELL_ROOT)

    # 同步更新索引裡的 updated_at
    for entry in index.get("stories", []):
        if entry.get("id") == story_id:
            entry["updated_at"] = story["updated_at"]
            break
    _save_index(index, SHELL_ROOT)


# ─────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────

def _facts_to_text(facts: dict[str, str]) -> str:
    return "\n".join(f"{k}：{v}" for k, v in facts.items())


def _text_to_facts(text: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or "：" not in line:
            continue
        key, value = line.split("：", 1)
        key = key.strip()
        value = value.strip()
        if key:
            facts[key] = value
    return facts


def _story_label(entry: dict) -> str:
    title = entry.get("title", "未命名")
    status = entry.get("status", "in_progress")
    updated = entry.get("updated_at", "")[:16].replace("T", " ")
    status_icon = "✅" if status == "completed" else "📝"
    return f"{status_icon} {title}（{updated}）"


# ─────────────────────────────────────────────────────────────
# 主畫面
# ─────────────────────────────────────────────────────────────

def render_main() -> str:
    index = _load_index(SHELL_ROOT)
    stories = index.get("stories", [])
    current_id = index.get("current_story_id", "")

    # 確保 current_id 有效
    if current_id and not _load_story(current_id, SHELL_ROOT):
        current_id = ""
        index["current_story_id"] = ""
    if not current_id and stories:
        current_id = stories[0]["id"]
        index["current_story_id"] = current_id
        _save_index(index, SHELL_ROOT)

    # ── 故事管理區塊 ──
    st.markdown("#### 📚 故事管理")

    if not stories:
        st.info("還沒有故事。點下方「➕ 新故事」開始第一段。")
        col_new, _ = st.columns([1, 5])
        if col_new.button("➕ 新故事", type="primary", use_container_width=True):
            new_title = f"故事 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
            story = _create_story(new_title, SHELL_ROOT)
            index["stories"].append({
                "id": story["id"],
                "title": story["title"],
                "created_at": story["created_at"],
                "updated_at": story["updated_at"],
                "status": "in_progress",
            })
            index["current_story_id"] = story["id"]
            _save_index(index, SHELL_ROOT)
            st.rerun()
        return ""

    # 選擇器
    story_labels = {entry["id"]: _story_label(entry) for entry in stories}
    selected_id = st.selectbox(
        "選擇故事",
        options=list(story_labels.keys()),
        index=list(story_labels.keys()).index(current_id) if current_id in story_labels else 0,
        format_func=lambda sid: story_labels.get(sid, sid),
        key="life_story_picker",
    )

    # 切換故事
    if selected_id != current_id:
        index["current_story_id"] = selected_id
        _save_index(index, SHELL_ROOT)
        st.rerun()

    # 操作按鈕
    current_story = _load_story(current_id, SHELL_ROOT) or {}
    is_completed = current_story.get("status") == "completed"

    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    new_clicked = btn_col1.button("➕ 新故事", use_container_width=True)
    snapshot_clicked = btn_col2.button("💾 存為快照", use_container_width=True)
    complete_label = "↩️ 標記進行中" if is_completed else "✅ 標記完成"
    complete_clicked = btn_col3.button(complete_label, use_container_width=True)
    delete_clicked = btn_col4.button("🗑️ 刪除", type="secondary", use_container_width=True)

    if new_clicked:
        new_title = f"故事 {datetime.now().strftime('%Y/%m/%d %H:%M')}"
        story = _create_story(new_title, SHELL_ROOT)
        index["stories"].append({
            "id": story["id"],
            "title": story["title"],
            "created_at": story["created_at"],
            "updated_at": story["updated_at"],
            "status": "in_progress",
        })
        index["current_story_id"] = story["id"]
        _save_index(index, SHELL_ROOT)
        st.rerun()

    if snapshot_clicked and current_id:
        story = _load_story(current_id, SHELL_ROOT)
        if story:
            snapshot_id = f"{current_id}_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            snapshot = dict(story)
            snapshot["id"] = snapshot_id
            snapshot["title"] = f"{story.get('title', '')}（快照）"
            snapshot["status"] = "completed"
            _save_story(snapshot, SHELL_ROOT)
            index["stories"].append({
                "id": snapshot_id,
                "title": snapshot["title"],
                "created_at": snapshot["created_at"],
                "updated_at": snapshot["updated_at"],
                "status": "completed",
            })
            _save_index(index, SHELL_ROOT)
            st.success(f"已存快照：{snapshot['title']}")

    if complete_clicked and current_id:
        story = _load_story(current_id, SHELL_ROOT)
        if story:
            new_status = "in_progress" if story.get("status") == "completed" else "completed"
            story["status"] = new_status
            _save_story(story, SHELL_ROOT)
            for entry in index["stories"]:
                if entry["id"] == current_id:
                    entry["status"] = new_status
                    break
            _save_index(index, SHELL_ROOT)
            st.rerun()

    if delete_clicked and current_id:
        _delete_story(current_id, SHELL_ROOT)
        index["stories"] = [e for e in index["stories"] if e["id"] != current_id]
        if index["stories"]:
            index["current_story_id"] = index["stories"][0]["id"]
        else:
            index["current_story_id"] = ""
        _save_index(index, SHELL_ROOT)
        st.rerun()

    # ── 載入目前故事 ──
    story = current_story

    # ── 採訪流程提示（折疊） ──
    with st.expander("📖 採訪流程與使用說明", expanded=False):
        st.markdown(PARENT_STORY_HINT)

    # ── 故事標題（可改） ──
    new_title = st.text_input(
        "故事標題",
        value=story.get("title", ""),
        placeholder="例如：媽媽北上工作",
        key="life_story_title",
    )
    if new_title != story.get("title", ""):
        story["title"] = new_title
        for entry in index["stories"]:
            if entry["id"] == current_id:
                entry["title"] = new_title
                break
        _save_story(story, SHELL_ROOT)
        _save_index(index, SHELL_ROOT)

    # ── 故事主線 ──
    st.markdown("#### 故事主線")
    story_seed = st.text_input(
        "如果今天只能先留下一段故事，您最想從哪一件事開始說起？",
        value=story.get("story_seed", ""),
        placeholder="例如：我媽年輕時一個人北上工作的那段日子",
        key="life_story_seed",
    )

    # ── 訪談進度筆記 ──
    st.markdown("#### 訪談進度筆記")
    st.caption("AI 會自動 append 進度；您也可以直接編輯補充。")
    progress_notes = st.text_area(
        "目前聊到什麼階段？有什麼想先記下來的關鍵字或場景？",
        value=story.get("progress_notes", ""),
        placeholder="例如：已確認主線、剛問完背景、接下來要問最大衝突",
        height=160,
        key="life_story_notes",
    )

    # ── 已蒐集事實 ──
    st.markdown("#### 已蒐集事實")
    st.caption("每行一筆「key：value」，AI 會自動 merge；您也可以手動編輯。")
    existing_facts = story.get("collected_facts", {})
    if not isinstance(existing_facts, dict):
        existing_facts = {}
    facts_text = st.text_area(
        "事實清單",
        value=_facts_to_text(existing_facts),
        placeholder="例如：\n主角：媽媽\n年代：1970 年代\n地點：台北",
        height=160,
        key="life_story_facts_editor",
    )
    edited_facts = _text_to_facts(facts_text)

    # ── 訪談時間軸 ──
    timeline = story.get("timeline", [])
    if not isinstance(timeline, list):
        timeline = []
    with st.expander(f"訪談時間軸（{len(timeline)} 輪，顯示最近 10 輪）", expanded=False):
        if not timeline:
            st.caption("（尚無紀錄）")
        for entry in timeline[-10:]:
            ts = entry.get("ts", "")
            user = entry.get("user", "")
            notes = entry.get("notes_added", "")
            facts_added = entry.get("facts_added", [])
            st.markdown(f"**[{ts}]** 使用者：{user}")
            if notes:
                st.markdown(f"　→ 筆記：{notes}")
            if facts_added:
                st.markdown(f"　→ 事實：{', '.join(facts_added)}")

    # ── 存檔 ──
    story["story_seed"] = story_seed
    story["progress_notes"] = progress_notes
    story["collected_facts"] = edited_facts
    story["timeline"] = timeline
    _save_story(story, SHELL_ROOT)

    # 同步索引 updated_at
    for entry in index["stories"]:
        if entry["id"] == current_id:
            entry["updated_at"] = story["updated_at"]
            break
    _save_index(index, SHELL_ROOT)

    # ── 匯出文件 ──
    st.markdown("#### 📤 匯出文件")
    st.caption("把目前故事匯出成 Word 或 PDF，存到 `story_outputs/` 並提供下載。")

    export_dir = PROJECT_ROOT / OUTPUT_DIR
    safe_title = _safe_filename(story.get("title", "未命名故事"))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_filename = f"{safe_title}_{stamp}.docx"
    pdf_filename = f"{safe_title}_{stamp}.pdf"
    docx_path = export_dir / docx_filename
    pdf_path = export_dir / pdf_filename

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        if st.button("📄 匯出 Word（.docx）", use_container_width=True):
            try:
                _export_to_docx(story, docx_path)
                st.session_state["_life_story_last_docx"] = str(docx_path)
                st.success(f"已匯出：{docx_filename}")
            except Exception as exc:
                st.error(f"Word 匯出失敗：`{exc}`")

    with exp_col2:
        if st.button("📕 匯出 PDF（.pdf）", use_container_width=True):
            try:
                _export_to_pdf(story, pdf_path)
                st.session_state["_life_story_last_pdf"] = str(pdf_path)
                st.success(f"已匯出：{pdf_filename}")
            except Exception as exc:
                st.error(f"PDF 匯出失敗：`{exc}`")

    # 下載按鈕（檔案存在才顯示）
    dl_col1, dl_col2 = st.columns(2)
    if docx_path.is_file():
        with dl_col1:
            st.download_button(
                "⬇️ 下載 Word",
                data=docx_path.read_bytes(),
                file_name=docx_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
    if pdf_path.is_file():
        with dl_col2:
            st.download_button(
                "⬇️ 下載 PDF",
                data=pdf_path.read_bytes(),
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True,
            )

    st.divider()

    # ── 給 Agent 的摘要 ──
    st.markdown("#### 給 Agent 的摘要")
    extra = format_extra_context(
        PAGE_NAME,
        共享資料檔=str(shared_data_path(PAGE_NAME, shell_root=SHELL_ROOT)),
        目前故事=story.get("title", "未命名"),
        故事主線=story_seed or "（尚未設定）",
        訪談進度筆記=progress_notes or "（空白）",
        已蒐集事實=_facts_to_text(edited_facts) or "（尚無）",
        訪談輪數=str(len(timeline)),
        故事輸出目錄=str(OUTPUT_DIR),
        輸出檔名慣例="{timestamp}_{故事標題}.md",
        採訪流程="請嚴格遵循 parent-story skill：先確認主線 → 背景 → 開端 → 衝突 → 決定 → 結果 → 意義 → 留給孩子的話；每次只問一題，優先補充細節。",
        自動紀錄規則="每輪回應結尾請輸出一個【NOTES】區塊（簡述本輪進度與關鍵字）與一個【FACTS】區塊（每行 key：value，列出本輪新蒐集到的事實），系統會自動 append 到目前故事的狀態檔。資訊足夠後再整理輸出 story_outputs/ 的 .md 檔案。",
    )
    st.code(extra, language="text")

    return extra


page_shell(
    "人生故事書",
    "留下最想說給孩子聽的一段人生故事。",
    render_main,
    page_name=PAGE_NAME,
    on_assistant_reply=_on_agent_reply,
)