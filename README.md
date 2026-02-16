🛡️ SecureGuard

✨ AI‑Powered Multi‑Modal Cyber Safety & Behavioral Intelligence System
🚨 Detecting digital harm before it escalates.

🌍 Overview
SecureGuard is an AI‑driven cyber safety platform built to intelligently detect and analyze:

🔹 Cyberbullying

🔹 Identity‑based harassment

🔹 Threat & doxxing attempts

🔹 Toxic behavioral escalation

🔹 Suspicious interaction patterns

It combines:

🧠 Offline AI Models

🌐 Instagram Web Extension

⚡ FastAPI Backend

🔥 Behavioral Intelligence Engine

📊 Real‑Time Analytics Dashboard

☁️ Firebase Realtime Database

This project demonstrates how AI can move beyond basic keyword filtering and perform contextual + behavioral risk analysis.

🚀 Platform Support
⚠️ Currently optimized for:

📸 Instagram (Web Version)

The architecture is modular and can be extended to other platforms with code modifications.

🧠 Core Features
🔎 Text Intelligence
✨ Transformer‑based toxicity detection (offline)

✨ Threat pattern recognition

✨ Identity‑based harassment detection

✨ Context‑aware analysis

📈 Behavioral Intelligence Engine

🔁 Aggression streak tracking

📊 Escalation monitoring

🧠 Psychological Pressure Index

🔥 Toxicity heatmap visualization

🎯 Target interaction monitoring

This transforms moderation from:

“Detecting bad words”

into:

“Detecting behavioral harm patterns.”


📊 Real‑Time Dashboard

📌 Total content scanned

📌 Risk trend graphs

📌 Network stress visualization

📌 Deep logs panel

📌 System resource monitoring

📌 Behavioral analytics insights

Clean, modern, intelligence‑style interface.

🏗️ System Architecture

User Input (Instagram Web)

        ↓

Browser Extension

        ↓

FastAPI Backend

        ↓

Offline AI Models

        ↓

Behavioral Risk Engine

        ↓

Firebase Database

        ↓

Analytics Dashboard

🧠 Offline AI Models

⚠️ This project uses locally downloaded AI models.

On first run:

⬇️ Required models will download automatically

📦 Model size may be large

🌐 Stable internet is required initially

💾 Ensure sufficient RAM and storage

All inference runs locally after download.

Use responsibly and ensure your system supports AI workloads.

☁️ Recommended Database – Firebase

SecureGuard is designed to work best with:

🔥 Firebase Realtime Database

Recommended setup:

🔹 Firebase SDK (Frontend)

🔹 Firebase Admin SDK (Backend)

🔹 Firebase Authentication

🔐 Authentication Setup

To enable login:

1️⃣ Go to Firebase Console

2️⃣ Navigate to Authentication

3️⃣ Manually create a user (Email + Password)

4️⃣ Use those credentials in the dashboard

You can modify authentication logic in the code as needed.

⚙️ Installation Guide -

📥 Clone Repository :

git clone https://github.com/your-username/secureguard.git

cd secureguard 

🖥 Backend Setup :

cd backend

pip install -r requirements.txt

Run server:

python -m uvicorn main:app --reload

Swagger Docs:

http://127.0.0.1:8000/docs

🌐 Frontend Dashboard
Open: frontend/index.html

Or run: python -m http.server 5500

🧩 Chrome Extension Setup

1️⃣ Open Chrome

2️⃣ Go to chrome://extensions

3️⃣ Enable Developer Mode

4️⃣ Click Load Unpacked

5️⃣ Select the extension folder

The extension captures input on Instagram Web and sends it to the backend for analysis.

⚠️ Ethical & Legal Warning

🚨 IMPORTANT 🚨

This tool captures user input events for AI moderation analysis.

Because of this, if misused, it may function similarly to input‑monitoring systems.

This project is strictly intended for:

📚 Educational purposes

🧠 AI research

🛡 Cyber safety experimentation

🔬 Controlled development environments

It must NOT be used for:

❌ Surveillance

❌ Unauthorized monitoring

❌ Privacy invasion

❌ Data theft

❌ Malicious activities

The creator is not responsible for misuse of this software.

By using this project, you agree to:

✔ Follow all local laws

✔ Respect platform policies

✔ Use only in controlled environments

✔ Maintain ethical AI practices

✔ Protect user privacy

Always use AI responsibly.

Always act ethically.

👤 Author
✨ Made by Me ✨
