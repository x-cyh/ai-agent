from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from studio_shell.agent_panel import render_chat_panel


def page_shell(
    title: str,
    caption: str,
    render_main: Callable[[], str | None],
    *,
    page_name: str = "",
    on_assistant_reply: Callable[[str, str], None] | None = None,
) -> None:
    """Left column UI + right column Agent. render_main returns extra_context for Agent.

    on_assistant_reply(answer, user_text) is called after each assistant reply
    finishes streaming, before st.rerun(). Use it to parse structured markers
    (e.g. 【NOTES】/【FACTS】) and update page state.
    """

    main, side = st.columns([5, 3], gap="large")

    with main:
        st.title(title)
        st.caption(caption)
        extra_context = render_main() or ""

    with side:
        render_chat_panel(
            extra_context=extra_context,
            page_name=page_name or title,
            on_assistant_reply=on_assistant_reply,
        )
