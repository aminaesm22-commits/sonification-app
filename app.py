import streamlit as st
import numpy as np
from scipy.io import wavfile
from PIL import Image
import io

# Настройка страницы
st.set_page_config(page_title="Image to Sound", page_icon="🎵", layout="centered")

st.title("🎵 Генератор звука из изображения")
st.write("Загрузите изображение — приложение просканирует пиксели и создаст WAV-файл.")

# --- Боковая панель с параметрами ---
st.sidebar.header("⚙️ Параметры синтеза")

sample_rate = st.sidebar.slider(
    "Частота дискретизации (Гц)", 8000, 44100, 22050, step=1000
)

duration_per_pixel = st.sidebar.slider(
    "Длительность одного пикселя (сек)", 0.0001, 0.01, 0.001, step=0.0001,
    format="%.4f"
)

min_freq = st.sidebar.slider("Минимальная частота (Гц)", 50, 500, 100)
max_freq = st.sidebar.slider("Максимальная частота (Гц)", 500, 5000, 2000)

num_pixels = st.sidebar.slider(
    "Количество сканируемых пикселей", 100, 20000, 4000, step=100,
    help="Изображение будет линейно преобразовано в последовательность из N пикселей"
)

waveform = st.sidebar.selectbox(
    "Форма волны", ["sine", "square", "sawtooth", "triangle"]
)

max_duration = st.sidebar.slider(
    "Максимальная длина аудио (сек)", 1, 60, 20
)

# --- Загрузка изображения ---
uploaded_file = st.file_uploader(
    "Загрузите изображение", type=["png", "jpg", "jpeg", "bmp", "webp"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("L")  # в оттенки серого
    st.image(image, caption="Загруженное изображение", use_container_width=True)

    # Преобразуем изображение в массив
    img_array = np.array(image, dtype=np.float32)  # значения 0..255

    # Линейно "разворачиваем" изображение и уменьшаем до num_pixels через интерполяцию
    flat = img_array.flatten()
    if len(flat) > num_pixels:
        # Прореживание с усреднением
        idx = np.linspace(0, len(flat) - 1, num_pixels).astype(int)
        samples = flat[idx]
    else:
        samples = flat

    # Нормируем в диапазон 0..1
    samples = samples - samples.min()
    if samples.max() > 0:
        samples = samples / samples.max()

    # Яркость -> частота
    freqs = min_freq + samples * (max_freq - min_freq)

    # --- Генерация звука ---
    samples_per_pixel = max(1, int(sample_rate * duration_per_pixel))
    total_samples = num_pixels * samples_per_pixel

    # Ограничиваем длину
    max_samples = sample_rate * max_duration
    if total_samples > max_samples:
        total_samples = max_samples

    t = np.arange(total_samples) / sample_rate
    audio = np.zeros(total_samples, dtype=np.float32)

    # Фазовая аккумуляция для корректной генерации без щелчков
    phase = 0.0

    for i in range(total_samples):
        px_idx = min(i // samples_per_pixel, num_pixels - 1)
        f = freqs[px_idx]
        phase += 2 * np.pi * f / sample_rate

        if waveform == "sine":
            val = np.sin(phase)
        elif waveform == "square":
            val = 1.0 if np.sin(phase) >= 0 else -1.0
        elif waveform == "sawtooth":
            val = 2.0 * ((phase / (2 * np.pi)) % 1.0) - 1.0
        elif waveform == "triangle":
            val = 2.0 * abs(2.0 * ((phase / (2 * np.pi)) % 1.0) - 1.0) - 1.0
        else:
            val = 0.0

        audio[i] = val

    # --- Нормализация и огибающая (убираем щелчки на краях) ---
    fade_len = min(int(sample_rate * 0.01), total_samples // 10)
    if fade_len > 0:
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        audio[:fade_len] *= fade_in
        audio[-fade_len:] *= fade_out

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.9  # запас 0.9 от клиппинга

    # --- Сохранение в WAV через scipy ---
    wav_buffer = io.BytesIO()
    wavfile.write(wav_buffer, sample_rate, (audio * 32767).astype(np.int16))
    wav_buffer.seek(0)

    st.success(f"✅ Аудио сгенерировано: {total_samples / sample_rate:.2f} сек, "
               f"{len(samples)} пикселей, {sample_rate} Гц")

    # Плеер и скачивание
    st.audio(wav_buffer, format="audio/wav")

    st.download_button(
        label="💾 Скачать WAV",
        data=wav_buffer,
        file_name="image_sound.wav",
        mime="audio/wav"
    )

    # Предпросмотр профиля яркости
    with st.expander("📊 Профиль яркости пикселей (первые 500)"):
        st.line_chart(samples[:500])
else:
    st.info("👆 Загрузите изображение, чтобы начать")