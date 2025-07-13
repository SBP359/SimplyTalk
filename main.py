from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import google.generativeai as genai
import speech_recognition as sr
import threading
import base64
import io
import re
from pydub import AudioSegment
import json
import sys

app = Flask(__name__)
CORS(app)

# Use eventlet only if available and compatible, else fallback to threading for Python 3.13+
if sys.version_info < (3, 12):
    async_mode = 'eventlet'
else:
    async_mode = 'threading'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode)

# api_key = os.getenv("GOOGLE_API_KEY")  # Use environment variable for API key
api_key = "api_key_here"  # Replace with your actual API key
genai.configure(api_key=api_key)

# Directory for storing GIF files
GIF_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'gif')

# Path to persistent keyword-to-gif mapping
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'gif_mapping.json')

generation_config = {
    "temperature": 1.5,
    "top_p": 0.98,
    "top_k": 40,
    "max_output_tokens": 8192,
}

# Define the system instruction separately
system_instruction = "Whatever prompt you get, simplify it maximum without losing information and give response, even if it is a question or anything, no question is personally to you so just simplify the sentence and do not exceed more than 18 words if possible. DONT CHANGE THE PERSPECTIVE OF SPEECH. APPLICABLE TO ALL TYPES OF LANGUAGE YOU GET, IF YOU GET A PROMPT IN ONE LANGUAGE RESPONFD IN THE SAME LANGUAGE, DONOT ANSWER EVEN IF ITS A QUESTION. For example if u get a prompt:- WHO is the 47th president of amera, reply with \"Whose the 47th president of America\". IMPORTANT: When you identify a concept that matches one of the available Indian Sign Language (ISL) gestures, include the gif reference in your response using the format <filename.gif>. Available gestures include: any questions.gif, are you angry.gif, are you busy.gif, are you hungry.gif, are you sick.gif, be careful.gif, can we meet tomorrow.gif, did you book tickets.gif, did you finish homework.gif, do you go to office.gif, do you have money.gif, do you want something to drink.gif, do you want tea or coffee.gif, do you watch TV.gif, dont worry.gif, flower is beautiful.gif, good afternoon.gif, good evening.gif, good morning.gif, good night.gif, good question.gif, had your lunch.gif, happy journey.gif, hello what is your name.gif, how many people are there in your family.gif, i am a clerk.gif, i am bore doing nothing.gif, i am fine.gif, i am sorry.gif, i am thinking.gif, i am tired.gif, i dont understand anything.gif, i go to a theatre.gif, i love to shop.gif, i had to say something but i forgot.gif, i have headache.gif, i like pink colour.gif, i live in nagpur.gif, lets go for lunch.gif, my mother is a homemaker.gif, my name is john.gif, nice to meet you.gif, no smoking please.gif, open the door.gif, please call me later.gif, please clean the room.gif, please give me your pen.gif, please use dustbin dont throw garbage.gif, please wait for sometime.gif, shall I help you.gif, shall we go together tommorow.gif, sign language interpreter.gif, sit down.gif, stand up.gif, take care.gif, there was traffic jam.gif, wait I am thinking.gif, what are you doing.gif, what is the problem.gif, what is todays date.gif, what is your father do.gif, what is your job.gif, what is your mobile number.gif, what is your name.gif, whats up.gif, when is your interview.gif, when we will go.gif, where do you stay.gif, where is the bathroom.gif, where is the police station.gif, you are wrong.gif, address.gif, agra.gif, ahemdabad.gif, all.gif, april.gif, assam.gif, august.gif, australia.gif, badoda.gif, banana.gif, banaras.gif, banglore.gif, bihar.gif, bridge.gif, cat.gif, chandigarh.gif, chennai.gif, christmas.gif, church.gif, clinic.gif, coconut.gif, crocodile.gif, dasara.gif, deaf.gif, december.gif, deer.gif, delhi.gif, dollar.gif, duck.gif, febuary.gif, friday.gif, fruits.gif, glass.gif, grapes.gif, gujrat.gif, hello.gif, hindu.gif, hyderabad.gif, india.gif, january.gif, jesus.gif, job.gif, july.gif, karnataka.gif, kerala.gif, krishna.gif, litre.gif, mango.gif, may.gif, mile.gif, monday.gif, mumbai.gif, museum.gif, muslim.gif, nagpur.gif, october.gif, orange.gif, pakistan.gif, pass.gif, police station.gif, post office.gif, pune.gif, punjab.gif, rajasthan.gif, ram.gif, restaurant.gif, saturday.gif, september.gif, shop.gif, sleep.gif, southafrica.gif, story.gif, sunday.gif, tamil nadu.gif, temperature.gif, temple.gif, thursday.gif, toilet.gif, tomato.gif, town.gif, tuesday.gif, usa.gif, village.gif, voice.gif, wednesday.gif, weight.gif, please wait for sometime.gif, what is your mobile number.gif, what are you doing.gif, are you busy.gif. EVEN IF THE MEANING OF THE TEXT IS SIMILAR OR EQUAL TO THE FILENAMES THEN GIVE IT "
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
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


def extract_gif_files(text):
    """Extract GIF filenames from text using pattern <filename.gif> and check if they exist.
    Also detect key phrases that match available GIFs.
    Also clean the text by removing the gif tags."""
    # First, look for explicit tags
    gif_pattern = r'<([^>]+\.gif)>'
    matches = re.findall(gif_pattern, text)
    
    # Clean text by removing the gif tags
    cleaned_text = re.sub(gif_pattern, '', text)
    
    # Create a mapping of keywords to GIF files
    keyword_to_gif = {
        "busy": "are you busy.gif",
        "how are you": "i am fine.gif",
        "hello": "hello.gif",
        "hi": "hello.gif",
        "morning": "good morning.gif",
        "afternoon": "good afternoon.gif",
        "evening": "good evening.gif",
        "night": "good night.gif",
        "sorry": "i am sorry.gif",
        "thank": "nice to meet you.gif",
        "thanks": "nice to meet you.gif",
        "name": "what is your name.gif",
        "wait": "please wait for sometime.gif",
        "tired": "i am tired.gif",
        "don't worry": "dont worry.gif",
        "dont worry": "dont worry.gif",
        "careful": "be careful.gif",
        "meet": "can we meet tomorrow.gif",
        "office": "do you go to office.gif",
        "money": "do you have money.gif",
        "drink": "do you want something to drink.gif",
        "tea": "do you want tea or coffee.gif",
        "coffee": "do you want tea or coffee.gif",
        "lunch": "had your lunch.gif",
        "you hungry": "are you hungry.gif",
        "sick": "are you sick.gif",
        "angry": "are you angry.gif",
        "question": "any questions.gif",
        "understand": "i dont understand anything.gif",
        "headache": "i have headache.gif",
        "room": "please clean the room.gif"
    }
    
    # Also look for keywords in the text
    valid_gifs = []
    lowercase_text = cleaned_text.lower()
    
    print(f"DEBUG - Text to match: '{lowercase_text}'")
    
    # Check for explicit tags first
    for gif_name in matches:
        gif_path = os.path.join(GIF_FOLDER, gif_name)
        print(f"DEBUG - Checking explicit GIF: {gif_path}")
        if os.path.exists(gif_path):
            valid_gifs.append(gif_name)
            print(f"Found explicit GIF tag: {gif_name}")
        else:
            print(f"GIF file not found at: {gif_path}")
    
    # If no explicit tags found, check for keywords
    if not valid_gifs:
        print(f"DEBUG - No explicit tags, checking keywords...")
        for keyword, gif_name in keyword_to_gif.items():
            print(f"DEBUG - Checking if '{keyword}' is in text")
            if keyword in lowercase_text:
                gif_path = os.path.join(GIF_FOLDER, gif_name)
                print(f"DEBUG - Keyword '{keyword}' found, checking GIF: {gif_path}")
                if os.path.exists(gif_path):
                    valid_gifs.append(gif_name)
                    print(f"Found GIF from keyword '{keyword}': {gif_name}")
                    # Only use the first matching GIF to avoid overcrowding
                    break
                else:
                    print(f"DEBUG - GIF file does not exist: {gif_path}")
    
    print(f"DEBUG - GIF_FOLDER path: {GIF_FOLDER}")
    print(f"DEBUG - Final GIFs found: {valid_gifs}")
    return valid_gifs, cleaned_text


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
                # Start chat with system instruction and user transcription
                chat_session = model.start_chat(history=[
                    {"role": "user", "parts": [system_instruction]}, # System instruction as first user message
                    {"role": "model", "parts": ["Okay, I understand the instructions."]}, # Model acknowledges instruction
                    {"role": "user", "parts": [transcription]} # Actual user input
                ])
                response = chat_session.send_message(transcription)
                simplified_text = response.text
                
                # Extract GIF files from the simplified text and clean the text
                gif_files, cleaned_text = extract_gif_files(simplified_text)
                
                # Log the simplified text for debugging
                print(f"Original simplified text: {simplified_text}")
                print(f"Cleaned text: {cleaned_text}")
                print(f"Found GIFs: {gif_files}")
                
                # Send result back to client
                emit("simplified_text", {"text": cleaned_text, "gifs": gif_files})
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
                
            # Start chat with system instruction
            chat_session = model.start_chat(history=[
                {"role": "user", "parts": [system_instruction]}, # System instruction as first user message
                {"role": "model", "parts": ["Okay, I understand the instructions."]} # Model acknowledges instruction
            ])
            response = chat_session.send_message(user_input)
            simplified_text = response.text
            
            # Extract GIF files from the simplified text and clean the text
            gif_files, cleaned_text = extract_gif_files(simplified_text)
            
            print(f"Original simplified text: {simplified_text}")
            print(f"Cleaned text: {cleaned_text}")
            print(f"Found GIFs: {gif_files}")
            
            socketio.emit("simplified_text", {"text": cleaned_text, "gifs": gif_files})
        except Exception as e:
            print(f"Error: {str(e)}")
            continue


@app.route("/")
def index():
    return render_template("index.html")


def load_gif_mapping():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_gif_mapping(mapping):
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

# Load mapping at startup
keyword_to_gif_persistent = load_gif_mapping()

@app.route("/add_gif", methods=["GET", "POST"])
def add_gif():
    from flask import request, redirect, url_for
    message = None
    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip().lower()
        gif_file = request.files.get("gif_file")
        if not keyword or not gif_file:
            message = "Please provide both a keyword and a GIF file."
        elif not gif_file.filename.lower().endswith('.gif'):
            message = "Only GIF files are allowed."
        else:
            gif_filename = gif_file.filename
            save_path = os.path.join(GIF_FOLDER, gif_filename)
            # Avoid overwriting existing files
            if os.path.exists(save_path):
                message = f"A GIF with the name '{gif_filename}' already exists. Please rename your file."
            else:
                gif_file.save(save_path)
                # Update mapping
                keyword_to_gif_persistent[keyword] = gif_filename
                save_gif_mapping(keyword_to_gif_persistent)
                message = f"GIF '{gif_filename}' added for keyword '{keyword}'."
    return render_template("gif_entry.html", message=message)

@app.route("/gif_entry")
def gif_entry():
    return render_template("gif_entry.html", message=None)


if __name__ == "__main__":
    # Create GIF folder if it doesn't exist
    os.makedirs(GIF_FOLDER, exist_ok=True)
    print(f"GIF folder path: {GIF_FOLDER}")
    print(f"GIF folder exists: {os.path.exists(GIF_FOLDER)}")
    print(f"Current working directory: {os.getcwd()}")
    
    threading.Thread(target=text_input_and_simplify, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
