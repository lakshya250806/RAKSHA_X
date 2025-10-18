from flask import Flask, render_template, request, render_template_string, redirect, url_for
import numpy as np
import tensorflow_hub as hub
import soundfile as sf
import tempfile
import urllib.request
import csv
import os
import wave
import json
from vosk import Model, KaldiRecognizer
import librosa
import tensorflow as tf


app = Flask(__name__)

# =============== FLASK SETUP ===============
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =============== TWILIO SETUP ===============
# Replace these with your credentials
from twilio.rest import Client
account_sid = ""
auth_token = ""
twilio_whatsapp = "whatsapp:+14155238886"   # Sandbox number
my_whatsapp = "whatsapp:+918595092765"
client = Client(account_sid, auth_token)

# Load YAMNet model
PUBLIC_URL = "https://dry-forks-wait.loca.lt"  # <-- Change this to your actual localtunnel URL
model = hub.load('https://tfhub.dev/google/yamnet/1')

# Load class labels
url = 'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
if not os.path.exists('yamnet_class_map.csv'):
    urllib.request.urlretrieve(url, 'yamnet_class_map.csv')
class_map = []
with open('yamnet_class_map.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        class_map.append(row['display_name'])

danger_sounds = ["Scream", "Gunshot", "Explosion", "Shout", "Crying", "Fireworks"]
keywords = ["help", "save me", "leave me", "don't touch" , "Stay away"]

HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Smart Audio Detection System</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: linear-gradient(135deg, #ece9e6, #ffffff);
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .container {
      background: #fff;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.15);
      text-align: center;
      width: 450px;
    }
    h2 {
      margin-bottom: 15px;
      color: #333;
    }
    form {
      margin: 20px 0;
    }
    input[type=file] {
      margin: 10px 0;
    }
    input[type=submit] {
      background: #4CAF50;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 14px;
    }
    input[type=submit]:hover {
      background: #45a049;
    }
    ul {
      list-style: none;
      padding: 0;
    }
    li {
      background: #f4f4f4;
      margin: 5px 0;
      padding: 8px;
      border-radius: 6px;
      text-align: left;
    }
    .alert {
      color: red;
      font-weight: bold;
      font-size: 18px;
    }
    .safe {
      color: green;
      font-weight: bold;
      font-size: 18px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h2>🔊 Smart Audio Detection System</h2>
    <p>Detects risky sounds and emergency phrases in real-time.</p>

    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept="audio/*" required>
      <br>
      <input type="submit" value="Upload & Analyze">
    </form>

    {% if results %}
      <h3>Top Detected Sounds:</h3>
      <ul>
        {% for label, score in results %}
          <li>{{ label }} ({{ score }}%)</li>
        {% endfor %}
      </ul>

      <h3>Speech Detected:</h3>
      <p><b>{{ speech_text }}</b></p>

      {% if alert %}
        <p class="alert">🚨 ALERT! Emergency detected!</p>
        <script>
          // redirect to SOS page after 2 seconds
          setTimeout(function(){
            window.location.href = "/sos";
          }, 2000);
        </script>
      {% else %}
        <p class="safe">✅ Environment Safe</p>
      {% endif %}
    {% endif %}
  </div>
</body>
'''


# =============== ROUTES ====================


# SOS page route: shows audio and SOS button
@app.route("/sos/<filename>")
def sos(filename):
  return render_template("sos.html", filename=filename)

# WhatsApp SOS sending route
@app.route("/send_sos/<filename>")
def send_sos(filename):
    # Only send a text message, no media
    message = client.messages.create(
        body="🚨 SOS Alert! The girl is in danger!",
        from_=twilio_whatsapp,
        to=my_whatsapp
    )
    return f"<h2>✅ SOS Sent! SID: {message.sid}</h2>"



@app.route('/', methods=['GET', 'POST'])
def index():
  results = None
  alert = False
  speech_text = ""
  filename = None
  if request.method == 'POST':
    file = request.files['file']
    if file:
      # Save uploaded file for evidence
      filename = file.filename
      filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
      file.save(filepath)
      # --- YAMNet ---
      wav_data, sr = sf.read(filepath)
      if len(wav_data.shape) > 1:
        wav_data = np.mean(wav_data, axis=1)
      if sr != 16000:
        wav_data = librosa.resample(wav_data, orig_sr=sr, target_sr=16000)
        sr = 16000
      wav_data = tf.convert_to_tensor(wav_data, dtype=tf.float32)
      scores, embeddings, spectrogram = model(wav_data)
      scores = scores.numpy()
      mean_scores = scores.mean(axis=0)
      top_indices = mean_scores.argsort()[-5:][::-1]
      results = [(class_map[i], f"{mean_scores[i]*100:.2f}") for i in top_indices]
      detected_labels = [class_map[i] for i in top_indices]
      # --- Vosk Speech-to-Text ---
      sf.write("temp_pcm.wav", wav_data.numpy(), 16000, subtype='PCM_16')
      wf = wave.open("temp_pcm.wav", "rb")
      vosk_model_path = "vosk-model-small-en-us-0.15"
      if not os.path.exists(vosk_model_path):
        import zipfile
        import requests
        vosk_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        r = requests.get(vosk_url)
        with open("vosk_model.zip", "wb") as f:
          f.write(r.content)
        with zipfile.ZipFile("vosk_model.zip", "r") as zip_ref:
          zip_ref.extractall(".")
      vosk_model = Model(vosk_model_path)
      rec = KaldiRecognizer(vosk_model, 16000)
      results_stt = []
      while True:
        data = wf.readframes(4000)
        if len(data) == 0:
          break
        if rec.AcceptWaveform(data):
          results_stt.append(json.loads(rec.Result()))
      final = json.loads(rec.FinalResult())
      results_stt.append(final)
      speech_text = " ".join([r.get("text", "") for r in results_stt])
      yamnet_alert = any(label in danger_sounds for label in detected_labels)
      stt_alert = any(k in speech_text.lower() for k in keywords)
      if yamnet_alert or stt_alert:
        alert = True
      try:
        os.remove("temp_pcm.wav")
      except Exception:
        pass
      if alert:
        return redirect(url_for('sos', filename=filename))
  return render_template_string(HTML, results=results, alert=alert, speech_text=speech_text)

if __name__ == '__main__':
    app.run(debug=True)
