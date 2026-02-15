import os
import datetime
import firebase_admin
from firebase_admin import credentials, db
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

# --- Configuration ---
# Initialize FastAPI
app = FastAPI(title="SentinelShield AI Engine")

# CORS Setup (Allowing extension and local dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Firebase Initialization ---
# NOTE: You must place your serviceAccountKey.json in the same directory
cred_path = "serviceAccountKey.json"
if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    # REPLACE databaseURL with your actual Firebase Realtime DB URL
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://sentinelspherelite-default-rtdb.firebaseio.com/' 
    })
    print("🔥 Firebase Connected")
else:
    print("⚠️ WARNING: serviceAccountKey.json not found. Firebase writes will fail.")

# --- AI Model Initialization ---
print("🧠 Loading Toxic-BERT Model... (This may take a moment)")
# Using a smaller, fast variant for demo speed, or unitary/toxic-bert as requested
# If unitary/toxic-bert is too slow locally, swap for 'distilbert-base-uncased-finetuned-sst-2-english'
classifier = pipeline("text-classification", model="unitary/toxic-bert", top_k=None)
print("✅ Model Loaded")

# --- Data Models ---
class ContentSubmission(BaseModel):
    platform: str
    user_id: str
    target_user_id: str = "unknown"
    content_type: str
    content: str

# --- Helper Functions ---
def analyze_toxicity(text):
    """Returns a score between 0 and 1 representing toxicity."""
    if not text:
        return 0.0
    results = classifier(text[:512]) # Truncate to 512 tokens
    # Sum scores of toxic labels
    toxic_score = 0.0
    for label in results[0]:
        if label['label'] in ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']:
            toxic_score += label['score']
    
    # Normalize roughly to 0-1 range (heuristic)
    return min(toxic_score, 1.0)

def check_restricted_words(text, restricted_list):
    """Count occurrences of restricted words."""
    count = 0
    text_lower = text.lower()
    for word in restricted_list:
        if word.lower() in text_lower:
            count += 1
    return count

def calculate_risk_level(score):
    if score <= 30:
        return "Calm"
    elif score <= 60:
        return "Aggressive"
    else:
        return "Escalating"

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "SentinelShield AI Online", "timestamp": datetime.datetime.now()}

@app.post("/moderate")
async def moderate_content(submission: ContentSubmission):
    try:
        # 1. Fetch Config (Restricted Words)
        restricted_words = []
        if firebase_admin._apps:
            ref_config = db.reference('config/restricted_words')
            config_data = ref_config.get()
            if config_data:
                restricted_words = list(config_data.values()) if isinstance(config_data, dict) else config_data

        # 2. AI Analysis
        toxicity_score = analyze_toxicity(submission.content) # 0.0 to 1.0
        restricted_count = check_restricted_words(submission.content, restricted_words)
        
        # 3. Retrieve User History for Context
        user_ref = db.reference(f'users/{submission.user_id}')
        user_data = user_ref.get() or {}
        
        prev_warnings = user_data.get('warnings_ignored', 0)
        repeated_target_count = user_data.get('repeated_targeting', 0)
        
        # Check if targeting same user
        last_target = user_data.get('last_target_id')
        if last_target == submission.target_user_id and submission.target_user_id != "unknown":
            repeated_target_count += 1
        
        # 4. Risk Calculation Logic
        # (Avg Toxicity * 40) + (Restricted Words * 25) + (Warnings Ignored * 20) + (Repeated Targeting * 15)
        # We use current toxicity instead of avg for the immediate risk score of this specific event
        base_risk = (toxicity_score * 40) + (restricted_count * 25) + (prev_warnings * 5) + (repeated_target_count * 15)
        risk_score = min(round(base_risk), 100) # Cap at 100
        risk_level = calculate_risk_level(risk_score)
        
        # 5. Update Firebase
        timestamp = datetime.datetime.now().isoformat()
        
        # Update User Stats
        new_total_scanned = user_data.get('total_scanned', 0) + 1
        new_flagged_count = user_data.get('flagged_count', 0) + (1 if risk_score > 30 else 0)
        
        # Update rolling average toxicity
        current_avg = user_data.get('avg_toxicity', 0.0)
        new_avg = ((current_avg * (new_total_scanned - 1)) + toxicity_score) / new_total_scanned
        
        update_data = {
            'last_updated': timestamp,
            'total_scanned': new_total_scanned,
            'flagged_count': new_flagged_count,
            'avg_toxicity': round(new_avg, 3),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'last_target_id': submission.target_user_id,
            'repeated_targeting': repeated_target_count,
            'platform': submission.platform
        }
        
        user_ref.update(update_data)
        
        # Log the specific event
        log_ref = db.reference('logs')
        log_ref.push({
            'user_id': submission.user_id,
            'content': submission.content, # In prod, might want to hash this for privacy
            'toxicity_score': round(toxicity_score, 3),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'timestamp': timestamp,
            'platform': submission.platform
        })

        # Update Daily Stats (Global)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        daily_ref = db.reference(f'daily_stats/{today}')
        daily_ref.child('scanned').transaction(lambda current: (current or 0) + 1)
        if risk_score > 30:
            daily_ref.child('flagged').transaction(lambda current: (current or 0) + 1)

        return {
            "status": "processed",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "toxicity": round(toxicity_score, 3)
        }

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)