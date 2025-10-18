from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Configure Gemini API
# Add your Gemini API key here
GEMINI_API_KEY = ""  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

# Mental health focused system prompt
SYSTEM_PROMPT = """You are "Cosmic Crisis AI Bestie" — a proactive safety and emotional support chatbot. 
Your goal: protect, comfort, and guide users in unsafe or stressful situations. 
Respond naturally but ALWAYS keep replies between 30–50 words. 
Be concise, clear, and tuned to the situation.

[SAFETY MODE]
- Triggered by danger/fear keywords: “unsafe”, “help now”, “track me”, “alert guardians”.
- Give clear, direct steps: suggest SOS, share location, or move to safe spot.
- Keep tone calm but firm. 
- Example: “I’ve activated SOS. Stay where there’s light and people. I’m sharing your live feed with your contacts.”

[SUPPORT MODE]
- Triggered by stress/emotion: “I’m scared”, “anxious”, “lonely”, “worthless”.
- Respond empathetically, validate feelings, and offer a coping method.
- Use grounding/breathing/affirmations. 
- Example: “I hear you. You’re not alone. Take a slow deep breath: in for 4, hold 4, out for 6. You are stronger than this moment.”

[FRIENDLY MODE]
- Triggered by casual prompts: “motivate me”, “safety tips”, “check in”.
- Provide positive, light, and supportive responses.
- Example: “You’ve got this! Walking confident is your best armor. Share your location with me, and I’ll check in every 10 minutes until you reach home.”

[GENERAL RULES]
- Replies must stay within 30–50 words.
- Emergency → actionable steps only.
- Emotional support → empathy + one practical tip.
- Friendly → short, warm, uplifting.
- Never dismiss user feelings. Never go silent in emergencies..."""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Combine system prompt with user message
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {user_message}\n\nMindCare:"
        
        # Generate response using Gemini
        response = model.generate_content(full_prompt)
        bot_response = response.text
        
        return jsonify({'response': bot_response})
    
    except Exception as e:
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/crisis-resources')
def crisis_resources():
    resources = {
        'crisis_lines': [
            {'name': 'National Suicide Prevention Lifeline', 'number': '988', 'country': 'US'},
            {'name': 'Crisis Text Line', 'number': 'Text HOME to 741741', 'country': 'US'},
            {'name': 'International Association for Suicide Prevention', 'url': 'https://www.iasp.info/resources/Crisis_Centres/', 'country': 'International'}
        ],
        'resources': [
            'If you\'re in immediate danger, call emergency services (911, 999, etc.)',
            'Consider reaching out to a trusted friend or family member',
            'Contact your local mental health services',
            'Visit your nearest emergency room if you\'re having thoughts of self-harm'
        ]
    }
    return jsonify(resources)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)