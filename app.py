import io
import base64
import numpy as np
import requests
import streamlit as st
import matplotlib.pyplot as plt
import cv2
from PIL import Image
from scipy.io import wavfile

# ============================================================
# КОНФИГ СТРАНИЦЫ
# ============================================================
st.set_page_config(
    page_title="Sonify — геометрия в звуке",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 🔑 ВСТАВЬТЕ СВОИ КЛЮЧИ SPOTIFY ЗДЕСЬ
# ============================================================
SPOTIFY_CLIENT_ID = ""       # <-- ваш Client ID
SPOTIFY_CLIENT_SECRET = ""   # <-- ваш Client Secret

# Либо через .streamlit/secrets.toml:
#   SPOTIFY_CLIENT_ID = "xxx"
#   SPOTIFY_CLIENT_SECRET = "yyy"
try:
    if not SPOTIFY_CLIENT_ID:
        SPOTIFY_CLIENT_ID = st.secrets.get("SPOTIFY_CLIENT_ID", "")
    if not SPOTIFY_CLIENT_SECRET:
        SPOTIFY_CLIENT_SECRET = st.secrets.get("SPOTIFY_CLIENT_SECRET", "")
except Exception:
    pass

# ============================================================
# ЦВЕТОВЫЕ ТЕМЫ (включая сайдбар)
# ============================================================
THEMES = {
    "Пастель (по умолчанию)": {
        "bg_gradient": "linear-gradient(135deg, #fdf6f0 0%, #f4f0fa 50%, #eef6f7 100%)",
        "card_bg": "rgba(255, 255, 255, 0.75)",
        "title_color": "#4a4a63",
        "accent": "#c8b6e2",
        "accent2": "#a8c8e8",
        "wave_color": "#9b87c9",
        "wave_fill": "#c8b6e2",
        "text_muted": "#8a8aa0",
        "sidebar_bg": "linear-gradient(180deg, #fbf6ff 0%, #f0f6fb 100%)",
        "sidebar_border": "rgba(200, 190, 220, 0.3)",
        "sidebar_text": "#5a5a78",
    },
    "Тёплый закат": {
        "bg_gradient": "linear-gradient(135deg, #fff5ec 0%, #ffe8d6 50%, #ffd6c9 100%)",
        "card_bg": "rgba(255, 250, 245, 0.85)",
        "title_color": "#7a4a3a",
        "accent": "#f0a882",
        "accent2": "#e8c8a0",
        "wave_color": "#d88a6a",
        "wave_fill": "#f0c8b0",
        "text_muted": "#a08070",
        "sidebar_bg": "linear-gradient(180deg, #fff8f0 0%, #ffeede 100%)",
        "sidebar_border": "rgba(240, 200, 170, 0.45)",
        "sidebar_text": "#7a4a3a",
    },
    "Прохладный бриз": {
        "bg_gradient": "linear-gradient(135deg, #f0f8ff 0%, #e6f2fa 50%, #dceefa 100%)",
        "card_bg": "rgba(255, 255, 255, 0.8)",
        "title_color": "#3a5a7a",
        "accent": "#88b8d8",
        "accent2": "#a8d0e8",
        "wave_color": "#6a9ab8",
        "wave_fill": "#a8c8e0",
        "text_muted": "#7090a8",
        "sidebar_bg": "linear-gradient(180deg, #f2faff 0%, #e2f0fa 100%)",
        "sidebar_border": "rgba(168, 208, 232, 0.45)",
        "sidebar_text": "#3a5a7a",
    },
    "Мятная свежесть": {
        "bg_gradient": "linear-gradient(135deg, #f0fff4 0%, #e6faf0 50%, #dcf5ea 100%)",
        "card_bg": "rgba(255, 255, 255, 0.8)",
        "title_color": "#3a6a5a",
        "accent": "#88d8b8",
        "accent2": "#a8e8c8",
        "wave_color": "#6ab898",
        "wave_fill": "#a8d8c0",
        "text_muted": "#709088",
        "sidebar_bg": "linear-gradient(180deg, #f2fff8 0%, #e2f8ee 100%)",
        "sidebar_border": "rgba(168, 232, 200, 0.45)",
        "sidebar_text": "#3a6a5a",
    },
}

with st.sidebar:
    st.markdown("## 🎨 Оформление")
    theme_name = st.selectbox("Цветовая тема", list(THEMES.keys()), index=0)
    T = THEMES[theme_name]
    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)

# ============================================================
# ДИНАМИЧЕСКИЙ CSS
# ============================================================
CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Cormorant+Garamond:wght@500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: #3a3a4a;
}}

.stApp {{
    background: {T['bg_gradient']};
}}

.main-title {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.6rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: {T['title_color']};
    text-align: center;
    margin-bottom: 0.2rem;
}}
.main-subtitle {{
    text-align: center;
    color: {T['text_muted']};
    font-size: 0.98rem;
    margin-bottom: 1.8rem;
    font-weight: 300;
}}

.card {{
    background: {T['card_bg']};
    backdrop-filter: blur(8px);
    border-radius: 22px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 8px 28px rgba(160, 150, 190, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.9);
    margin-bottom: 1rem;
}}
.card-title {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: {T['title_color']};
    margin-bottom: 0.7rem;
    letter-spacing: 0.3px;
}}

/* ======== САЙДБАР — темизирован ======== */
section[data-testid="stSidebar"] {{
    background: {T['sidebar_bg']} !important;
    border-right: 1px solid {T['sidebar_border']} !important;
}}
section[data-testid="stSidebar"] * {{
    color: {T['sidebar_text']} !important;
}}
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {{
    font-family: 'Cormorant Garamond', serif;
    color: {T['sidebar_text']} !important;
}}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] input {{
    border-color: {T['sidebar_border']} !important;
}}
section[data-testid="stSidebar"] [role="slider"] {{
    background: {T['accent']} !important;
}}

.stButton > button, .stDownloadButton > button {{
    background: linear-gradient(135deg, {T['accent']} 0%, {T['accent2']} 100%);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 0.55rem 1.2rem;
    font-weight: 500;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
    box-shadow: 0 4px 14px rgba(168, 200, 232, 0.35);
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(168, 200, 232, 0.5);
    color: white;
}}

audio {{
    width: 100%;
    border-radius: 14px;
    margin-top: 0.5rem;
}}

.stat-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0.8rem;
    margin-bottom: 0.35rem;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 10px;
    border-left: 3px solid {T['accent']};
}}
.stat-label {{
    font-size: 0.88rem;
    color: {T['text_muted']};
    font-weight: 400;
}}
.stat-value {{
    font-size: 0.95rem;
    color: {T['title_color']};
    font-weight: 600;
    font-family: 'Inter', monospace;
}}

.divider-soft {{
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(160,150,190,0.35), transparent);
    margin: 1rem 0;
}}

.track-item {{
    padding: 0.55rem 0.9rem;
    margin-bottom: 0.3rem;
    background: rgba(255, 255, 255, 0.45);
    border-radius: 10px;
    font-size: 0.92rem;
    border-left: 3px solid {T['accent2']};
}}
.track-name {{ font-weight: 600; color: {T['title_color']}; }}
.track-artist {{ color: {T['text_muted']}; font-size: 0.85rem; }}

.img-caption {{
    text-align: center;
    font-size: 0.85rem;
    color: {T['text_muted']};
    margin-top: 0.35rem;
    margin-bottom: 0.8rem;
    letter-spacing: 0.2px;
}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# ЗАГОЛОВОК
# ============================================================
st.markdown('<div class="main-title">Sonify · Геометрия в звуке</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Превратите линии, контуры и формы интерьера в звуковую композицию — '
    'для презентаций архитектурных и дизайнерских проектов.</div>',
    unsafe_allow_html=True,
)

# ============================================================
# БОКОВАЯ ПАНЕЛЬ — ПАРАМЕТРЫ СИНТЕЗА
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ Параметры синтеза")
    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)

    sample_rate = st.selectbox(
        "Частота дискретизации (Гц)",
        options=[44100, 48000],
        index=0,
    )

    pixel_duration_ms = st.slider(
        "Длительность одного пикселя (мс)",
        min_value=1, max_value=50, value=6, step=1,
    )

    freq_min = st.number_input("Минимальная частота (Гц)", 50, 2000, 150, 10)
    freq_max = st.number_input("Максимальная частота (Гц)", 200, 12000, 4000, 50)

    scan_size = st.slider(
        "Разрешение сканирования (пикселей по ширине)",
        min_value=64, max_value=512, value=256, step=16,
    )

    waveform = st.selectbox(
        "Форма волны",
        options=["Синусоидальная (Sine)", "Прямоугольная (Square)",
                 "Пилообразная (Sawtooth)", "Треугольная (Triangle)"],
        index=0,
    )

    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)
    st.markdown("### ⏱️ Длительность аудио")

    total_duration = st.slider(
        "Длительность (сек)",
        min_value=3.0, max_value=180.0, value=30.0, step=1.0,
    )

    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)
    show_contours = st.checkbox("Показывать контуры поверх изображения", value=True)
    canny_low = st.slider("Canny: нижний порог", 0, 255, 60)
    canny_high = st.slider("Canny: верхний порог", 0, 255, 160)

if freq_min >= freq_max:
    st.error("Минимальная частота должна быть меньше максимальной.")
    st.stop()

# ============================================================
# ФУНКЦИИ СИНТЕЗА
# ============================================================
def extract_geometry(gray: np.ndarray, size: int, low: int, high: int) -> np.ndarray:
    img = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    edges = cv2.Canny(img, low, high)
    edges = cv2.GaussianBlur(edges, (3, 3), 0)
    return edges.astype(np.float32) / 255.0


def image_to_sound(geometry: np.ndarray, sample_rate: int, pixel_duration_ms: float,
                   freq_min: float, freq_max: float, waveform: str) -> np.ndarray:
    h, w = geometry.shape
    pixel_samples = max(8, int(sample_rate * pixel_duration_ms / 1000.0))
    audio = np.zeros(w * pixel_samples, dtype=np.float32)

    for x in range(w):
        column = geometry[:, x]
        col_energy = float(np.sum(column))
        if col_energy < 1e-6:
            continue

        ys = np.arange(h, dtype=np.float32)
        norm_y = 1.0 - (ys / max(h - 1, 1))
        weights = column / (col_energy + 1e-9)
        avg_norm_y = float(np.sum(weights * norm_y))

        freq = freq_min * (freq_max / freq_min) ** avg_norm_y
        amp = float(np.clip(col_energy / (h * 0.35), 0.0, 1.0))

        t = np.arange(pixel_samples, dtype=np.float32) / sample_rate
        phase = 2 * np.pi * freq * t

        if waveform.startswith("Синус"):
            wave = np.sin(phase)
        elif waveform.startswith("Прямоуг"):
            wave = np.sign(np.sin(phase))
        elif waveform.startswith("Пилообр"):
            wave = 2.0 * ((freq * t) % 1.0) - 1.0
        else:
            wave = 4.0 * np.abs(((freq * t) % 1.0) - 0.5) - 1.0

        env = np.hanning(pixel_samples).astype(np.float32)
        audio[x * pixel_samples:(x + 1) * pixel_samples] = wave * amp * env

    peak = float(np.max(np.abs(audio))) if audio.size else 1.0
    if peak > 0:
        audio = audio / peak * 0.9
    return audio.astype(np.float32)


def enforce_duration(audio: np.ndarray, sr: int, target_sec: float) -> np.ndarray:
    target_len = int(sr * target_sec)
    if audio.size == 0:
        return np.zeros(target_len, dtype=np.float32)
    x_old = np.linspace(0, 1, audio.size, endpoint=False)
    x_new = np.linspace(0, 1, target_len, endpoint=False)
    resampled = np.interp(x_new, x_old, audio).astype(np.float32)
    peak = float(np.max(np.abs(resampled)))
    if peak > 0:
        resampled = resampled / peak * 0.9
    return resampled


def to_wav_bytes(audio: np.ndarray, sr: int) -> io.BytesIO:
    buf = io.BytesIO()
    pcm = np.int16(np.clip(audio, -1.0, 1.0) * 32767)
    wavfile.write(buf, sr, pcm)
    buf.seek(0)
    return buf


def describe_audio(audio: np.ndarray, sr: int) -> dict:
    if audio.size == 0:
        return {"avg_freq": 0, "peak_amp": 0, "rms": 0, "duration": 0, "richness": 0}
    n = min(len(audio), sr * 4)
    spectrum = np.abs(np.fft.rfft(audio[:n] * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1 / sr)
    total = float(np.sum(spectrum) + 1e-9)
    avg_freq = float(np.sum(freqs * spectrum) / total)
    rms = float(np.sqrt(np.mean(audio ** 2)))
    thr = np.mean(spectrum) + np.std(spectrum)
    richness = int(np.sum(spectrum > thr))
    return {
        "avg_freq": avg_freq,
        "peak_amp": float(np.max(np.abs(audio))),
        "rms": rms,
        "duration": len(audio) / sr,
        "richness": richness,
    }


# ============================================================
# SPOTIFY: ТОКЕН + ПОИСК ЧЕРЕЗ SEARCH API
# ============================================================
@st.cache_data(ttl=3500, show_spinner=False)
def get_spotify_token(client_id: str, client_secret: str):
    if not client_id or not client_secret:
        return None
    try:
        auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


@st.cache_data(ttl=3500, show_spinner=False)
def find_similar_tracks(avg_freq: float, rms: float, duration: float,
                        token: str, limit: int = 5) -> list:
    """
    Поиск похожих реальных треков через Spotify Search API.
    Средняя частота и RMS -> ключевые слова настроения.
    """
    if not token:
        return []

    if avg_freq < 500:
        mood = "ambient dark"
    elif avg_freq < 1500:
        mood = "chill electronic"
    elif avg_freq < 2500:
        mood = "mellow indie"
    else:
        mood = "bright energetic"

    if rms < 0.1:
        mood += " soft"
    elif rms > 0.5:
        mood += " upbeat"

    query = mood.strip()

    try:
        resp = requests.get(
            "https://api.spotify.com/v1/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"q": query, "type": "track", "limit": limit},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        items = resp.json().get("tracks", {}).get("items", [])
        return [
            {
                "name": t.get("name", "Unknown"),
                "artist": t["artists"][0]["name"] if t.get("artists") else "—",
                "url": t.get("external_urls", {}).get("spotify", ""),
            }
            for t in items
        ]
    except Exception:
        return []


# ============================================================
# ЗАГРУЗКА ИЗОБРАЖЕНИЯ
# ============================================================
uploaded = st.file_uploader(
    "📤 Загрузите изображение плана, фасада или интерьера (JPG / PNG)",
    type=["jpg", "jpeg", "png"],
)

if uploaded is None:
    st.markdown(
        '<div class="card" style="text-align:center; padding:3rem 2rem;">'
        '<div class="card-title">Здесь появится ваша композиция</div>'
        '<p style="color:#8a8aa0;">Загрузите изображение плана, разреза или интерьера — '
        'и приложение переведёт его геометрию в звук.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Чтение изображения (безопасно)
pil_img = Image.open(uploaded).convert("RGB")
img_rgb = np.array(pil_img, dtype=np.uint8)
if img_rgb.ndim == 2:
    img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_GRAY2RGB)
if img_rgb.shape[2] != 3:
    img_rgb = img_rgb[:, :, :3]
img_rgb = np.ascontiguousarray(img_rgb)
gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

# Синтез
geometry = extract_geometry(gray, scan_size, canny_low, canny_high)
audio = image_to_sound(geometry, sample_rate, pixel_duration_ms,
                       freq_min, freq_max, waveform)
audio = enforce_duration(audio, sample_rate, total_duration)
stats = describe_audio(audio, sample_rate)

# ============================================================
# ВЕРХНИЙ БЛОК: две колонки
# ============================================================
col_left, col_right = st.columns(2, gap="large")

# ----- ЛЕВАЯ: симметричная волна + характеристики в столбик -----
with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🌊 Волновая форма</div>', unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=110)
    fig.patch.set_alpha(0)
    ax.set_facecolor((1, 1, 1, 0.0))

    vis_len = min(len(audio), sample_rate * 10)
    t_axis = np.arange(vis_len) / sample_rate
    wave_vis = audio[:vis_len]

    # Симметричная огибающая: +|wave| и -|wave|
    pos_env = np.abs(wave_vis)
    ax.fill_between(t_axis, pos_env, -pos_env,
                    color=T['wave_fill'], alpha=0.45, linewidth=0)
    ax.plot(t_axis, pos_env, color=T['wave_color'], linewidth=0.9)
    ax.plot(t_axis, -pos_env, color=T['wave_color'], linewidth=0.9)
    ax.axhline(0, color=T['wave_color'], linewidth=0.8, alpha=0.6, linestyle="--")

    ax.set_xlabel("Время, с", color=T['text_muted'], fontsize=9)
    ax.set_ylabel("Амплитуда (симметрично)", color=T['text_muted'], fontsize=9)
    ax.tick_params(colors=T['text_muted'], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#d8d2e6")
    ax.grid(True, color="#ece7f5", linewidth=0.6)
    max_env = float(np.max(pos_env)) if len(pos_env) else 1.0
    ax.set_ylim(-max_env * 1.1, max_env * 1.1)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Характеристики в столбик
    st.markdown(
        f"""
        <div class="stat-row"><span class="stat-label">Средняя частота</span><span class="stat-value">{stats['avg_freq']:.1f} Гц</span></div>
        <div class="stat-row"><span class="stat-label">Пиковая амплитуда</span><span class="stat-value">{stats['peak_amp']:.3f}</span></div>
        <div class="stat-row"><span class="stat-label">RMS (громкость)</span><span class="stat-value">{stats['rms']:.3f}</span></div>
        <div class="stat-row"><span class="stat-label">Длительность</span><span class="stat-value">{stats['duration']:.1f} с</span></div>
        <div class="stat-row"><span class="stat-label">Спектральная насыщенность</span><span class="stat-value">{stats['richness']} пиков</span></div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ----- ПРАВАЯ: ДВЕ картинки (исходная + контуры) + WAV + плеер -----
with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🖼️ Изображение и результат</div>', unsafe_allow_html=True)

    # Готовим изображение с наложенными контурами
    contour_img = img_rgb.copy()
    try:
        img_safe = np.ascontiguousarray(img_rgb.astype(np.uint8))
        edges_vis = (np.clip(geometry, 0.0, 1.0) * 255).astype(np.uint8)
        if edges_vis.ndim == 3:
            edges_vis = cv2.cvtColor(edges_vis, cv2.COLOR_RGB2GRAY)
        th, tw = img_safe.shape[:2]
        if edges_vis.shape[:2] != (th, tw):
            edges_vis = cv2.resize(edges_vis, dsize=(tw, th),
                                   interpolation=cv2.INTER_NEAREST)
        edges_rgb = np.ascontiguousarray(cv2.cvtColor(edges_vis, cv2.COLOR_GRAY2RGB))
        contour_img = cv2.addWeighted(img_safe, 0.55, edges_rgb, 0.45, 0)
    except Exception as e:
        st.warning(f"⚠️ Не удалось наложить контуры ({e}). Показано исходное изображение.")
        contour_img = img_rgb

    # Две картинки рядом
    if show_contours:
        img_col1, img_col2 = st.columns(2, gap="small")
        with img_col1:
            st.image(img_rgb, use_container_width=True)
            st.markdown('<div class="img-caption">📷 Исходное изображение</div>',
                        unsafe_allow_html=True)
        with img_col2:
            st.image(contour_img, use_container_width=True)
            st.markdown('<div class="img-caption">✏️ Считанные линии (контуры)</div>',
                        unsafe_allow_html=True)
    else:
        st.image(img_rgb, use_container_width=True)
        st.markdown('<div class="img-caption">📷 Исходное изображение</div>',
                    unsafe_allow_html=True)

    # Аудио и скачивание
    wav_buf = to_wav_bytes(audio, sample_rate)
    wav_bytes = wav_buf.getvalue()
    st.audio(wav_bytes, format="audio/wav")
    st.download_button(
        label="⬇️ Скачать WAV",
        data=wav_bytes,
        file_name=f"sonify_{sample_rate}Hz_{int(total_duration)}s.wav",
        mime="audio/wav",
        use_container_width=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# НИЖНИЙ БЛОК: профиль плотности
# ============================================================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">📊 Профиль плотности геометрических линий</div>',
            unsafe_allow_html=True)

x_profile = np.sum(geometry, axis=0)
x_profile_norm = x_profile / (np.max(x_profile) + 1e-9)
y_profile = np.sum(geometry, axis=1)
y_profile_norm = y_profile / (np.max(y_profile) + 1e-9)

fig2, axes = plt.subplots(1, 2, figsize=(12, 3), dpi=110)
fig2.patch.set_alpha(0)
for ax in axes:
    ax.set_facecolor((1, 1, 1, 0.0))
    for spine in ax.spines.values():
        spine.set_color("#d8d2e6")
    ax.tick_params(colors=T['text_muted'], labelsize=8)
    ax.grid(True, color="#ece7f5", linewidth=0.6)

axes[0].fill_between(np.arange(len(x_profile_norm)), x_profile_norm,
                     color=T['wave_fill'], alpha=0.55)
axes[0].plot(x_profile_norm, color=T['wave_color'], linewidth=1.2)
axes[0].set_title("Плотность линий по горизонтали (X → время)",
                  color=T['title_color'], fontsize=10, fontfamily="serif")
axes[0].set_xlabel("Сканируемая колонка", color=T['text_muted'], fontsize=9)
axes[0].set_ylabel("Плотность", color=T['text_muted'], fontsize=9)

axes[1].fill_between(np.arange(len(y_profile_norm)), y_profile_norm,
                     color=T['accent2'], alpha=0.55)
axes[1].plot(y_profile_norm, color=T['accent'], linewidth=1.2)
axes[1].invert_yaxis()
axes[1].set_title("Плотность линий по вертикали (Y → высота тона)",
                  color=T['title_color'], fontsize=10, fontfamily="serif")
axes[1].set_xlabel("Плотность", color=T['text_muted'], fontsize=9)
axes[1].set_ylabel("Строка (сверху вниз)", color=T['text_muted'], fontsize=9)

fig2.tight_layout()
st.pyplot(fig2, use_container_width=True)
plt.close(fig2)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ПОХОЖИЕ ТРЕКИ
# ============================================================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">🎧 Похожие реальные композиции</div>', unsafe_allow_html=True)

token = get_spotify_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

if not token:
    st.info(
        "🔑 Для поиска похожих треков добавьте `SPOTIFY_CLIENT_ID` и `SPOTIFY_CLIENT_SECRET` "
        "в начале файла `app.py` или в `.streamlit/secrets.toml`. "
        "Ключи бесплатно выдаются на [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)."
    )
else:
    with st.spinner("Ищу композиции с похожими характеристиками…"):
        similar = find_similar_tracks(
            avg_freq=stats["avg_freq"],
            rms=stats["rms"],
            duration=stats["duration"],
            token=token,
            limit=5,
        )
    if not similar:
        st.warning("Не удалось получить рекомендации. Возможно, временно недоступен API Spotify.")
    else:
        st.caption(
            f"Подобрано по: средняя частота ≈ {stats['avg_freq']:.0f} Гц, "
            f"RMS ≈ {stats['rms']:.2f}"
        )
        for tr in similar:
            link = f' — <a href="{tr["url"]}" target="_blank">открыть</a>' if tr["url"] else ""
            st.markdown(
                f'<div class="track-item">'
                f'<span class="track-name">{tr["name"]}</span>'
                f'<span class="track-artist"> — {tr["artist"]}</span>{link}'
                f'</div>',
                unsafe_allow_html=True,
            )
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# ФУТЕР
# ============================================================
st.markdown(
    '<div style="text-align:center; color:#a8a8bd; font-size:0.8rem; margin-top:1.5rem;">'
    'Sonify · геометрия интерьера, звучащая как музыка'
    '</div>',
    unsafe_allow_html=True,
)
