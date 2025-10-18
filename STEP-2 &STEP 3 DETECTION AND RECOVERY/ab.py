import streamlit as st
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import soundfile as sf
import tempfile
import urllib.request
import librosa
import csv

# Load YAMNet model
@st.cache_resource
def load_model():
    model = hub.load('https://tfhub.dev/google/yamnet/1')
    return model

# Load class labels
@st.cache_data
def load_class_map():
    url = 'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
    urllib.request.urlretrieve(url, 'yamnet_class_map.csv')
    class_map = []
    with open('yamnet_class_map.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            class_map.append(row['display_name'])
    return class_map

model = load_model()
class_map = load_class_map()

# Streamlit UI
st.title("🔊 Smart Audio Detection System")
st.write("Detects screams, gunshots, explosions, and other risky sounds in real-time.")

uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg"])

if uploaded_file:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        tmpfile.write(uploaded_file.read())
        tmp_path = tmpfile.name

    # Load audio
        wav_data, sr = sf.read(tmp_path)
        if len(wav_data.shape) > 1:  # stereo to mono
            wav_data = np.mean(wav_data, axis=1)

        # Resample to 16kHz (required for YAMNet)
        if sr != 16000:
            wav_data = librosa.resample(wav_data, orig_sr=sr, target_sr=16000)
            sr = 16000

        # Convert to tensor
        wav_data = tf.convert_to_tensor(wav_data, dtype=tf.float32)

    # Run model
    scores, embeddings, spectrogram = model(wav_data)
    scores = scores.numpy()

    mean_scores = scores.mean(axis=0)
    top_indices = mean_scores.argsort()[-5:][::-1]

    st.subheader("Top Detected Sounds:")
    for i in top_indices:
        st.write(f"🔹 {class_map[i]} ({mean_scores[i]*100:.2f}%)")

    # Alert conditions
    danger_sounds = ["Scream", "Gunshot", "Explosion", "Shout", "Crying", "Fireworks"]

    detected_labels = [class_map[i] for i in top_indices]
    if any(label in danger_sounds for label in detected_labels):
        st.error("🚨 ALERT! Dangerous sound detected!")
    else:
        st.success("✅ Environment Safe")
