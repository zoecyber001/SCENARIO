// ============================================================================
// WebSocket Connection
// ============================================================================

const socket = io();
let startTime = null;
let timerInterval = null;
let alertCount = 0;

console.log('[INIT] Script loaded');

// ============================================================================
// DOM Elements
// ============================================================================

const elements = {
    startBtn: document.getElementById('start-btn'),
    status: document.getElementById('status'),
    timer: document.getElementById('timer'),
    consoleLog: document.getElementById('console-log'),
    hexDump: document.getElementById('hex-dump'),
    codeViewer: document.getElementById('code-viewer'),
    codeContent: document.getElementById('code-content'),
    telemetryModel: document.getElementById('telemetry-model'),
    telemetryIp: document.getElementById('telemetry-ip'),
    telemetryStatus: document.getElementById('telemetry-status')
};

console.log('[INIT] DOM elements loaded');

// ============================================================================
// WebSocket Event Handlers
// ============================================================================

socket.on('connect', () => {
    console.log('[WS] WebSocket connected');
    addLogEntry('system', 'WebSocket connection established');
});

socket.on('log', (data) => {
    console.log('[WS] Received log:', data);
    addLogEntry(data.type, data.message, data.timestamp);
});

socket.on('hex', (data) => {
    addHexLine(data.addr, data.hex, data.ascii);
});

socket.on('telemetry', (data) => {
    updateTelemetry(data.key, data.value);
});

socket.on('code', (data) => {
    addCodeLine(data.line);
});

// ============================================================================
// UI Functions
// ============================================================================

function addLogEntry(type, message, timestamp = null) {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;

    const ts = timestamp || new Date().toLocaleTimeString('en-US', { hour12: false });

    entry.innerHTML = `
        <span class="timestamp">[${ts}]</span>
        <span class="message">${message}</span>
    `;

    elements.consoleLog.appendChild(entry);
    elements.consoleLog.scrollTop = elements.consoleLog.scrollHeight;
}

function addHexLine(addr, hex, ascii) {
    // Clear placeholder on first hex dump
    if (elements.hexDump.children.length === 1 &&
        elements.hexDump.children[0].querySelector('.hex-data').textContent.includes('--')) {
        elements.hexDump.innerHTML = '';
    }

    const line = document.createElement('div');
    line.className = 'hex-line';
    line.innerHTML = `
        <span class="hex-addr">${addr}</span>
        <span class="hex-data">${hex}</span>
        <span class="hex-ascii">${ascii}</span>
    `;

    elements.hexDump.appendChild(line);
    elements.hexDump.scrollTop = elements.hexDump.scrollHeight;
}

function updateTelemetry(key, value) {
    switch (key) {
        case 'model':
            elements.telemetryModel.textContent = value;
            break;
        case 'ip':
            elements.telemetryIp.textContent = value;
            break;
        case 'status':
            elements.telemetryStatus.textContent = value;
            updateStatusIndicator(value);
            break;
    }
}

function updateStatusIndicator(status) {
    const statusText = elements.status.querySelector('.status-text');
    const statusDot = elements.status.querySelector('.status-dot');

    statusText.textContent = status;

    // Change color based on status
    const colors = {
        'CONNECTED': '#10b981',
        'COMPROMISED': '#ef4444',
        'DISCONNECTED': '#ef4444',
        'DUMPING MEMORY': '#f59e0b',
        'ANALYZING': '#f59e0b',
        'INVESTIGATING': '#f59e0b'
    };

    const color = colors[status] || '#14b8a6';
    statusDot.style.background = color;
    statusDot.style.boxShadow = `0 0 10px ${color}`;
}

function addCodeLine(line) {
    // Show code viewer on first line
    if (elements.codeContent.textContent === '') {
        elements.codeViewer.style.display = 'block';
    }

    elements.codeContent.textContent += line + '\n';
}

function startTimer() {
    console.log('[TIMER] Starting timer');
    startTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const seconds = (elapsed % 60).toString().padStart(2, '0');
        elements.timer.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

// ============================================================================
// Event Listeners
// ============================================================================

if (elements.startBtn) {
    elements.startBtn.addEventListener('click', () => {
        console.log('[BUTTON] Start button clicked');
        elements.startBtn.disabled = true;
        elements.startBtn.textContent = '⏳ RUNNING...';

        // Clear previous data
        elements.consoleLog.innerHTML = '';
        elements.hexDump.innerHTML = '<div class="hex-line"><span class="hex-addr">0000</span><span class="hex-data">-- -- -- -- -- -- -- --</span><span class="hex-ascii">........</span></div>';
        elements.codeContent.textContent = '';
        elements.codeViewer.style.display = 'none';
        alertCount = 0;

        // Start timer
        startTimer();

        // Trigger scenario
        console.log('[WS] Emitting start_scenario event');
        socket.emit('start_scenario');
        console.log('[WS] Event emitted');
    });
    console.log('[INIT] Button listener attached');
} else {
    console.error('[ERROR] Start button not found!');
}

// ============================================================================
// Initialization
// ============================================================================

console.log('[INIT] PRINTMON Client initialized');
addLogEntry('system', 'Press START ANALYSIS to begin...');
