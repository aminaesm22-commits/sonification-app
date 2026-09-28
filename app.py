import io
import numpy as np
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
# КАСТОМНЫЙ CSS — мягкие пастельные тона, скругления, шрифты
# ============================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Cormorant+Garamond:wght@500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #3a3a4a;
}

.stApp {
    background: linear-gradient(135deg, #fdf6f0 0%, #f4f0fa 50%, #eef6f7 100%);
}

/* Заголовок */
.main-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.6rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: #4a4a63;
    text-align: center;
    margin-bottom: 0.2rem;
}
.main-subtitle {
    text-align: center;
    color: #8a8aa0;
    font-size: 0.98rem;
    margin-bottom: 1.8rem;
    font-weight: 300;
}

/* Карточки */
.card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(8px);
    border-radius: 22px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 8px 28px rgba(160, 150, 190, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.9);
    margin-bottom: 1rem;
}
.card-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: #5a5a78;
    margin-bottom: 0.7rem;
    letter-spacing: 0.3px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fbf6ff 0%, #f0f6fb 100%);
    border-right: 1px solid rgba(200, 190, 220, 0.3);
}
section[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'Cormorant Garamond', serif;
    color: #5a5a78;
}

/* Кнопки */
.stButton > button, .stDownloadButton > button {
    background: linear-gradient(135deg, #c8b6e2 0%, #a8c8e8 100%);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 0.55rem 1.2rem;
    font-weight: 500;
    letter-spacing: 0.3px;
    transition: all 0.25s ease;
    box-shadow: 0 4px 14px rgba(168, 200, 232, 0.35);
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(168, 200, 232, 0.5);
    color: white;
}

/* Аудиоплеер */
audio {
    width: 100%;
    border-radius: 14px;
    margin-top: 0.5rem;
}

/* Метрики-плашки */
.stat-pill {
    display: inline-block;
    background: rgba(200, 182, 226, 0.18);
    color: #5a5a78;
    border-radius: 12px;
    padding: 0.35rem 0.85rem;
    margin: 0.15rem 0.25rem 0.15rem 0;
    font-size: 0.85rem;
    font-weight: 500;
}
.divider-soft {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(160,150,190,0.35), transparent);
    margin: 1rem 0;
}
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
        help="Стандартные значения аудио-CD и профессионального аудио.",
    )

    pixel_duration_ms = st.slider(
        "Длительность одного пикселя (мс)",
        min_value=1, max_value=50, value=6, step=1,
        help="Сколько миллисекунд «звучит» каждая вертикальная колонка изображения.",
    )

    freq_min = st.number_input("Минимальная частота (Гц)", 50, 2000, 150, 10)
    freq_max = st.number_input("Максимальная частота (Гц)", 200, 12000, 4000, 50)

    scan_size = st.slider(
        "Разрешение сканирования (пикселей по ширине)",
        min_value=64, max_value=512, value=256, step=16,
        help="Число вертикальных срезов изображения, каждый = один тон.",
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
        help="Итоговая длина аудио. Автоматически согласуется с длительностью пикселя.",
    )

    st.markdown('<div class="divider-soft"></div>', unsafe_allow_html=True)
    show_contours = st.checkbox("Показывать контуры поверх изображения", value=True)
    canny_low = st.slider("Canny: нижний порог", 0, 255, 60)
    canny_high = st.slider("Canny: верхний порог", 0, 255, 160)

# Проверка корректности частот
if freq_min >= freq_max:
    st.error("Минимальная частота должна быть меньше максимальной.")
    st.stop()

# ============================================================
# ЗАГРУЗКА ИЗОБРАЖЕНИЯ
# ============================================================
uploaded = st.file_uploader(
    "📤 Загрузите изображение плана, фасада или интерьера (JPG / PNG)",
    type=["jpg", "jpeg", "png"],
)

# ============================================================
# ФУНКЦИИ СИНТЕЗА
# ============================================================
def extract_geometry(gray: np.ndarray, size: int, low: int, high: int) -> np.ndarray:
    """Возвращает матрицу (size × size) с силой геометрии (границ) 0..1."""
    # Приводим к квадрату для стабильного сканирования
    img = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    # Canny — детектор границ
    edges = cv2.Canny(img, low, high)
    # Небольшое размытие, чтобы границы давали мягкие тона
    edges = cv2.GaussianBlur(edges, (3, 3), 0)
    return edges.astype(np.float32) / 255.0


def image_to_sound(geometry: np.ndarray, sample_rate: int, pixel_duration_ms: float,
                   freq_min: float, freq_max: float, waveform: str) -> np.ndarray:
    """
    Сонификация: каждый столбец изображения -> короткий тон.
    Y-координата (сверху вниз) -> высота тона (сверху — высокие, снизу — низкие).
    X-координата -> время (слева направо).
    """
    h, w = geometry.shape
    pixel_samples = int(sample_rate * pixel_duration_ms / 1000.0)
    if pixel_samples < 8:
        pixel_samples = 8

    audio = np.zeros(w * pixel_samples, dtype=np.float32)

    # Предвычисляем фазу для непрерывности
    for x in range(w):
        column = geometry[:, x]
        col_energy = float(np.sum(column))
        if col_energy < 1e-6:
            continue

        # Взвешенная по яркости средняя Y-позиция линий в столбце
        ys = np.arange(h, dtype=np.float32)
        # сверху (y=0) -> высокие частоты, снизу (y=h) -> низкие
        norm_y = 1.0 - (ys / max(h - 1, 1))   # 0 внизу, 1 сверху
        weights = column / (col_energy + 1e-9)
        avg_norm_y = float(np.sum(weights * norm_y))

        # Частота по экспоненциальной шкале для музыкальности
        freq = freq_min * (freq_max / freq_min) ** avg_norm_y

        # Амплитуда ~ плотность геометрии в столбце
        amp = min(1.0, col_energy / (h * 0.35))
        amp = float(np.clip(amp, 0.0, 1.0))

        t = np.arange(pixel_samples, dtype=np.float32) / sample_rate
        phase = 2 * np.pi * freq * t

        if waveform.startswith("Синус"):
            wave = np.sin(phase)
        elif waveform.startswith("Прямоуг"):
            wave = np.sign(np.sin(phase))
        elif waveform.startswith("Пилообр"):
            frac = (freq * t) % 1.0
            wave = 2.0 * frac - 1.0
        else:  # Треугольная
            frac = (freq * t) % 1.0
            wave = 4.0 * np.abs(frac - 0.5) - 1.0

        # Плавная огибающая (окно Ханна) для избежания щелчков
        env = np.hanning(pixel_samples).astype(np.float32)
        audio[x * pixel_samples:(x + 1) * pixel_samples] = wave * amp * env

    # Нормализация
    peak = float(np.max(np.abs(audio))) if audio.size else 1.0
    if peak > 0:
        audio = audio / peak * 0.9
    return audio.astype(np.float32)


def enforce_duration(audio: np.ndarray, sr: int, target_sec: float) -> np.ndarray:
    """Растягивает/сжимает массив по времени до target_sec (линейная интерполяция)."""
    target_len = int(sr * target_sec)
    if audio.size == 0:
        return np.zeros(target_len, dtype=np.float32)
    if target_len <= 0:
        return audio
    x_old = np.linspace(0, 1, audio.size, endpoint=False)
    x_new = np.linspace(0, 1, target_len, endpoint=False)
    resampled = np.interp(x_new, x_old, audio).astype(np.float32)
    # повторная нормализация
    peak = float(np.max(np.abs(resampled)))
    if peak > 0:
        resampled = resampled / peak * 0.9
    return resampled


def to_wav_bytes(audio: np.ndarray, sr: int) -> io.BytesIO:
    """WAV в оперативной памяти."""
    buf = io.BytesIO()
    pcm = np.int16(np.clip(audio, -1.0, 1.0) * 32767)
    wavfile.write(buf, sr, pcm)
    buf.seek(0)
    return buf


def describe_audio(audio: np.ndarray, sr: int) -> dict:
    """Анализ: преобладание высоких/низких, насыщенность спектра."""
    if audio.size == 0:
        return {"low": 0, "high": 0, "richness": 0, "peak": 0}
    # FFT
    n = min(len(audio), sr * 4)
    spectrum = np.abs(np.fft.rfft(audio[:n] * np.hanning(n)))
    freqs = np.fft.rfftfreq(n, 1 / sr)
    total = float(np.sum(spectrum) + 1e-9)
    low_band = float(np.sum(spectrum[freqs < 1000]) / total)
    high_band = float(np.sum(spectrum[freqs >= 1000]) / total)
    # Насыщенность спектра — кол-во значимых пиков
    thr = np.mean(spectrum) + np.std(spectrum)
    richness = int(np.sum(spectrum > thr))
    return {
        "low": low_band * 100,
        "high": high_band * 100,
        "richness": richness,
        "peak": float(np.max(np.abs(audio))),
    }


# ============================================================
# ОСНОВНОЙ КОНТЕНТ
# ============================================================
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

# Чтение изображения
pil_img = Image.open(uploaded).convert("RGB")
img_rgb = np.array(pil_img)
gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

# Извлечение геометрии
geometry = extract_geometry(gray, scan_size, canny_low, canny_high)

# Синтез
audio = image_to_sound(
    geometry, sample_rate, pixel_duration_ms,
    freq_min, freq_max, waveform,
)
audio = enforce_duration(audio, sample_rate, total_duration)

# Анализ
stats = describe_audio(audio, sample_rate)

# Верхний блок: две колонки
col_left, col_right = st.columns(2, gap="large")

# ----- ЛЕВАЯ: Осциллограмма + характеристики -----
with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🌊 Волновая форма</div>', unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(6.2, 2.9), dpi=110)
    fig.patch.set_alpha(0)
    ax.set_facecolor((1, 1, 1, 0.0))
    # Отрисовать только часть для наглядности (до 10 сек)
    vis_len = min(len(audio), sample_rate * 10)
    t_axis = np.arange(vis_len) / sample_rate
    ax.plot(t_axis, audio[:vis_len], color="#9b87c9", linewidth=0.7)
    ax.fill_between(t_axis, audio[:vis_len], color="#c8b6e2", alpha=0.35)
    ax.set_xlabel("Время, с", color="#7a7a92", fontsize=9)
    ax.set_ylabel("Амплитуда", color="#7a7a92", fontsize=9)
    ax.tick_params(colors="#8a8aa0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#d8d2e6")
    ax.grid(True, color="#ece7f5", linewidth=0.6)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Текстовые характеристики
    tone = "высоких" if stats["high"] > stats["low"] else "низких"
    st.markdown(
        f'<div style="margin-top:0.4rem;">'
        f'<span class="stat-pill">🎼 Преобладание: {tone} частот</span>'
        f'<span class="stat-pill">🔊 Низкие: {stats["low"]:.1f}%</span>'
        f'<span class="stat-pill">🎵 Высокие: {stats["high"]:.1f}%</span>'
        f'<span class="stat-pill">✨ Спектральная насыщенность: {stats["richness"]} пиков</span>'
        f'<span class="stat-pill">⏱️ Длительность: {total_duration:.0f} с</span>'
        f'<span class="stat-pill">📈 Пик: {stats["peak"]:.2f}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ----- ПРАВАЯ: Изображение + скачивание + плеер -----
with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">🖼️ Изображение и результат</div>', unsafe_allow_html=True)

    if show_contours:
        edges_vis = (geometry * 255).astype(np.uint8)
        edges_rgb = cv2.cvtColor(edges_vis, cv2.COLOR_GRAY2RGB)
        overlay = cv2.addWeighted(img_rgb, 0.55, edges_rgb, 0.85, 0)
        preview = overlay
    else:
        preview = img_rgb

    st.image(preview, use_container_width=True,
             caption="Контуры геометрии, использованные для сонификации"
             if show_contours else "Исходное изображение")

    # WAV + плеер
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
# НИЖНИЙ БЛОК: Профиль плотности геометрических линий
# ============================================================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-title">📊 Профиль плотности геометрических линий</div>', unsafe_allow_html=True)

# Профиль: суммарная энергия границ по X (слева-направо)
x_profile = np.sum(geometry, axis=0)
x_profile_norm = x_profile / (np.max(x_profile) + 1e-9)

# Профиль по Y (сверху-вниз)
y_profile = np.sum(geometry, axis=1)
y_profile_norm = y_profile / (np.max(y_profile) + 1e-9)

fig2, axes = plt.subplots(1, 2, figsize=(12, 3), dpi=110)
fig2.patch.set_alpha(0)
for ax in axes:
    ax.set_facecolor((1, 1, 1, 0.0))
    for spine in ax.spines.values():
        spine.set_color("#d8d2e6")
    ax.tick_params(colors="#8a8aa0", labelsize=8)
    ax.grid(True, color="#ece7f5", linewidth=0.6)

axes[0].fill_between(np.arange(len(x_profile_norm)), x_profile_norm,
                     color="#b6d8e8", alpha=0.55)
axes[0].plot(x_profile_norm, color="#7fb8d8", linewidth=1.2)
axes[0].set_title("Плотность линий по горизонтали (X → время)",
                  color="#5a5a78", fontsize=10, fontfamily="serif")
axes[0].set_xlabel("Сканируемая колонка (слева → направо)", color="#8a8aa0", fontsize=9)
axes[0].set_ylabel("Плотность", color="#8a8aa0", fontsize=9)

axes[1].fill_between(np.arange(len(y_profile_norm)), y_profile_norm,
                     color="#e8c6d8", alpha=0.55)
axes[1].plot(y_profile_norm, color="#d8a6c0", linewidth=1.2)
axes[1].invert_yaxis()
axes[1].set_title("Плотность линий по вертикали (Y → высота тона)",
                  color="#5a5a78", fontsize=10, fontfamily="serif")
axes[1].set_xlabel("Плотность", color="#8a8aa0", fontsize=9)
axes[1].set_ylabel("Сканируемая строка (сверху вниз)", color="#8a8aa0", fontsize=9)

fig2.tight_layout()
st.pyplot(fig2, use_container_width=True)
plt.close(fig2)

st.markdown(
    '<p style="color:#8a8aa0; font-size:0.85rem; margin-top:0.4rem;">'
    'Каждый пик соответствует скоплению контуров — именно эти места становятся '
    'акцентными звуковыми событиями в композиции.'
    '</p>',
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
