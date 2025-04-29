from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import google.generativeai as genai
import speech_recognition as sr
import threading
import base64
import io
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 1.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
    system_instruction="Whatever prompt you get , simplify it maximum without losing information and give response , even if it is a question or anything ,, no question is personally to you so just simplify the sentence and do not exceed more than 18 words if possible. DONT CHANGE THE PERSPECTIVE OF SPEECH. APPLICABLE TO ALL TYPES OF LANGUAGE YOU GET, IF YOU GET A PROMPT IN ONE LANGUAGE RESPONFD IN THE SAME LANGUAGE, DONOT ANSWER EVEN IF ITS A QUESTION. for example if u get a prompt :- WHO is the 47th president of amera, reply with \"Whose the 47th president of America\"",
)

recognizer = sr.Recognizer()


def process_audio_data(audio_data):
    try:
        audio = base64.b64decode(audio_data)
        audio_segment = AudioSegment.from_file(io.BytesIO(audio), format="webm")
        audio_file = io.BytesIO()
        audio_segment.export(audio_file, format="wav")
        audio_file.seek(0)
        return audio_file
    except Exception as e:
        print(f"Error processing audio data: {e}")
        return None


@socketio.on("audio_data")
def handle_audio_data(data):
    audio_file = process_audio_data(data["audio"])
    if audio_file is None:
        emit("simplified_text", {"text": "Error processing audio data"})
        return

    language_code = data.get("language", "en-US")  # Default to English if no language is specified
    is_continuous = data.get("continuous", False)  # Check if this is from hold-to-speak

    try:
        with sr.AudioFile(audio_file) as source:
            # If continuous audio, adjust for longer audio
            if is_continuous:
                print("Processing continuous audio input from hold-to-speak")
                # Set energy threshold higher for continuous audio to filter background noise
                recognizer.energy_threshold = 300
                # Set dynamic energy threshold to adjust for ambient noise
                recognizer.dynamic_energy_threshold = True
            
            audio = recognizer.record(source)
            try:
                transcription = recognizer.recognize_google(audio, language=language_code)
                print(f"Detected text: {transcription} (Language: {language_code}, Continuous: {is_continuous})")
                
                # Process with Gemini model
                chat_session = model.start_chat(history=[{"role": "user", "parts": [transcription]}])
                response = chat_session.send_message(transcription)
                simplified_text = response.text
                
                # Log the simplified text for debugging
                print(f"Simplified text: {simplified_text}")
                
                # Send result back to client
                emit("simplified_text", {"text": simplified_text})
            except sr.UnknownValueError:
                emit("simplified_text", {"text": "Could not understand audio"})
            except sr.RequestError as e:
                emit("simplified_text", {"text": f"Error: {e}"})
    except Exception as e:
        print(f"Unexpected error processing audio: {str(e)}")
        emit("simplified_text", {"text": f"Error processing audio: {str(e)}"})


def text_input_and_simplify():
    while True:
        try:
            user_input = input("Enter text to simplify: ").strip()
            if not user_input:
                print("Please enter some text to simplify.")
                continue
                
            chat_session = model.start_chat(history=[])
            response = chat_session.send_message(user_input)
            simplified_text = response.text
            print(f"Simplified text: {simplified_text}")
            socketio.emit("simplified_text", {"text": simplified_text})
        except Exception as e:
            print(f"Error: {str(e)}")
            continue


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    threading.Thread(target=text_input_and_simplify, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
