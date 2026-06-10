from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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

PAGE_NAME = "Runner"
CHARACTER_OPTIONS = ["忍者", "機器人", "貓咪"]
DIFFICULTY_OPTIONS = ["簡單", "普通", "困難"]
CHARACTER_EMOJI = {
    "忍者": "🥷",
    "機器人": "🤖",
    "貓咪": "🐱",
}
CHARACTER_COLOR = {
    "忍者": "#22c55e",
    "機器人": "#38bdf8",
    "貓咪": "#f59e0b",
}

st.set_page_config(page_title="跑酷遊戲", page_icon="🏃", layout="wide")
inject_style()


def _render_runner_game(character: str, difficulty: str, player_name: str, target_score: int, special_move: str) -> None:
    difficulty_speed = {
        "簡單": 0.9,
        "普通": 1.05,
        "困難": 1.22,
    }.get(difficulty, 1.05)
    avatar = CHARACTER_EMOJI.get(character, "🏃")
    runner_color = CHARACTER_COLOR.get(character, "#22c55e")
    safe_name = (player_name or "玩家").replace("<", "&lt;").replace(">", "&gt;")
    safe_move = (special_move or "自動專注模式").replace("<", "&lt;").replace(">", "&gt;")

    html = f"""
    <!doctype html>
    <html lang="zh-Hant">
    <head>
      <meta charset="utf-8" />
      <style>
        :root {{
          color-scheme: dark;
          font-family: 'Segoe UI', 'Microsoft JhengHei', system-ui, sans-serif;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          background: transparent;
          color: #f8fafc;
        }}
        .shell {{
          display: grid;
          gap: 12px;
        }}
        .topbar {{
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }}
        .card {{
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(15, 23, 42, 0.54);
          border-radius: 10px;
          padding: 10px 12px;
          min-height: 66px;
          backdrop-filter: blur(6px);
        }}
        .label {{
          font-size: 12px;
          color: rgba(248,250,252,0.72);
        }}
        .value {{
          margin-top: 4px;
          font-size: 24px;
          font-weight: 800;
        }}
        .game-meta {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
          padding: 0 2px;
          color: rgba(248,250,252,0.86);
        }}
        .game-meta-left {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          align-items: center;
        }}
        .meta-pill {{
          padding: 7px 12px;
          border-radius: 999px;
          background: rgba(15, 23, 42, 0.64);
          border: 1px solid rgba(255,255,255,0.12);
          font-size: 13px;
          font-weight: 700;
        }}
        .game {{
          position: relative;
          height: 620px;
          overflow: hidden;
          border-radius: 16px;
          border: 1px solid rgba(255,255,255,0.16);
          background: radial-gradient(circle at 50% 12%, rgba(255,255,255,0.14), transparent 18%), linear-gradient(180deg, #0f172a 0%, #1e293b 32%, #020617 100%);
          outline: none;
        }}
        .game:focus {{
          box-shadow: inset 0 0 0 2px rgba(56, 189, 248, 0.72);
        }}
        #scene3d {{
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          display: block;
        }}
        .in-game-panel {{
          position: absolute;
          top: 16px;
          right: 16px;
          z-index: 4;
          min-width: 172px;
          padding: 12px 14px;
          border-radius: 16px;
          text-align: right;
          background: rgba(15, 23, 42, 0.8);
          border: 1px solid rgba(255,255,255,0.14);
          box-shadow: 0 12px 24px rgba(0,0,0,0.22);
          pointer-events: none;
        }}
        .in-game-panel .score-label {{
          font-size: 12px;
          color: rgba(248,250,252,0.72);
        }}
        .in-game-panel .score-value {{
          margin-top: 2px;
          font-size: 28px;
          line-height: 1;
          font-weight: 900;
          letter-spacing: 0.02em;
        }}
        .timer-value {{
          margin-top: 10px;
          font-size: 22px;
          font-weight: 900;
          color: #67e8f9;
        }}
        .reticle {{
          position: absolute;
          inset: auto 50% 130px auto;
          width: 120px;
          height: 12px;
          transform: translateX(50%);
          border-radius: 999px;
          background: radial-gradient(circle at center, rgba(255,255,255,0.75), rgba(255,255,255,0));
          filter: blur(8px);
          pointer-events: none;
          z-index: 2;
        }}
        .overlay {{
          position: absolute;
          inset: 0;
          z-index: 5;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(2, 6, 23, 0.24);
          pointer-events: none;
        }}
        .overlay.hidden {{ display: none; }}
        .overlay-card {{
          min-width: min(92%, 430px);
          text-align: center;
          padding: 24px 22px;
          border-radius: 18px;
          background: rgba(15,23,42,0.92);
          border: 1px solid rgba(255,255,255,0.14);
          box-shadow: 0 24px 50px rgba(0,0,0,0.32);
        }}
        .overlay-card h3 {{ margin: 0 0 8px 0; font-size: 28px; }}
        .overlay-card p {{ margin: 0; color: rgba(248,250,252,0.8); }}
        .message-box {{
          display: grid;
          grid-template-columns: 1.2fr 1fr;
          gap: 12px;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.14);
          background: rgba(15,23,42,0.54);
          padding: 12px 14px;
        }}
        .message {{
          font-weight: 800;
          font-size: 16px;
        }}
        .sub {{
          margin-top: 4px;
          font-size: 13px;
          color: rgba(248,250,252,0.72);
        }}
        .keys {{
          display: flex;
          justify-content: flex-end;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
          color: rgba(248,250,252,0.82);
          font-size: 13px;
        }}
        kbd {{
          display: inline-block;
          min-width: 30px;
          padding: 3px 8px;
          border-radius: 6px;
          border: 1px solid rgba(255,255,255,0.18);
          background: rgba(255,255,255,0.08);
          font-weight: 800;
          text-align: center;
        }}
        @media (max-width: 800px) {{
          .topbar, .message-box {{ grid-template-columns: 1fr 1fr; }}
          .game {{ height: 540px; }}
        }}
        @media (max-width: 560px) {{
          .topbar, .message-box {{ grid-template-columns: 1fr; }}
          .keys {{ justify-content: flex-start; }}
          .game-meta {{ align-items: flex-start; }}
        }}
      </style>
      <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    </head>
    <body>
      <div class="shell">
        <div class="topbar">
          <div class="card"><div class="label">陪跑角色</div><div class="value">{safe_name}</div></div>
          <div class="card"><div class="label">自動跑酷分數</div><div class="value" id="score">0</div></div>
          <div class="card"><div class="label">剩餘時間</div><div class="value" id="timeLeft">25:00</div></div>
          <div class="card"><div class="label">狀態</div><div class="value" id="stateLabel">待命</div></div>
        </div>

        <div class="game-meta">
          <div class="game-meta-left">
            <div class="meta-pill">角色：{character} {avatar}</div>
            <div class="meta-pill">難度：{difficulty}</div>
            <div class="meta-pill">預設目標：{target_score}</div>
          </div>
          <div class="meta-pill">模式：Auto Runner Timer / {safe_move}</div>
        </div>

        <div id="game" class="game" tabindex="0" aria-label="Runner 3D Auto Timer">
          <canvas id="scene3d"></canvas>
          <div class="in-game-panel">
            <div class="score-label">AUTO SCORE</div>
            <div class="score-value" id="cornerScore">0</div>
            <div class="score-label" style="margin-top: 10px;">COUNTDOWN</div>
            <div class="timer-value" id="cornerTimer">25:00</div>
          </div>
          <div class="reticle"></div>
          <div class="overlay" id="overlay">
            <div class="overlay-card">
              <h3>Auto Runner Timer</h3>
              <p>選一個計時長度，再按空白鍵開始。角色會自動高速閃避障礙，作為你的專注陪跑背景。</p>
            </div>
          </div>
        </div>

        <div class="message-box">
          <div>
            <div class="message" id="message">自動跑酷模式已啟動：角色會自行換道、跳躍、滑行與撿金幣，你只要專心計時。</div>
            <div class="sub">操作：按 1 / 5 / 0 / 2 切換 1、5、10、25 分鐘；按 Space 開始或重來。角色技能欄目前作為模式標籤：{safe_move}</div>
          </div>
          <div class="keys">
            <span><kbd>1</kbd> 1 分鐘</span>
            <span><kbd>5</kbd> 5 分鐘</span>
            <span><kbd>0</kbd> 10 分鐘</span>
            <span><kbd>2</kbd> 25 分鐘</span>
            <span><kbd>Space</kbd> 開始 / 重來</span>
          </div>
        </div>
      </div>

      <script>
        const canvas = document.getElementById('scene3d');
        const game = document.getElementById('game');
        const scoreEl = document.getElementById('score');
        const cornerScoreEl = document.getElementById('cornerScore');
        const stateLabel = document.getElementById('stateLabel');
        const timeLeftEl = document.getElementById('timeLeft');
        const cornerTimerEl = document.getElementById('cornerTimer');
        const messageEl = document.getElementById('message');
        const overlay = document.getElementById('overlay');
        const speedFactor = {difficulty_speed};
        const targetScore = {target_score};
        const laneX = [-2.6, 0, 2.6];
        const durationMap = {{
          Digit1: 60,
          Digit5: 300,
          Digit0: 600,
          Digit2: 1500,
        }};

        let state = null;
        let scene, camera, renderer, clock;
        let worldRoot, runnerGroup, floorLines;
        let obstacles = [];
        let decorItems = [];
        let runnerBox = new THREE.Box3();

        function formatTime(totalSeconds) {{
          const clamped = Math.max(0, Math.ceil(totalSeconds));
          const minutes = String(Math.floor(clamped / 60)).padStart(2, '0');
          const seconds = String(clamped % 60).padStart(2, '0');
          return `${{minutes}}:${{seconds}}`;
        }}

        function buildScene() {{
          scene = new THREE.Scene();
          scene.fog = new THREE.Fog(0x020617, 18, 60);

          camera = new THREE.PerspectiveCamera(58, 1, 0.1, 120);
          camera.position.set(0, 5.5, 11.5);
          camera.lookAt(0, 1.5, 0);

          renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, alpha: true }});
          renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
          resizeRenderer();

          clock = new THREE.Clock();
          worldRoot = new THREE.Group();
          scene.add(worldRoot);

          const hemi = new THREE.HemisphereLight(0xa5f3fc, 0x0f172a, 1.6);
          scene.add(hemi);

          const sun = new THREE.DirectionalLight(0xffffff, 1.2);
          sun.position.set(6, 12, 8);
          scene.add(sun);

          const ambient = new THREE.AmbientLight(0x7dd3fc, 0.26);
          scene.add(ambient);

          const skyGeo = new THREE.SphereGeometry(55, 24, 24);
          const skyMat = new THREE.MeshBasicMaterial({{
            color: 0x0f172a,
            side: THREE.BackSide,
          }});
          scene.add(new THREE.Mesh(skyGeo, skyMat));

          createTrack();
          createRunner();
          createDecor();
          resetState();
          animate();
        }}

        function resizeRenderer() {{
          const rect = game.getBoundingClientRect();
          renderer.setSize(rect.width, rect.height, false);
          camera.aspect = rect.width / rect.height;
          camera.updateProjectionMatrix();
        }}

        function createTrack() {{
          const base = new THREE.Mesh(
            new THREE.BoxGeometry(12, 0.4, 120),
            new THREE.MeshStandardMaterial({{ color: 0x111827, metalness: 0.2, roughness: 0.9 }})
          );
          base.position.set(0, -0.22, -36);
          worldRoot.add(base);

          const shoulderGeo = new THREE.BoxGeometry(1.2, 0.16, 120);
          const shoulderMat = new THREE.MeshStandardMaterial({{ color: 0x374151 }});
          [-5.8, 5.8].forEach(x => {{
            const shoulder = new THREE.Mesh(shoulderGeo, shoulderMat);
            shoulder.position.set(x, 0.03, -36);
            worldRoot.add(shoulder);
          }});

          const markerMat = new THREE.MeshStandardMaterial({{ color: 0x94a3b8, emissive: 0x1e293b }});
          [-1.3, 1.3].forEach(x => {{
            const rail = new THREE.Mesh(new THREE.BoxGeometry(0.14, 0.06, 120), markerMat);
            rail.position.set(x, 0.06, -36);
            worldRoot.add(rail);
          }});

          floorLines = [];
          const sleeperMat = new THREE.MeshStandardMaterial({{ color: 0x475569 }});
          for (let i = 0; i < 40; i += 1) {{
            const sleeper = new THREE.Mesh(new THREE.BoxGeometry(7.2, 0.03, 0.45), sleeperMat);
            sleeper.position.set(0, 0.01, -i * 3);
            worldRoot.add(sleeper);
            floorLines.push(sleeper);
          }}
        }}

        function createRunner() {{
          runnerGroup = new THREE.Group();

          const body = new THREE.Mesh(
            new THREE.BoxGeometry(1.15, 1.55, 0.9),
            new THREE.MeshStandardMaterial({{ color: '{runner_color}', emissive: '{runner_color}', emissiveIntensity: 0.12 }})
          );
          body.position.y = 1.65;
          runnerGroup.add(body);

          const head = new THREE.Mesh(
            new THREE.SphereGeometry(0.42, 20, 20),
            new THREE.MeshStandardMaterial({{ color: 0xf8fafc }})
          );
          head.position.y = 2.75;
          runnerGroup.add(head);

          const visor = new THREE.Mesh(
            new THREE.BoxGeometry(0.62, 0.18, 0.62),
            new THREE.MeshStandardMaterial({{ color: 0x0f172a, emissive: 0x22d3ee, emissiveIntensity: 0.35 }})
          );
          visor.position.set(0, 2.72, 0.17);
          runnerGroup.add(visor);

          const legMat = new THREE.MeshStandardMaterial({{ color: 0x111827 }});
          [-0.26, 0.26].forEach(x => {{
            const leg = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.95, 0.28), legMat);
            leg.position.set(x, 0.68, 0);
            runnerGroup.add(leg);
          }});

          runnerGroup.position.set(0, 0, 5.5);
          scene.add(runnerGroup);
        }}

        function createDecor() {{
          const colors = [0x1e293b, 0x334155, 0x0f172a, 0x1d4ed8];
          for (let i = 0; i < 28; i += 1) {{
            const height = 2 + Math.random() * 6;
            const mesh = new THREE.Mesh(
              new THREE.BoxGeometry(1.8 + Math.random() * 1.4, height, 1.8 + Math.random()),
              new THREE.MeshStandardMaterial({{
                color: colors[i % colors.length],
                emissive: 0x0f172a,
                emissiveIntensity: 0.14,
              }})
            );
            const side = i % 2 === 0 ? -1 : 1;
            mesh.position.set(side * (8 + Math.random() * 7), height / 2, -i * 4.5 - Math.random() * 8);
            worldRoot.add(mesh);
            decorItems.push(mesh);
          }}
        }}

        function resetState() {{
          obstacles.forEach(item => scene.remove(item.mesh));
          obstacles = [];
          state = {{
            started: false,
            over: false,
            lane: 1,
            jumpY: 0,
            jumpVelocity: 0,
            sliding: false,
            slideTimer: 0,
            score: 0,
            speed: 17 * speedFactor,
            spawnTimer: 0,
            coinTimer: 0,
            elapsed: 0,
            duration: 1500,
            timeLeft: 1500,
          }};
          updateRunnerTransform(0);
          updateHud();
          overlay.classList.remove('hidden');
          overlay.querySelector('h3').textContent = 'Auto Runner Timer';
          overlay.querySelector('p').textContent = '按 1 / 5 / 0 / 2 選計時，再按空白鍵開始。角色會自動表演超強跑酷。';
          messageEl.textContent = '已切換成自動專注模式：角色會自行換道、跳躍、滑行，幫你把時間視覺化。';
        }}

        function updateHud() {{
          const displayScore = Math.floor(state.score);
          const timeText = formatTime(state.timeLeft);
          scoreEl.textContent = displayScore;
          cornerScoreEl.textContent = displayScore;
          timeLeftEl.textContent = timeText;
          cornerTimerEl.textContent = timeText;
          if (state.over && state.timeLeft <= 0) stateLabel.textContent = '完成';
          else if (state.over) stateLabel.textContent = '已停止';
          else if (!state.started) stateLabel.textContent = '待命';
          else if (state.timeLeft <= 10) stateLabel.textContent = '衝刺';
          else stateLabel.textContent = '專注中';
        }}

        function updateRunnerTransform(dt) {{
          const targetX = laneX[state.lane];
          const moveFactor = Math.min(1, dt * 10 || 1);
          runnerGroup.position.x += (targetX - runnerGroup.position.x) * moveFactor;
          runnerGroup.position.y = state.jumpY;
          runnerGroup.rotation.z = (targetX - runnerGroup.position.x) * -0.16;
          runnerGroup.scale.y = state.sliding ? 0.42 : 1;
          runnerGroup.scale.x = state.sliding ? 1.18 : 1;
          runnerGroup.scale.z = 1;
          runnerGroup.updateMatrixWorld(true);
        }}

        function spawnObstacle(kind = 'obstacle') {{
          const lane = Math.floor(Math.random() * 3);
          let mesh;
          let type = kind;
          if (kind === 'coin') {{
            mesh = new THREE.Mesh(
              new THREE.TorusGeometry(0.42, 0.14, 10, 24),
              new THREE.MeshStandardMaterial({{ color: 0xfacc15, emissive: 0xf59e0b, emissiveIntensity: 0.55 }})
            );
            mesh.rotation.x = Math.PI / 2;
            mesh.position.y = 1.55;
          }} else {{
            type = Math.random() > 0.5 ? 'high' : 'low';
            const height = type === 'high' ? 2.4 : 0.78;
            mesh = new THREE.Mesh(
              new THREE.BoxGeometry(1.55, height, 1.4),
              new THREE.MeshStandardMaterial({{
                color: type === 'high' ? 0xf97316 : 0xa855f7,
                emissive: type === 'high' ? 0x7c2d12 : 0x581c87,
                emissiveIntensity: 0.28,
              }})
            );
            mesh.position.y = height / 2;
          }}
          mesh.position.x = laneX[lane];
          mesh.position.z = -55;
          scene.add(mesh);
          obstacles.push({{ lane, type, mesh, box: new THREE.Box3() }});
        }}

        function setDuration(seconds) {{
          state.duration = seconds;
          state.timeLeft = seconds;
          updateHud();
          messageEl.textContent = `計時長度已切換為 ${{formatTime(seconds)}}。按空白鍵開始自動跑酷。`;
          if (!state.started) {{
            overlay.querySelector('p').textContent = `目前設定為 ${{formatTime(seconds)}}。按空白鍵開始，角色會自動閃避到時間結束。`;
          }}
        }}

        function startGame() {{
          if (state.started && !state.over) return;
          if (state.over) resetState();
          state.started = true;
          state.over = false;
          state.timeLeft = state.duration;
          state.score = 0;
          state.elapsed = 0;
          state.speed = 17 * speedFactor;
          state.spawnTimer = 0;
          state.coinTimer = 0;
          overlay.classList.add('hidden');
          stateLabel.textContent = '專注中';
          messageEl.textContent = '自動超強跑酷開始：角色會主動判斷路線並閃避障礙，你只要專心做事。';
          game.focus();
        }}

        function finishTimer() {{
          state.over = true;
          state.started = false;
          state.timeLeft = 0;
          overlay.classList.remove('hidden');
          overlay.querySelector('h3').textContent = '專注完成';
          overlay.querySelector('p').textContent = `本輪已完成 ${{formatTime(state.duration)}} 計時，Auto Runner 得分 ${{Math.floor(state.score)}}。按空白鍵再跑一輪。`;
          messageEl.textContent = '計時結束！這輪自動跑酷已順利陪你完成專注時間。';
          updateHud();
        }}

        function nearestThreat() {{
          let best = null;
          let bestDistance = Infinity;
          obstacles.forEach(item => {{
            if (item.type === 'coin') return;
            const dz = runnerGroup.position.z - item.mesh.position.z;
            if (dz < -1 || dz > 18) return;
            if (dz < bestDistance) {{
              bestDistance = dz;
              best = item;
            }}
          }});
          return best;
        }}

        function laneDangerScore(lane) {{
          let score = 0;
          obstacles.forEach(item => {{
            const dz = runnerGroup.position.z - item.mesh.position.z;
            if (item.lane !== lane) return;
            if (item.type === 'coin') {{
              if (dz >= 0 && dz <= 12) score -= 1.2;
              return;
            }}
            if (dz >= 0 && dz <= 7.5) score += 10;
            else if (dz > 7.5 && dz <= 14) score += 3;
          }});
          return score;
        }}

        function triggerJump() {{
          if (state.jumpY === 0) {{
            state.jumpVelocity = 8.8;
          }}
        }}

        function triggerSlide() {{
          if (!state.sliding && state.jumpY < 0.2) {{
            state.sliding = true;
            state.slideTimer = 0.58;
          }}
        }}

        function runAutoPilot() {{
          const threat = nearestThreat();
          let bestLane = state.lane;
          let bestLaneScore = Infinity;
          [0, 1, 2].forEach(lane => {{
            const score = laneDangerScore(lane) + Math.abs(lane - 1) * 0.15;
            if (score < bestLaneScore) {{
              bestLaneScore = score;
              bestLane = lane;
            }}
          }});
          state.lane = bestLane;

          if (!threat || threat.lane !== state.lane) return;

          const dz = runnerGroup.position.z - threat.mesh.position.z;
          if (threat.type === 'high' && dz >= 0.5 && dz <= 6.4 && state.jumpY === 0) {{
            triggerJump();
          }}
          if (threat.type === 'low' && dz >= 0.4 && dz <= 5.4 && !state.sliding && state.jumpY < 0.2) {{
            triggerSlide();
          }}
        }}

        function updateObstacles(dt) {{
          runnerBox.setFromObject(runnerGroup);
          obstacles.slice().forEach(item => {{
            item.mesh.position.z += state.speed * dt;
            if (item.type === 'coin') item.mesh.rotation.z += dt * 3.5;
            item.mesh.updateMatrixWorld(true);
            item.box.setFromObject(item.mesh);

            if (item.type === 'coin' && runnerBox.intersectsBox(item.box)) {{
              state.score += 35;
              scene.remove(item.mesh);
              obstacles = obstacles.filter(o => o !== item);
              return;
            }}

            if (item.mesh.position.z > 16) {{
              scene.remove(item.mesh);
              obstacles = obstacles.filter(o => o !== item);
            }}
          }});
        }}

        function updateEnvironment(dt) {{
          floorLines.forEach(line => {{
            line.position.z += state.speed * dt;
            if (line.position.z > 12) line.position.z -= 120;
          }});
          decorItems.forEach(item => {{
            item.position.z += state.speed * dt * 0.55;
            if (item.position.z > 14) item.position.z -= 140;
          }});
        }}

        function animate() {{
          requestAnimationFrame(animate);
          const dt = Math.min(clock.getDelta(), 0.032);

          if (state.started && !state.over) {{
            state.elapsed += dt;
            state.timeLeft = Math.max(0, state.timeLeft - dt);
            state.score += dt * 84 * speedFactor;
            state.speed = (17 + Math.min(6, state.elapsed * 0.18)) * speedFactor;
            state.spawnTimer += dt;
            state.coinTimer += dt;

            runAutoPilot();

            if (state.spawnTimer >= Math.max(0.56, 1.0 - state.elapsed * 0.015)) {{
              spawnObstacle('obstacle');
              state.spawnTimer = 0;
            }}
            if (state.coinTimer >= 1.65) {{
              spawnObstacle('coin');
              state.coinTimer = 0;
            }}

            if (state.jumpY > 0 || state.jumpVelocity > 0) {{
              state.jumpVelocity -= 18 * dt;
              state.jumpY = Math.max(0, state.jumpY + state.jumpVelocity * dt);
              if (state.jumpY === 0) state.jumpVelocity = 0;
            }}
            if (state.sliding) {{
              state.slideTimer -= dt;
              if (state.slideTimer <= 0) {{
                state.sliding = false;
                state.slideTimer = 0;
              }}
            }}

            updateRunnerTransform(dt);
            updateObstacles(dt);
            updateEnvironment(dt);
            if (Math.floor(state.score) === targetScore) {{
              messageEl.textContent = '已超過預設目標分數，專注計時仍會繼續直到時間結束。';
            }}
            if (state.timeLeft <= 0) {{
              finishTimer();
            }}
            updateHud();
          }} else {{
            updateRunnerTransform(dt);
          }}

          renderer.render(scene, camera);
        }}

        document.addEventListener('keydown', (event) => {{
          if (['Space', 'Digit1', 'Digit5', 'Digit0', 'Digit2'].includes(event.code)) {{
            event.preventDefault();
          }}
          if (durationMap[event.code]) {{
            setDuration(durationMap[event.code]);
            return;
          }}
          if (event.code === 'Space') {{
            startGame();
          }}
        }});

        window.addEventListener('resize', resizeRenderer);
        buildScene();
      </script>
    </body>
    </html>
    """

    components.html(html, height=840)


def render_main() -> str:
    state = load_page_data(PAGE_NAME, shell_root=SHELL_ROOT)

    st.markdown("#### Runner 設定")
    player_name = st.text_input(
        "玩家名稱",
        value=state.get("player_name", ""),
        placeholder="例如：閃電跑者",
    )

    col1, col2 = st.columns(2)
    with col1:
        character_default = state.get("character", CHARACTER_OPTIONS[0])
        character_index = CHARACTER_OPTIONS.index(character_default) if character_default in CHARACTER_OPTIONS else 0
        character = st.selectbox("角色", CHARACTER_OPTIONS, index=character_index)
    with col2:
        difficulty_default = state.get("difficulty", DIFFICULTY_OPTIONS[1])
        difficulty_index = DIFFICULTY_OPTIONS.index(difficulty_default) if difficulty_default in DIFFICULTY_OPTIONS else 1
        difficulty = st.selectbox("難度", DIFFICULTY_OPTIONS, index=difficulty_index)

    target_score = st.slider(
        "目標分數",
        min_value=100,
        max_value=5000,
        step=100,
        value=int(state.get("target_score", 1000)),
    )
    special_move = st.text_input(
        "角色技能",
        value=state.get("special_move", ""),
        placeholder="例如：自動專注模式、番茄陪跑",
    )

    save_page_data(
        PAGE_NAME,
        {
            "player_name": player_name,
            "character": character,
            "difficulty": difficulty,
            "target_score": target_score,
            "special_move": special_move,
        },
        shell_root=SHELL_ROOT,
    )

    st.divider()
    st.markdown("#### Auto Runner Timer")
    st.caption("這個版本已改成自動超強跑酷計時器：角色會自動閃避障礙，並用倒數時間作為主要完成條件。")
    _render_runner_game(character, difficulty, player_name, target_score, special_move)

    st.divider()
    st.markdown("#### 工具模式摘要")
    st.write(
        f"陪跑角色 **{player_name or '（未命名）'}** 會使用 **{character}** 進入 **{difficulty}** 節奏的自動跑酷計時模式，預設參考分數為 **{target_score}**。"
    )
    st.caption(f"目前模式標籤：{special_move or '（未填）'}")
    st.caption("遊戲區內可按 1 / 5 / 0 / 2 切換 1、5、10、25 分鐘，按空白鍵開始。")

    st.divider()
    st.markdown("#### 給 Agent 的摘要")
    extra = format_extra_context(
        PAGE_NAME,
        共享資料檔=str(shared_data_path(PAGE_NAME, shell_root=SHELL_ROOT)),
        玩家名稱=player_name or "（未填）",
        角色=character,
        難度=difficulty,
        目標分數=target_score,
        角色技能=special_move or "（未填）",
        遊戲模式="Auto Runner Timer（自動超強跑酷計時器）",
        操作方式="按 1/5/0/2 切換 1、5、10、25 分鐘；Space 開始或重來",
        技術方案="Streamlit + components.html + Three.js(WebGL)",
    )
    st.code(extra, language="text")
    return extra


page_shell(
    "跑酷遊戲設定",
    "設定角色後，直接使用自動跑酷計時器版本的 Three.js Runner。",
    render_main,
    page_name=PAGE_NAME,
)
