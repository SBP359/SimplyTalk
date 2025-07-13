# SimplyTalk 🗣️🤖✨ (AI-Powered ISL Speech Simplifier)

SimplyTalk is a real-time web application that simplifies spoken or typed sentences using Google Gemini AI and provides relevant Indian Sign Language (ISL) GIFs as visual aids. Built with Flask, Socket.IO, and audio + AI processing tools, this project aims to improve accessibility and inclusive communication.

---

## 🚀 Features

🔊 Speech-to-Text + Gemini AI  
- Speak or type input.  
- Converts speech (WebM audio) to text using `speech_recognition`.  
- Uses Gemini AI to simplify the text (max 18 words, same language, same person/perspective).  

🤟 Indian Sign Language (ISL) GIFs  
- Matches simplified text or keywords to ISL gesture GIFs.  
- Supports explicit GIF tagging (e.g., `<hello.gif>`) or automatic keyword matching.  
- Web interface to upload new GIFs and assign keyword mappings.  

⚡ Real-Time Experience  
- Real-time client-server interaction using Flask-SocketIO.  
- Audio is streamed, processed, and responded to instantly.  

🌐 Web Interface  
- Intuitive front-end UI for interaction.  
- Upload ISL GIFs via `/add_gif`.  

---

## 🧠 Architecture Overview

[User]  
 ↓ speaks or types  
[Frontend (HTML/JS)] ←→ [Flask + Flask-SocketIO]  
 ↓                        ↓  
audio / text         Gemini API, SpeechRecognition  
 ↓                        ↓  
simplified text + matched GIFs  
 ↓  
[UI Display with ISL GIFs]  

---

## ⚙️ Tech Stack

- Flask – Core backend  
- Flask-SocketIO – Real-time WebSocket communication  
- SpeechRecognition – Converts audio to text  
- pydub + ffmpeg – Handles audio conversion  
- google-generativeai – Gemini Pro integration  
- Flask-CORS – Enables cross-origin frontend/backend  
- eventlet/threading – Async server support (depends on Python version)  

---

## 🔧 Setup Instructions

1. Clone the Repo

    git clone https://github.com/SBP359/SimplyTalk.git  
    cd SimplyTalk  

2. Install Dependencies

    ⚠️ Make sure ffmpeg is installed and in your PATH.

    pip install -r requirements.txt  

3. Run the App

    python main.py  

4. Open in Browser

    http://localhost:5000/  

---

## 📁 Project Structure

SimplyTalk/  
├── static/                 # JS, CSS, GIFs  
├── templates/              # HTML templates  
├── gif/                    # ISL GIF files  
├── gif_mapping.json        # Keyword-to-GIF mappings  
├── main.py                 # App entry point  
├── utils.py                # Audio + AI handling  
├── requirements.txt  
└── README.md  

---

## 🧩 Add New ISL GIFs

1. Go to `/add_gif` in your browser.  
2. Upload a `.gif` and assign one or more keywords.  
3. GIF is saved to `gif/` and mapping is persisted in `gif_mapping.json`.  

---

## 🔐 Security Notes

- Gemini API key is hardcoded → Use environment variables!  
- No authentication → Anyone can upload GIFs.  
- CORS is fully open → Restrict in production.  

---

## 💡 Future Enhancements

- Add login/authentication for GIF management.  
- Smarter GIF matching using NLP or embeddings.  
- Multi-language support.  
- Move GIF mappings to a database for scale.  
- More robust error handling and logging.  

---

## 🧪 Python Compatibility

| Python Version | Compatible? | Notes |
|----------------|-------------|-------|
| 3.11 or lower  | ✅ Yes       | Uses eventlet for async |
| 3.13 or higher | ⚠️ Partial   | Falls back to threading (slower WebSocket perf) |

---
<h2 align="center">📸 SimplyTalk Web UI Showcase</h2>

<h3 align="center">🧠 Main App Interface – Real-Time Speech Simplification</h3>

<p align="center">
  <img src="https://raw.githubusercontent.com/SBP359/SBP359/135006194d56104de07f8347e4d62c260b42282f/simplytalk/1.jpeg" width="600"/>
</p>
<p align="center"><i>Main web interface of SimplyTalk — supports speech-to-text, Gemini AI simplification, and real-time ISL GIF suggestions.</i></p>

<hr/>

<h3 align="center">🖼️ GIF Management Interface – Add New ISL Mappings</h3>

<p align="center">
  <img src="https://raw.githubusercontent.com/SBP359/SBP359/135006194d56104de07f8347e4d62c260b42282f/simplytalk/2.jpeg" width="600"/>
</p>
<p align="center"><i>Admin page to upload new Indian Sign Language (ISL) GIFs and map them to keywords — no database needed.</i></p>


<h2 align="center">🖼️ SimplyTalk on Smartwatch (Wearable UI Demo)</h2>

<p align="center">
  <img src="https://raw.githubusercontent.com/SBP359/SBP359/c1c653c416943a645c14fb7ee319d6279e24be54/simplytalk/simplytalk.png" width="300"/>
</p>

<p align="center"><i>Prototype of SimplyTalk running on a smartwatch UI, showing real-time transcription and ISL integration.</i></p>

## 🤝 Credits

Built with ❤️ by SBP359  
Inspired by accessibility tech and the power of generative AI.  

---

## 📜 License

MIT License — use freely, contribute, and improve!
