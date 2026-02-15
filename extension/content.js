// SentinelShield - Multi-Platform Input Listener
// Verified On/Off Logic

let debounceTimer;
const BACKEND_URL = "http://127.0.0.1:8000/moderate";
const USER_ID = "user_" + Math.floor(Math.random() * 10000); 

// --- 1. State Management (Crucial for Toggle) ---
let isMonitoringEnabled = true;

// Initial check on load
if (typeof chrome !== 'undefined' && chrome.storage) {
    chrome.storage.local.get(['sentinelActive'], (result) => {
        // Default to true if the key doesn't exist yet
        isMonitoringEnabled = result.sentinelActive !== false;
        console.log(`🛡️ SentinelShield Status: ${isMonitoringEnabled ? 'ACTIVE' : 'PAUSED'}`);
    });
}

// Listen for the switch being toggled in the popup while the page is open
if (typeof chrome !== 'undefined' && chrome.storage) {
    chrome.storage.onChanged.addListener((changes, areaName) => {
        if (areaName === 'local' && changes.sentinelActive) {
            isMonitoringEnabled = changes.sentinelActive.newValue;
            console.log(`🛡️ SentinelShield Toggled: ${isMonitoringEnabled ? 'ENABLED' : 'DISABLED'}`);
        }
    });
}

// --- 2. Platform Detection ---
function getPlatformName() {
    const hostname = window.location.hostname;
    if (hostname.includes('instagram')) return 'Instagram';
    if (hostname.includes('twitter') || hostname.includes('x.com')) return 'X (Twitter)';
    if (hostname.includes('snapchat')) return 'Snapchat';
    if (hostname.includes('whatsapp')) return 'WhatsApp';
    if (hostname.includes('facebook')) return 'Facebook';
    if (hostname.includes('linkedin')) return 'LinkedIn';
    return 'Web';
}

const CURRENT_PLATFORM = getPlatformName();

function sendToBackend(text) {
    // 🛑 THE MASTER SWITCH
    // If the user turned the tool OFF in the popup, this stops the AI request
    if (!isMonitoringEnabled) {
        return;
    }

    if (!text || text.trim().length < 2) return;

    const payload = {
        platform: CURRENT_PLATFORM,
        user_id: USER_ID,
        target_user_id: "unknown", 
        content_type: "text_input",
        content: text
    };

    fetch(BACKEND_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => console.log("🛡️ SentinelShield Analysis:", data))
    .catch(err => console.error("SentinelShield Error:", err));
}

function handleInput(e) {
    const text = e.target.value || e.target.innerText;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => sendToBackend(text), 1000); 
}

function attachListeners() {
    const inputs = document.querySelectorAll('textarea, input[type="text"], [contenteditable="true"]');
    inputs.forEach(input => {
        if (!input.dataset.sentinelBound) {
            input.addEventListener('input', handleInput);
            input.dataset.sentinelBound = "true";
        }
    });
}

// Start listeners
attachListeners();

// Re-attach listeners when the page content changes (common in social media feeds)
const observer = new MutationObserver(() => attachListeners());
observer.observe(document.body, { childList: true, subtree: true });