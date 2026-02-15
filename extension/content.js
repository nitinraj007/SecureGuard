/**
 * SentinelSphere v3.5 - Robust Audio-Visual Guardian
 * UPDATED: Fixed FormData/Blob crashes and isolated Text logic.
 */

const BACKEND_URL = "http://127.0.0.1:8000";
const USER_ID = "user_" + Math.floor(Math.random() * 100000);
let isMonitoringEnabled = true;

// Cache to prevent spamming the backend
const processedMedia = new Set(); 

// --- 1. INITIALIZATION ---
if (typeof chrome !== 'undefined' && chrome.storage) {
    chrome.storage.local.get(['sentinelActive'], (result) => {
        isMonitoringEnabled = result.sentinelActive !== false;
    });
    chrome.storage.onChanged.addListener((changes) => {
        if (changes.sentinelActive) isMonitoringEnabled = changes.sentinelActive.newValue;
    });
}

// --- 2. VISUAL PROTECTION (Blur & Badge) ---
function applyShield(element, label, confidence) {
    if (element.dataset.shielded) return;
    element.dataset.shielded = "true";

    // Blur
    element.style.transition = "filter 0.5s ease";
    element.style.filter = "blur(15px) grayscale(80%)";

    // Badge
    const parent = element.parentElement;
    if (parent) {
        parent.style.position = "relative"; 
        const badge = document.createElement("div");
        badge.style.cssText = `
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(15, 23, 42, 0.95); color: #f43f5e; border: 1px solid #f43f5e;
            padding: 12px 20px; border-radius: 12px; z-index: 9999; text-align: center;
            font-family: sans-serif; box-shadow: 0 10px 25px rgba(0,0,0,0.5); pointer-events: none;
        `;
        badge.innerHTML = `
            <div style="font-size: 24px; mb: 5px;">🛡️</div>
            <div style="font-size: 14px; font-weight: 800; text-transform: uppercase;">${label}</div>
            <div style="font-size: 10px; color: #94a3b8;">Confidence: ${confidence}%</div>
        `;
        element.parentNode.insertBefore(badge, element.nextSibling);
    }
}

// --- 3. ROBUST MEDIA ANALYZER ---
async function analyzeVideo(videoElement) {
    if (!isMonitoringEnabled || videoElement.dataset.analyzing === "true") return;
    
    videoElement.dataset.analyzing = "true";
    
    try {
        const canvas = document.createElement('canvas');
        const scale = Math.min(1, 480 / (videoElement.videoWidth || 480));
        canvas.width = (videoElement.videoWidth || 480) * scale;
        canvas.height = (videoElement.videoHeight || 270) * scale;
        const ctx = canvas.getContext('2d');
        try { videoElement.crossOrigin = "anonymous"; } catch(e){}
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
        
        let audioBlob = null;
        try {
            if (videoElement.captureStream) {
                const stream = videoElement.captureStream();
                if (stream.getAudioTracks().length > 0) {
                    const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
                    const chunks = [];
                    recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
                    recorder.onstop = () => {
                        audioBlob = new Blob(chunks, { type: 'audio/webm' });
                        processBlobs(canvas, audioBlob, videoElement); // Handle sending here
                    };
                    recorder.start();
                    setTimeout(() => { if (recorder.state === "recording") recorder.stop(); }, 1500);
                    return; 
                }
            }
        } catch (e) { /* Audio capture failed, fall back to visual */ }

        // Fallback if no audio
        processBlobs(canvas, null, videoElement);

    } catch (e) {
        console.error("Video Error:", e);
        videoElement.dataset.analyzing = "false";
    }
}

// Helper to safely convert canvas to blob and send
function processBlobs(canvas, audioBlob, element) {
    canvas.toBlob(async (visualBlob) => {
        try {
            await sendToBackend(visualBlob, audioBlob, element);
        } finally {
            element.dataset.analyzing = "false"; // Reset lock
        }
    }, 'image/jpeg', 0.8);
}

async function sendToBackend(visualBlob, audioBlob, element) {
    const formData = new FormData();
    let hasData = false;

    // STRICT CHECK: Only append if it is a valid Blob
    if (visualBlob && visualBlob instanceof Blob) {
        formData.append('image_file', visualBlob, 'frame.jpg');
        hasData = true;
    }
    if (audioBlob && audioBlob instanceof Blob) {
        formData.append('audio_file', audioBlob, 'audio.webm');
        hasData = true;
    }

    if (!hasData) return; // Don't send empty requests

    formData.append('user_id', USER_ID);
    formData.append('context', 'reel_frame');

    try {
        const res = await fetch(`${BACKEND_URL}/analyze-media`, { method: 'POST', body: formData });
        const data = await res.json();
        
        if (data.authenticity_label.includes("Deepfake") || 
            data.authenticity_label.includes("Abuse") || 
            data.authenticity_label.includes("Bullying")) {
            
            const score = Math.max(data.deepfake_probability, data.abuse_probability, data.audio_toxicity * 100);
            applyShield(element, data.authenticity_label, score.toFixed(0));
        }
    } catch (err) {}
}

// --- 4. TEXT MODERATION ---
let typingTimer;
function attachTextListeners() {
    const inputs = document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"]');
    inputs.forEach(input => {
        if (input.dataset.sentinelBound) return;
        input.dataset.sentinelBound = "true";

        input.addEventListener('input', (e) => {
            clearTimeout(typingTimer);
            const text = e.target.value || e.target.innerText;
            
            if (text && text.length > 3) {
                typingTimer = setTimeout(() => {
                    fetch(`${BACKEND_URL}/moderate`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            platform: window.location.hostname,
                            user_id: USER_ID,
                            content_type: "text",
                            content: text
                        })
                    }).then(res => res.json()).then(data => {
                        if (data.risk_level === 'Aggressive') {
                            input.style.border = "2px solid #f43f5e"; // Red border warning
                        }
                    }).catch(()=>{});
                }, 1000);
            }
        });
    });
}

// --- 5. OBSERVERS ---
async function scanImage(img) {
    if (!isMonitoringEnabled || img.width < 150 || processedMedia.has(img.src)) return;
    processedMedia.add(img.src);

    const imgClone = new Image();
    imgClone.crossOrigin = "anonymous";
    imgClone.src = img.src;

    imgClone.onload = () => {
        try {
            const canvas = document.createElement('canvas');
            const scale = Math.min(1, 480 / imgClone.width);
            canvas.width = imgClone.width * scale;
            canvas.height = imgClone.height * scale;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(imgClone, 0, 0, canvas.width, canvas.height);
            
            canvas.toBlob(async (blob) => {
                // STRICT CHECK
                if (!blob || !(blob instanceof Blob)) return; 
                
                const formData = new FormData();
                formData.append('image_file', blob, 'image.jpg');
                formData.append('user_id', USER_ID);
                formData.append('context', 'image');
                
                try {
                    const res = await fetch(`${BACKEND_URL}/analyze-media`, { method: 'POST', body: formData });
                    const data = await res.json();
                    if (data.authenticity_label !== 'Real') {
                        applyShield(img, data.authenticity_label, Math.max(data.deepfake_probability, data.abuse_probability).toFixed(0));
                    }
                } catch (e) {}
            }, 'image/jpeg', 0.8);
        } catch(e) {}
    };
}

const observer = new MutationObserver((mutations) => {
    if (!isMonitoringEnabled) return;
    mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1) {
                if (node.tagName === 'IMG') scanImage(node);
                node.querySelectorAll?.('img').forEach(scanImage);
                if (node.tagName === 'VIDEO') attachVideoListener(node);
                node.querySelectorAll?.('video').forEach(attachVideoListener);
                attachTextListeners(); // Keep re-attaching to new inputs
            }
        });
    });
});

function attachVideoListener(vid) {
    if(vid.dataset.sentinelBound) return;
    vid.dataset.sentinelBound = "true";
    vid.addEventListener('play', () => { setTimeout(() => analyzeVideo(vid), 1500); });
}

observer.observe(document.body, { childList: true, subtree: true });
setTimeout(() => {
    document.querySelectorAll('img').forEach(scanImage);
    document.querySelectorAll('video').forEach(attachVideoListener);
    attachTextListeners();
}, 2000);