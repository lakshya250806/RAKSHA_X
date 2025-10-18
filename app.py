from flask import Flask, render_template, request, redirect, url_for, jsonify
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
import google.generativeai as genai
from twilio.rest import Client

app = Flask(__name__)

# =============== FLASK SETUP ===============
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =============== TWILIO SETUP ===============
# Replace these with your credentials
account_sid = ""
auth_token = ""
twilio_whatsapp = "whatsapp:+14155238886"   # Sandbox number
my_whatsapp = "whatsapp:+918595092765"
client = Client(account_sid, auth_token)

# =============== GEMINI SETUP ===============
GEMINI_API_KEY = ""  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')

# =============== YAMNET MODEL SETUP ===============
# Load YAMNet model (load once at startup)
try:
    print("Loading YAMNet model...")
    model = hub.load('https://tfhub.dev/google/yamnet/1')
    print("YAMNet model loaded successfully")
except Exception as e:
    print(f"Error loading YAMNet model: {e}")
    model = None

# Load class labels
class_map = []
try:
    url = 'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
    if not os.path.exists('yamnet_class_map.csv'):
        print("Downloading YAMNet class map...")
        urllib.request.urlretrieve(url, 'yamnet_class_map.csv')
    
    with open('yamnet_class_map.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            class_map.append(row['display_name'])
    print(f"Loaded {len(class_map)} class labels")
except Exception as e:
    print(f"Error loading class map: {e}")
    class_map = []

danger_sounds = ["Scream", "Gunshot", "Explosion", "Shout", "Crying", "Fireworks"]
keywords = ["help", "save me", "leave me", "don't touch", "Stay away"]

# =============== ROUTES ====================

@app.route('/')
def index():
    """Main landing page with navigation to all features"""
    return render_template('index.html')

@app.route('/game')
def game():
    """Street safety navigation game"""
    return render_template('game.html')

@app.route('/detect', methods=['GET', 'POST'])
def detect():
    """Audio detection using YAMNet"""
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
            try:
                wav_data, sr = sf.read(filepath)
                if len(wav_data.shape) > 1:
                    wav_data = np.mean(wav_data, axis=1)
                if sr != 16000:
                    wav_data = librosa.resample(wav_data, orig_sr=sr, target_sr=16000)
                    sr = 16000
                wav_data = tf.convert_to_tensor(wav_data, dtype=tf.float32)
                
                if model is not None:
                    scores, embeddings, spectrogram = model(wav_data)
                    scores = scores.numpy()
                    mean_scores = scores.mean(axis=0)
                    top_indices = mean_scores.argsort()[-5:][::-1]
                    results = [(class_map[i] if i < len(class_map) else f"Class_{i}", f"{mean_scores[i]*100:.2f}") for i in top_indices]
                    detected_labels = [class_map[i] if i < len(class_map) else f"Class_{i}" for i in top_indices]
                else:
                    # Fallback if YAMNet model is not available
                    results = [("Audio Analysis", "Model unavailable")]
                    detected_labels = ["Unknown"]
                    
            except Exception as e:
                print(f"Audio processing error: {e}")
                results = [("Audio Analysis", "Processing failed")]
                detected_labels = ["Unknown"]
            
            # --- Vosk Speech-to-Text ---
            speech_text = ""
            try:
                sf.write("temp_pcm.wav", wav_data.numpy(), 16000, subtype='PCM_16')
                wf = wave.open("temp_pcm.wav", "rb")
                vosk_model_path = "vosk-model-small-en-us-0.15"
                
                # Check if model exists, if not try to download it
                if not os.path.exists(vosk_model_path):
                    print("Vosk model not found, attempting to download...")
                    import zipfile
                    import requests
                    try:
                        vosk_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
                        r = requests.get(vosk_url, timeout=30)
                        with open("vosk_model.zip", "wb") as f:
                            f.write(r.content)
                        with zipfile.ZipFile("vosk_model.zip", "r") as zip_ref:
                            zip_ref.extractall(".")
                        print("Vosk model downloaded successfully")
                    except Exception as e:
                        print(f"Failed to download Vosk model: {e}")
                        speech_text = "Speech recognition unavailable"
                        wf.close()
                        try:
                            os.remove("temp_pcm.wav")
                        except:
                            pass
                        # Continue without speech recognition
                        yamnet_alert = any(label in danger_sounds for label in detected_labels)
                        stt_alert = False  # No speech recognition available
                        if yamnet_alert or stt_alert:
                            alert = True
                        if alert:
                            return redirect(url_for('sos', filename=filename))
                        return render_template('detect.html', results=results, alert=alert, speech_text=speech_text)
                
                # Load Vosk model
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
                wf.close()
                
            except Exception as e:
                print(f"Speech recognition error: {e}")
                speech_text = "Speech recognition failed"
                try:
                    wf.close()
                except:
                    pass
            
            # Determine if alert should be triggered
            yamnet_alert = any(label in danger_sounds for label in detected_labels) if detected_labels else False
            stt_alert = any(k in speech_text.lower() for k in keywords) if speech_text else False
            
            # If both models failed, provide a manual option
            if not results or results[0][0] == "Audio Analysis":
                # Show manual analysis option
                pass
            else:
                if yamnet_alert or stt_alert:
                    alert = True
            
            # Clean up temporary files
            try:
                os.remove("temp_pcm.wav")
            except Exception:
                pass
                
            if alert:
                return redirect(url_for('sos', filename=filename))
    
    return render_template('detect.html', results=results, alert=alert, speech_text=speech_text)

@app.route('/sos')
@app.route('/sos/<filename>')
def sos(filename=None):
    """SOS page with emergency alert and WhatsApp button"""
    return render_template('sos.html', filename=filename)

@app.route('/send_sos/<filename>')
def send_sos(filename):
    """Send WhatsApp SOS message"""
    message = client.messages.create(
        body="🚨 SOS Alert! The girl is in danger!",
        from_=twilio_whatsapp,
        to=my_whatsapp
    )
    return f"<h2>✅ SOS Sent! SID: {message.sid}</h2>"

@app.route('/chatbot')
def chatbot():
    """Mental health chatbot page"""
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Chatbot API endpoint"""
    try:
        user_message = request.json.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Mental health focused system prompt
        system_prompt = """You are Cosmic Crisis AI Bestie — a proactive safety and emotional support chatbot.
Your mission: protect, comfort, and guide users in unsafe or stressful situations.

⚡ Response Limits:

Only respond to: safety concerns, emotional trauma, mental health stress, or greetings (hi/hello/check-in).

For unrelated topics (coding, math, random questions), politely decline:
“I’m designed specifically for emotional safety, trauma support, and mental health. I can’t answer that.”

Modes of Response

[SAFETY MODE]

Triggered by: danger/fear words → "unsafe", "help now", "track me", "alert guardians".

Clear, direct steps: SOS, share location, move to safe spot.

Calm but firm.

30–50 words only.

Example:

"SOS activated. Stay visible, move toward lighted areas. Sharing your location now with trusted contacts. Breathe steady — help is on the way."

[SUPPORT MODE]

Triggered by: stress/emotion words → "scared", "anxious", "lonely", "worthless".

Validate feelings + give one coping method (breathing, grounding, affirmation).

Warm, empathetic, short.

Example:

"I hear your fear. Let’s slow down: inhale 4, hold 4, exhale 6. Repeat twice. You are safe with me in this moment."

[FRIENDLY MODE]

Triggered by: casual greetings/tips → "hi", "motivate me", "check in".

Positive, light, uplifting, short.

Example:

"Hey, friend 🌸. I’m here with you. You’ve got this — let’s keep moving forward together."

Rules

Always 30–50 words.

Emergency → actionable steps only.

Emotional support → empathy + one grounding action.

Friendly → warm and short.

Anything off-topic → politely decline...."""
        
        # Combine system prompt with user message
        full_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nMindCare:"
        
        # Generate response using Gemini
        response = gemini_model.generate_content(full_prompt)
        bot_response = response.text
        
        return jsonify({'response': bot_response})
    
    except Exception as e:
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/crisis-resources')
def crisis_resources():
    """Crisis resources API endpoint"""
    resources = {
        'crisis_lines': [
            {'name': 'National Suicide Prevention Lifeline', 'number': '100', 'country': 'INdia'},
            {'name': 'Crisis Text Line', 'number': 'Text HOME to 10101', 'country': 'India'},
            {'name': 'International Association for Suicide Prevention', 'url': 'https://www.iasp.info/resources/Crisis_Centres/', 'country': 'International'}
        ],
        'resources': [
            'If you\'re in immediate danger, call emergency services (102, 101, etc.)',
            'Consider reaching out to a trusted friend or family member',
            'Contact your local mental health services',
            'Visit your nearest emergency room if you\'re having thoughts of self-harm'
        ]
    }
    return jsonify(resources)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
