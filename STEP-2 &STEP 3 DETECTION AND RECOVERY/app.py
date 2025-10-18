import streamlit as st
import numpy as np
import soundfile as sf
import tensorflow_hub as hub
import librosa

st.title("Audio Event Detection (YAMNet)")

uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

if uploaded_file is not None:
    # Read audio file
    wav, sr = sf.read(uploaded_file)
    if sr != 16000:
        wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)
        sr = 16000
    if wav.ndim > 1:
        wav = np.mean(wav, axis=1)
    wav = wav.astype(np.float32)

    # Load YAMNet model
    model = hub.load('https://tfhub.dev/google/yamnet/1')
    scores, embeddings, spectrogram = model(wav)
    scores = np.array(scores)
    pred_idx = np.argmax(scores.mean(axis=0))
    loudness = np.abs(wav).mean()

    st.write(f"Predicted index: {pred_idx}")
    st.write(f"Loudness: {loudness:.4f}")
    if loudness > 0.02:
        st.error("ALERT: Loud event detected")
    else:
        st.success("Not a loud event")
