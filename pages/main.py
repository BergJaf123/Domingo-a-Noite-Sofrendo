import base64
import json
import os
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Dimensões do jogo
WIDTH = 1400
HEIGHT = 800

# Dicionário de tipos MIME
MIME_BY_SUFFIX = {
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif",
}

def get_local_file_as_data_uri(file_name):
    # O arquivo original usava .parent.parent, o que pode subir demais na estrutura de pastas
    # Vamos tentar encontrar o arquivo no diretório atual primeiro
    base_path = Path(__file__).parent
    file_path = base_path / file_name
    
    # Se não encontrar no atual, tenta no diretório pai (caso esteja em uma subpasta)
    if not file_path.exists():
        file_path = base_path.parent / file_name
        
    if not file_path.exists(): 
        return None
        
    suffix = file_path.suffix.lower()
    mime = MIME_BY_SUFFIX.get(suffix, "application/octet-stream")
    try:
        with open(file_path, "rb") as f:
            payload = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{payload}"
    except: 
        return None

def file_to_data_uri(uploaded_file, file_name, fallback_mime="application/octet-stream"):
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        mime = MIME_BY_SUFFIX.get(suffix, fallback_mime)
        payload = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
        return f"data:{mime};base64,{payload}", "Upload"
    
    uri = get_local_file_as_data_uri(file_name)
    return (uri, "Padrão") if uri else ("", "Não encontrado")

# Estilo CSS
st.markdown("""
    <style>
        .block-container { padding: 1rem 1rem; max-width: 100% !important; }
        [data-testid="stSidebar"] { width: 300px !important; }
        .stFileUploader section { padding: 0.1rem 0.3rem !important; min-height: 45px !important; }
        .stFileUploader label { font-size: 0.75rem !important; margin-bottom: 2px !important; }
        .stFileUploader div div { font-size: 0.65rem !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🕹️ Domingo de Noite Sofrendo")

with st.sidebar:
    st.header("🎮 Configurações")
    
    if st.button("🏠 Voltar para o Início"):
        st.info("Redirecionando...")
        # st.switch_page("GameBerg.py") # Comentado para evitar erro se o arquivo não existir
    
    st.divider()
    st.subheader("🎵 Música")
    audio_file = st.file_uploader("Trocar Música", type=["mp3", "wav", "ogg"], label_visibility="collapsed")
    audio_uri, audio_status = file_to_data_uri(audio_file, "musica.mp3", "audio/mpeg")
    st.caption(f"Status: {audio_status}")
    if audio_status == "Não encontrado":
        st.warning("Arquivo 'musica.mp3' não encontrado na pasta do script.")
    
    st.divider()
    st.subheader("🖼️ Sprites")
    chroma_sensitivity = st.slider("Chroma Key", 0, 255, 100)
    
    col1, col2 = st.columns(2)
    with col1:
        u_idle = st.file_uploader("Idle", type=["png", "jpg"], key="u_idle")
        u_left = st.file_uploader("Esq", type=["png", "jpg"], key="u_left")
        u_down = st.file_uploader("Baixo", type=["png", "jpg"], key="u_down")
    with col2:
        u_up = st.file_uploader("Cima", type=["png", "jpg"], key="u_up")
        u_right = st.file_uploader("Dir", type=["png", "jpg"], key="u_right")

    idle_uri, s_idle = file_to_data_uri(u_idle, "sprite_p.png")
    left_uri, s_left = file_to_data_uri(u_left, "sprite_e.png")
    down_uri, s_down = file_to_data_uri(u_down, "sprite_b.png")
    up_uri, s_up = file_to_data_uri(u_up, "sprite_c.png")
    right_uri, s_right = file_to_data_uri(u_right, "sprite_d.png")
    
    # Mostrar avisos se os sprites padrão não forem encontrados
    if "Não encontrado" in [s_idle, s_left, s_down, s_up, s_right]:
        st.error("Alguns sprites padrão não foram encontrados.")

    st.divider()
    st.subheader("⚙️ Dificuldade")
    bpm = st.slider("BPM", 60, 500, 172)
    note_speed = st.slider("Velocidade", 100, 1000, 350)
    note_freq = st.slider("Densidade", 0.2, 5.0, 1.0)
    seed = st.number_input("Seed", value=12345)

# Preparar assets para o JavaScript
assets = {
    "audio": audio_uri,
    "sprites": {
        "idle": idle_uri,
        "left": left_uri or idle_uri,
        "down": down_uri or idle_uri,
        "up": up_uri or idle_uri,
        "right": right_uri or idle_uri,
    },
    "config": {
        "width": WIDTH, "height": HEIGHT, "bpm": bpm,
        "noteSpeed": note_speed, "noteFreq": note_freq,
        "seed": int(seed), "chromaSensitivity": chroma_sensitivity
    },
}

config_json = json.dumps(assets, ensure_ascii=False)

# Código HTML/JS do jogo
html_code = f"""
<div id="game-container" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
    <div style="width: 100%; max-width: {WIDTH}px; display: flex; justify-content: space-between; margin-bottom: 10px;">
        <button id="start-btn" style="padding: 12px 24px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">JOGAR / REINICIAR</button>
        <span id="game-status" style="color: white; font-family: monospace; font-size: 18px;">Aguardando...</span>
    </div>
    <canvas id="gameCanvas" width="{WIDTH}" height="{HEIGHT}" tabindex="0" style="background: #146464; border: 4px solid #262730; border-radius: 12px; outline: none; width: 100%; max-width: {WIDTH}px; height: auto;"></canvas>
</div>

<script>
(() => {{
    const assets = {config_json};
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const startBtn = document.getElementById('start-btn');
    const statusTxt = document.getElementById('game-status');

    const COLORS = {{ bg: '#146464', dark: '#141428', gray: '#3c3c50', white: '#ffffff', hitLine: '#c8c8ff', perfect: '#ffdc32', good: '#50dc78', miss: '#dc3c3c', combo: '#ffb400', lanes: ['#ffffff', '#ffa032', '#3cffff', '#f0a0f0'] }};
    const GAME_CFG = {{ laneCount: 4, laneWidth: 80, gap: 15, startX: 50, hitY: {HEIGHT} - 120, noteH: 30, charX: {WIDTH}*0.65, charY: {HEIGHT}-100, spriteH: 500 }};
    const KEY_MAP = {{ 'ArrowLeft': 0, 'ArrowDown': 1, 'ArrowUp': 2, 'ArrowRight': 3, 'a': 0, 's': 1, 'j': 2, 'k': 3, 'A': 0, 'S': 1, 'J': 2, 'K': 3 }};

    function removeGreen(img) {{
        const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
        const x = c.getContext('2d'); x.drawImage(img, 0, 0);
        const d = x.getImageData(0, 0, c.width, c.height);
        const s = assets.config.chromaSensitivity;
        for (let i=0; i<d.data.length; i+=4) {{ if (d.data[i+1] > s && d.data[i+1] > d.data[i] && d.data[i+1] > d.data[i+2]) d.data[i+3] = 0; }}
        x.putImageData(d, 0, 0); const n = new Image(); n.src = c.toDataURL(); return n;
    }}

    const sprites = {{}};
    const spritePromises = Object.entries(assets.sprites).map(([name, src]) => {{
        if (!src) return Promise.resolve();
        return new Promise(r => {{ const i = new Image(); i.onload = () => {{ sprites[name] = removeGreen(i); r(); }}; i.src = src; }});
    }});

    const audio = assets.audio ? new Audio(assets.audio) : null;

    class Game {{
        constructor() {{ this.reset(); }}
        reset() {{
            this.running = false; this.score = 0; this.combo = 0; this.health = 100;
            this.feedback = ""; this.fbT = 0; this.pose = "idle"; this.poseT = 0;
            this.flash = [0,0,0,0]; this.gameOver = false; this.finished = false;
            this.rng = assets.config.seed; this.chart = this.genChart();
            if (audio) {{ audio.pause(); audio.currentTime = 0; }}
        }}
        random() {{ this.rng = (this.rng * 1664525 + 1013904223) >>> 0; return this.rng / 4294967296; }}
        genChart() {{
            const n = []; const dur = (audio && audio.duration && isFinite(audio.duration)) ? audio.duration : 120; const bi = 60 / assets.config.bpm;
            let t = 3.0;
            while (t < dur - 1.0) {{
                const l = Math.floor(this.random() * 4); n.push({{ lane: l, time: t, hit: false, miss: false }});
                if (this.random() < 0.2) n.push({{ lane: (l+1)%4, time: t, hit: false, miss: false }});
                t += bi * [0.5, 1, 1, 1, 2][Math.floor(this.random()*5)] * assets.config.noteFreq;
            }}
            return n.sort((a,b) => a.time - b.time);
        }}
        start() {{ this.reset(); this.running = true; this.startTime = performance.now(); if (audio) audio.play(); statusTxt.textContent = "JOGANDO!"; }}
        update(now) {{
            if (!this.running || this.gameOver || this.finished) return;
            const ct = (now - this.startTime) / 1000;
            for (const n of this.chart) if (!n.hit && !n.miss && n.time < ct - 0.25) {{ n.miss = true; this.combo = 0; this.health -= 8; this.feedback = "MISS"; this.fbT = 0.4; }}
            if (this.fbT > 0) this.fbT -= 1/60;
            if (this.poseT > 0) this.poseT -= 1/60; else this.pose = "idle";
            for (let i=0; i<4; i++) if (this.flash[i] > 0) this.flash[i] -= 1/60;
            if (this.health <= 0) {{ this.gameOver = true; this.running = false; if (audio) audio.pause(); statusTxt.textContent = "GAME OVER"; }}
            const dur = (audio && audio.duration && isFinite(audio.duration)) ? audio.duration : 120;
            if (ct > dur + 1) {{ this.finished = true; this.running = false; statusTxt.textContent = "FIM!"; }}
        }}
        handle(key) {{
            const l = KEY_MAP[key]; if (l === undefined || !this.running) return;
            const ct = (performance.now() - this.startTime) / 1000;
            let b = null; let d = 999;
            for (const n of this.chart) if (!n.hit && !n.miss && n.lane === l) {{ const df = Math.abs(n.time - ct); if (df < d) {{ d = df; b = n; }} }}
            if (!b || d > 0.25) return;
            this.flash[l] = 0.15; this.pose = ["left", "down", "up", "right"][l]; this.poseT = 0.25;
            if (d < 0.08) {{ b.hit = true; this.score += 300; this.combo++; this.feedback = "PERFECT"; this.fbT = 0.6; this.health = Math.min(100, this.health+5); }}
            else {{ b.hit = true; this.score += 100; this.combo++; this.feedback = "GOOD"; this.fbT = 0.5; this.health = Math.min(100, this.health+2); }}
        }}
        roundRect(x, y, w, h, r, fill) {{
            ctx.beginPath(); ctx.moveTo(x+r, y); ctx.arcTo(x+w, y, x+w, y+h, r); ctx.arcTo(x+w, y+h, x, y+h, r); ctx.arcTo(x, y+h, x, y, r); ctx.arcTo(x, y, x+w, y, r); ctx.closePath();
            if (fill) ctx.fill(); else ctx.stroke();
        }}
        draw() {{
            ctx.fillStyle = COLORS.bg; ctx.fillRect(0, 0, {WIDTH}, {HEIGHT});
            const ct = this.running ? (performance.now() - this.startTime) / 1000 : 0;
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * 100;
                ctx.fillStyle = COLORS.dark; ctx.fillRect(x, 0, 90, {HEIGHT});
                ctx.strokeStyle = COLORS.lanes[i]; ctx.lineWidth = 2; ctx.strokeRect(x, 0, 90, {HEIGHT});
            }}
            ctx.strokeStyle = COLORS.hitLine; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(GAME_CFG.startX-10, GAME_CFG.hitY); ctx.lineTo(GAME_CFG.startX+390, GAME_CFG.hitY); ctx.stroke();
            for (const n of this.chart) {{
                if (n.hit || n.miss) continue;
                const td = n.time - ct; if (td > 2 || td < -0.5) continue;
                const y = GAME_CFG.hitY - td * assets.config.noteSpeed - 17;
                const x = GAME_CFG.startX + n.lane * 100;
                ctx.fillStyle = COLORS.lanes[n.lane]; this.roundRect(x+5, y, 80, 35, 12, true);
                ctx.strokeStyle = "white"; ctx.lineWidth = 2; this.roundRect(x+5, y, 80, 35, 12, false);
            }}
            const labels = ["◄", "▼", "▲", "►"];
            for (let i=0; i<4; i++) {{
                const x = GAME_CFG.startX + i * 100;
                ctx.fillStyle = this.flash[i] > 0 ? COLORS.lanes[i] : COLORS.gray;
                this.roundRect(x+5, GAME_CFG.hitY-25, 80, 50, 15, true);
                ctx.fillStyle = "white"; ctx.font = "bold 30px monospace"; ctx.textAlign = "center";
                ctx.fillText(labels[i], x+45, GAME_CFG.hitY+10);
            }}
            const img = sprites[this.pose] || sprites.idle;
            if (img) {{ const r = 500/img.height; ctx.drawImage(img, {WIDTH}*0.7-img.width*r/2, {HEIGHT}-120-550, img.width*r, 550); }}
            ctx.textAlign = "left"; ctx.fillStyle = "white"; ctx.font = "bold 40px monospace";
            ctx.fillText("SCORE: " + String(this.score).padStart(8, '0'), 500, 80);
            if (this.combo >= 3) {{ ctx.fillStyle = COLORS.combo; ctx.fillText(this.combo + "x COMBO", 500, 130); }}
            if (this.fbT > 0) {{ ctx.globalAlpha = Math.min(1, this.fbT / 0.2); ctx.fillStyle = this.feedback === "PERFECT" ? COLORS.perfect : (this.feedback === "MISS" ? COLORS.miss : COLORS.good); ctx.font = "bold 70px monospace"; ctx.fillText(this.feedback, GAME_CFG.startX, GAME_CFG.hitY-100); ctx.globalAlpha = 1; }}
            ctx.fillStyle = COLORS.gray; this.roundRect(500, {HEIGHT}-100, 450, 35, 15, true);
            ctx.fillStyle = this.health > 25 ? COLORS.good : COLORS.miss; this.roundRect(500, {HEIGHT}-100, 450*(this.health/100), 35, 15, true);
            ctx.strokeStyle = "white"; ctx.lineWidth = 3; this.roundRect(500, {HEIGHT}-100, 450, 35, 15, false);
            if (this.gameOver) this.drawOverlay("GAME OVER", COLORS.miss, "HP zerado!");
            if (this.finished) this.drawOverlay("FIM!", COLORS.perfect, "Score: " + this.score);
            if (!this.running && !this.gameOver && !this.finished) {{ this.drawOverlay("PRONTO?", "white", "Clique em JOGAR"); }}
        }}
        drawOverlay(txt, color, sub) {{
            ctx.fillStyle = "rgba(0,0,0,0.8)"; ctx.fillRect(0,0,{WIDTH},{HEIGHT});
            ctx.textAlign = "center"; ctx.fillStyle = color; ctx.font = "bold 100px monospace";
            ctx.fillText(txt, {WIDTH}/2, {HEIGHT}/2);
            ctx.fillStyle = "white"; ctx.font = "bold 40px monospace"; ctx.fillText(sub, {WIDTH}/2, {HEIGHT}/2 + 80);
        }}
    }}

    const game = new Game();
    function loop(n) {{ game.update(n); game.draw(); requestAnimationFrame(loop); }}
    startBtn.onclick = () => {{ canvas.focus(); game.start(); }};
    canvas.onkeydown = (e) => {{ if (e.key === 'Enter' && !game.running) game.start(); game.handle(e.key); }};
    Promise.all(spritePromises).then(() => {{ requestAnimationFrame(loop); statusTxt.textContent = "Pronto!"; }});
}})();
</script>
"""

components.html(html_code, height=900, scrolling=False)
