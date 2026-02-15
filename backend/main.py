import os
import datetime
import json
import numpy as np
import shutil
import tempfile
import firebase_admin
from firebase_admin import credentials, db, auth
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

# Defensive imports for Media
try:
    import cv2
    from PIL import Image
    import easyocr
    MEDIA_SUPPORT = True
except ImportError:
    print("⚠️ Media libraries missing. Run pip install -r requirements.txt")
    MEDIA_SUPPORT = False

app = FastAPI(title="SentinelSphere v3.5 | Audio-Visual Defense")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Firebase Initialization ---
cred_path = "serviceAccountKey.json"
if not os.path.exists(cred_path):
    print("❌ ERROR: serviceAccountKey.json missing!")
else:
    try:
        with open(cred_path) as f:
            cred_data = json.load(f)
        project_id = cred_data.get("project_id")
        db_url = f"https://{project_id}-default-rtdb.firebaseio.com/"
        cred = credentials.Certificate(cred_path)
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred, {'databaseURL': db_url})
        print(f"🔥 Firebase Connected to: {db_url}")
    except Exception as e:
        print(f"❌ Firebase Auth Failed: {e}")

# --- AI Model Loading ---
print("🧠 Loading AI Models (This may take a moment)...")

# 1. Text Toxicity (BERT)
try:
    text_classifier = pipeline("text-classification", model="unitary/toxic-bert", top_k=None, device=0)
    print("✅ Text Toxicity AI Ready")
except:
    text_classifier = None

# 2. Deepfake Detection (ViT)
try:
    deepfake_classifier = pipeline("image-classification", model="prithivML/deepfake-detection", device=0)
    print("✅ Deepfake AI Ready")
except:
    deepfake_classifier = None

# 3. Visual Abuse/NSFW
try:
    image_abuse_classifier = pipeline("image-classification", model="Falconsai/nsfw_image_detection", device=0)
    print("✅ Visual Abuse AI Ready")
except:
    image_abuse_classifier = None

# 4. Audio Transcription (Whisper)
try:
    # Using 'tiny' model for speed. 
    transcriber = pipeline("automatic-speech-recognition", model="openai/whisper-tiny.en", device=0)
    print("✅ Whisper Audio AI Ready")
except:
    transcriber = None
    print("⚠️ Whisper AI Failed to Load (Audio analysis will be skipped)")

# --- Endpoints ---

class TextPayload(BaseModel):
    platform: str
    user_id: str
    content_type: str
    content: str

@app.post("/moderate")
async def moderate_text(payload: TextPayload):
    toxic_score = 0
    risk_level = "Calm"
    
    if text_classifier:
        results = text_classifier(payload.content)[0]
        toxic_score = next((r['score'] for r in results if r['label'] == 'toxic'), 0)
        risk_level = "Aggressive" if toxic_score > 0.7 else "Calm"
        if toxic_score > 0.9: risk_level = "Critical"

    log_entry = {
        "platform": payload.platform,
        "user_id": payload.user_id,
        "content": payload.content,
        "risk_score": round(toxic_score * 100),
        "risk_level": risk_level,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Print to Terminal for Demo
    print(f"\n💬 TEXT SCAN: [{risk_level}] {payload.content[:30]}... ({round(toxic_score*100)}%)")
    
    try:
        db.reference('logs').push(log_entry)
    except:
        pass
        
    return log_entry

@app.post("/analyze-media")
async def analyze_media(
    image_file: UploadFile = File(None), 
    audio_file: UploadFile = File(None),
    user_id: str = Form(...), 
    context: str = Form("image")
):
    """
    Handles BOTH Image frames and Audio chunks.
    """
    res = {
        "media_type": "video" if context == "reel_frame" else "image",
        "timestamp": datetime.datetime.now().isoformat(),
        "user_id": user_id,
        "authenticity_label": "Real",
        "deepfake_probability": 0,
        "abuse_probability": 0,
        "audio_toxicity": 0,
        "ocr_text_toxicity": 0,
        "transcript": ""
    }

    # --- 1. VISUAL ANALYSIS ---
    if image_file:
        try:
            contents = await image_file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            
            # Deepfake Check
            if deepfake_classifier:
                df_results = deepfake_classifier(pil_img)
                res["deepfake_probability"] = round(next((r['score'] for r in df_results if r['label'].lower() == 'fake'), 0) * 100, 2)

            # NSFW/Abuse Check
            if image_abuse_classifier:
                ab_results = image_abuse_classifier(pil_img)
                res["abuse_probability"] = round(next((r['score'] for r in ab_results if r['label'].lower() == 'nsfw'), 0) * 100, 2)

        except Exception as e:
            print(f"❌ Image Error: {e}")

    # --- 2. AUDIO ANALYSIS ---
    if audio_file and transcriber:
        try:
            # Save temp file for ffmpeg/librosa
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                shutil.copyfileobj(audio_file.file, tmp)
                tmp_path = tmp.name
            
            # Transcribe Audio -> Text
            transcription = transcriber(tmp_path)
            text_content = transcription.get("text", "").strip()
            res["transcript"] = text_content

            # Analyze Text Toxicity
            if text_content and text_classifier:
                tox_results = text_classifier(text_content)[0]
                audio_tox = next((r['score'] for r in tox_results if r['label'] == 'toxic'), 0)
                res["audio_toxicity"] = round(audio_tox, 2)
            
            os.remove(tmp_path) # Cleanup
        except Exception as e:
            print(f"❌ Audio Error: {e}")

    # --- 3. DECISION LOGIC ---
    df_score = res["deepfake_probability"]
    ab_score = res["abuse_probability"]
    au_score = res["audio_toxicity"] * 100

    if df_score > 70:
        res["authenticity_label"] = "Deepfake"
    
    if ab_score > 60:
        res["authenticity_label"] = "Abusive Visuals"

    if au_score > 65:
        if res["authenticity_label"] == "Deepfake":
            res["authenticity_label"] = "Weaponized Deepfake"
        else:
            res["authenticity_label"] = "Verbal Abuse/Bullying"

    # --- 4. TERMINAL REPORT ---
    print("\n" + "="*50)
    print(f"🔍 ANALYSIS REPORT [{datetime.datetime.now().strftime('%H:%M:%S')}]")
    print("-" * 50)
    print(f"🏷️  VERDICT:    {res['authenticity_label'].upper()}")
    print(f"🤖 Deepfake:   {res['deepfake_probability']}%")
    print(f"🔞 Abuse/NSFW: {res['abuse_probability']}%")
    if res['audio_toxicity'] > 0:
        print(f"🎤 Audio Tox:  {int(res['audio_toxicity']*100)}%")
        print(f"📝 Transcript: \"{res['transcript'][:50]}...\"")
    print("="*50 + "\n")

    # Save to Firebase
    try:
        if context == "reel_frame" or res["authenticity_label"] != "Real":
            path = "videos" if context == "reel_frame" else "images"
            db.reference(f'media_analysis/{path}').push(res)
    except Exception as e:
        print(f"❌ Firebase Write Error: {e}")

    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
