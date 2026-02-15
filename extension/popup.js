document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('toggle-switch');
    const statusCard = document.getElementById('status-card');
    const statusText = document.getElementById('status-text');
    const statusSub = document.getElementById('status-sub');
    const statusIcon = document.getElementById('status-icon');
    const dashboardBtn = document.getElementById('btn-dashboard');

    // Load saved state
    chrome.storage.local.get(['sentinelActive'], (result) => {
        const isActive = result.sentinelActive !== false; // Default to true
        toggle.checked = isActive;
        updateUI(isActive);
    });

    // Handle toggle change
    toggle.addEventListener('change', () => {
        const isActive = toggle.checked;
        chrome.storage.local.set({ sentinelActive: isActive }, () => {
            console.log("Sentinel State Updated:", isActive);
            updateUI(isActive);
        });
    });

    function updateUI(isActive) {
        if (isActive) {
            statusCard.className = "status-card active";
            statusText.innerText = "SHIELD ACTIVE";
            statusIcon.innerText = "🛡️";
            statusSub.innerText = "Scanning Images, Video & Text";
            statusText.style.color = "#10b981";
        } else {
            statusCard.className = "status-card inactive";
            statusText.innerText = "PROTECTION PAUSED";
            statusIcon.innerText = "⏸️";
            statusSub.innerText = "AI Models Disconnected";
            statusText.style.color = "#f43f5e";
        }
    }

    // Open Dashboard in new tab
    dashboardBtn.addEventListener('click', () => {
        chrome.tabs.create({ url: 'http://127.0.0.1:5500/frontend/index.html' }); 
        // Note: User might be running index.html from a file or server, ensure this matches their setup.
        // If simply opening the file: chrome.tabs.create({ url: 'index.html' });
    });
});