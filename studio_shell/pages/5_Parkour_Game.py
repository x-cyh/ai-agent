from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from studio_shell.page_shell import page_shell
from studio_shell.shell_ui import format_extra_context, inject_style


st.set_page_config(page_title="跑酷遊戲", page_icon="🏃", layout="wide")
inject_style()


def _render_keyboard_game() -> None:
    components.html(
        """
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<style>
    :root {
        color-scheme: dark;
        font-family: "Segoe UI", "Microsoft JhengHei", system-ui, sans-serif;
    }

    body {
        margin: 0;
        background: transparent;
        color: #f8fafc;
    }

    .game-shell {
        display: grid;
        gap: 12px;
    }

    .status-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
    }

    .status-box,
    .control-panel {
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 8px;
        background: rgba(2, 6, 23, 0.42);
        backdrop-filter: blur(6px);
    }

    .status-box {
        min-height: 54px;
        padding: 8px 12px;
    }

    .status-label {
        color: rgba(248, 250, 252, 0.7);
        font-size: 12px;
        line-height: 1.2;
    }

    .status-value {
        margin-top: 3px;
        font-size: 21px;
        font-weight: 800;
        line-height: 1.1;
    }

    .game {
        position: relative;
        height: 430px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 8px;
        outline: none;
        background:
            radial-gradient(circle at 12% 18%, rgba(255, 218, 112, 0.34), transparent 17%),
            linear-gradient(180deg, #24486f 0%, #306d6b 48%, #23262b 49%, #111316 100%);
    }

    .game:focus {
        box-shadow: inset 0 0 0 2px rgba(125, 211, 252, 0.55);
    }

    .skyline {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 138px;
        height: 96px;
        opacity: 0.86;
        background:
            linear-gradient(90deg,
                transparent 0 5%, rgba(14, 20, 31, 0.62) 5% 13%, transparent 13% 19%,
                rgba(14, 20, 31, 0.78) 19% 31%, transparent 31% 39%,
                rgba(14, 20, 31, 0.68) 39% 48%, transparent 48% 55%,
                rgba(14, 20, 31, 0.84) 55% 70%, transparent 70% 79%,
                rgba(14, 20, 31, 0.72) 79% 89%, transparent 89% 100%);
    }

    .road {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 138px;
        background:
            repeating-linear-gradient(90deg, rgba(255,255,255,0.8) 0 54px, transparent 54px 118px),
            linear-gradient(180deg, #2f343a, #17191d);
        background-size: 172px 6px, auto;
        background-position: 0 59px, 0 0;
    }

    .game.running .road {
        animation: road-slide 0.9s linear infinite;
    }

    .runner {
        position: absolute;
        left: 13%;
        bottom: 104px;
        z-index: 4;
        width: 82px;
        height: 82px;
        font-size: 68px;
        line-height: 82px;
        text-align: center;
        transform: scaleX(-1);
        transform-origin: center;
        filter: drop-shadow(0 14px 10px rgba(0, 0, 0, 0.34));
    }

    .game.running .runner:not(.jump):not(.dash) {
        animation: run-bob 0.48s ease-in-out infinite;
    }

    .game.running .runner.jump {
        animation: jump 0.54s ease-out;
    }

    .game.running .runner.dash {
        animation: dash 0.26s ease-out;
    }

    .runner.stop {
        animation: none;
        opacity: 0.58;
        transform: scaleX(-1) rotate(-10deg);
    }

    .obstacle {
        position: absolute;
        right: -90px;
        bottom: 106px;
        z-index: 3;
        width: 82px;
        height: 82px;
        font-size: 62px;
        line-height: 82px;
        text-align: center;
    }

    .control-panel {
        display: grid;
        grid-template-columns: 1.2fr 1fr;
        gap: 12px;
        align-items: center;
        padding: 10px 12px;
    }

    .message {
        color: #f8fafc;
        font-weight: 800;
    }

    .keys {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
        color: rgba(248, 250, 252, 0.82);
        font-size: 13px;
        line-height: 1.4;
    }

    kbd {
        display: inline-block;
        min-width: 28px;
        padding: 3px 7px;
        border: 1px solid rgba(255, 255, 255, 0.24);
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.1);
        color: #f8fafc;
        font-family: inherit;
        font-weight: 800;
        text-align: center;
    }

    .flash {
        position: absolute;
        inset: 0;
        z-index: 2;
        pointer-events: none;
        opacity: 0;
        background: rgba(248, 113, 113, 0.22);
    }

    .flash.hit {
        animation: hit-flash 0.25s ease-out;
    }

    @keyframes road-slide {
        from { background-position: 0 59px, 0 0; }
        to { background-position: -172px 59px, 0 0; }
    }

    @keyframes run-bob {
        0%, 100% { transform: scaleX(-1) translateY(0) rotate(-2deg); }
        50% { transform: scaleX(-1) translateY(-12px) rotate(4deg); }
    }

    @keyframes jump {
        0% { transform: scaleX(-1) translateY(0); }
        50% { transform: scaleX(-1) translateY(-92px) rotate(8deg); }
        100% { transform: scaleX(-1) translateY(0); }
    }

    @keyframes dash {
        0% { transform: scaleX(-1) translateX(0); }
        50% { transform: scaleX(-1) translateX(58px) rotate(-8deg); }
        100% { transform: scaleX(-1) translateX(0); }
    }

    @keyframes hit-flash {
        0% { opacity: 0; }
        35% { opacity: 1; }
        100% { opacity: 0; }
    }

    @media (max-width: 640px) {
        .game { height: 380px; }
        .status-strip,
        .control-panel { grid-template-columns: 1fr; }
        .status-box { min-height: 42px; }
        .status-value { font-size: 18px; }
        .keys { justify-content: flex-start; }
        .runner { left: 8%; }
    }
</style>
</head>
<body>
<div class="game-shell">
    <section class="status-strip" aria-live="polite">
        <div class="status-box">
            <div class="status-label">分數</div>
            <div class="status-value" id="score">0</div>
        </div>
        <div class="status-box">
            <div class="status-label">生命</div>
            <div class="status-value" id="lives">3</div>
        </div>
        <div class="status-box">
            <div class="status-label">障礙</div>
            <div class="status-value" id="obstacleName">矮牆</div>
        </div>
    </section>
    <main class="game" id="game" tabindex="0" aria-label="跑酷遊戲">
        <div class="skyline"></div>
        <div class="road"></div>
        <div class="runner" id="runner">🥷</div>
        <div class="obstacle" id="obstacle">🧱</div>
        <div class="flash" id="flash"></div>
    </main>
    <section class="control-panel">
        <div class="message" id="message">準備起跑！按下跳躍或衝刺開始。</div>
        <div class="keys" aria-label="控制方法">
            <span><kbd>Space</kbd> <kbd>↑</kbd> <kbd>W</kbd> 跳躍</span>
            <span><kbd>→</kbd> <kbd>D</kbd> 衝刺</span>
            <span><kbd>Enter</kbd> <kbd>R</kbd> 重來</span>
        </div>
    </section>
</div>

<script>
const game = document.getElementById("game");
const runner = document.getElementById("runner");
const obstacleEl = document.getElementById("obstacle");
const obstacleNameEl = document.getElementById("obstacleName");
const scoreEl = document.getElementById("score");
const livesEl = document.getElementById("lives");
const messageEl = document.getElementById("message");
const flash = document.getElementById("flash");

const obstacles = [
    { name: "矮牆", icon: "🧱", action: "jump" },
    { name: "水坑", icon: "💧", action: "jump" },
    { name: "路障", icon: "🚧", action: "dash" },
    { name: "斷橋", icon: "🌉", action: "dash" },
];

let score = 0;
let lives = 3;
let current = obstacles[0];
let obstacleX = game.clientWidth + 40;
let speed = 4.6;
let lastTime = performance.now();
let locked = false;
let gameOver = false;
let started = false;

function chooseObstacle() {
    current = obstacles[Math.floor(Math.random() * obstacles.length)];
    obstacleEl.textContent = current.icon;
    obstacleNameEl.textContent = current.name;
    obstacleX = game.clientWidth + 50;
    obstacleEl.style.transform = `translateX(${obstacleX - game.clientWidth}px)`;
}

function setMessage(text) {
    messageEl.textContent = text;
}

function setRunnerAnimation(name) {
    runner.classList.remove("jump", "dash");
    void runner.offsetWidth;
    runner.classList.add(name);
    window.setTimeout(() => runner.classList.remove(name), name === "jump" ? 540 : 260);
}

function resetGame() {
    score = 0;
    lives = 3;
    speed = 4.6;
    gameOver = false;
    started = false;
    game.classList.remove("running");
    runner.classList.remove("stop");
    scoreEl.textContent = score;
    livesEl.textContent = lives;
    chooseObstacle();
    setMessage("準備起跑！按跳躍或衝刺開始。");
}

function startGame() {
    if (started) return;
    started = true;
    game.classList.add("running");
    lastTime = performance.now();
}

function handleAction(action) {
    if (locked) return;
    if (gameOver) {
        resetGame();
        return;
    }

    startGame();
    locked = true;
    window.setTimeout(() => locked = false, 230);
    setRunnerAnimation(action);

    if (current.action === action) {
        score += 10;
        speed = Math.min(8.5, speed + 0.18);
        scoreEl.textContent = score;
        setMessage(`成功通過${current.name}！`);
        chooseObstacle();
        return;
    }

    lives -= 1;
    livesEl.textContent = lives;
    flash.classList.remove("hit");
    void flash.offsetWidth;
    flash.classList.add("hit");

    if (lives <= 0) {
        gameOver = true;
        game.classList.remove("running");
        runner.classList.add("stop");
        setMessage(`遊戲結束，最後分數 ${score}。`);
        return;
    }

    setMessage(`撞上${current.name}，再試一次。`);
    chooseObstacle();
}

function update(time) {
    const delta = Math.min(32, time - lastTime);
    lastTime = time;

    if (started && !gameOver) {
        obstacleX -= speed * (delta / 16.67);
        if (obstacleX < -90) chooseObstacle();
        obstacleEl.style.transform = `translateX(${obstacleX - game.clientWidth}px)`;
    }

    requestAnimationFrame(update);
}

game.addEventListener("keydown", (event) => {
    if (event.code === "Space" || event.code === "ArrowUp" || event.code === "KeyW") {
        event.preventDefault();
        handleAction("jump");
    }
    if (event.code === "ArrowRight" || event.code === "KeyD") {
        event.preventDefault();
        handleAction("dash");
    }
    if (event.code === "Enter" || event.code === "KeyR") {
        event.preventDefault();
        resetGame();
    }
});

game.addEventListener("click", () => game.focus());
window.addEventListener("load", () => game.focus());
resetGame();
requestAnimationFrame(update);
</script>
</body>
</html>
""",
        height=640,
    )


def render_main() -> str:
    st.markdown("#### 街頭跑酷挑戰")
    st.write("閃過障礙，累積分數，撐到最後。")
    st.info("控制方法：Space / ↑ / W = 跳躍，→ / D = 衝刺，Enter / R = 重新開始。")
    _render_keyboard_game()

    extra = format_extra_context(
        "跑酷遊戲",
        控制方式="鍵盤控制",
        視覺狀態="人物面向前進方向，障礙物迎面移動",
    )
    return extra


page_shell(
    "跑酷遊戲",
    "街頭跑酷挑戰。",
    render_main,
    page_name="跑酷遊戲",
)
