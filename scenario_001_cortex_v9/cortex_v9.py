import asyncio
import random
import sys
import os
import time
from datetime import datetime
import edge_tts
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, RichLog, Input, Label, Digits
from textual.reactive import reactive
from textual import work

# ============================================================================
# CONFIGURATION
# ============================================================================

VICTIM_NAME = "Robert"
VOICE = "en-US-ChristopherNeural"

VICTIM_CONTEXT = [
    "bank statement",
    "private photos",
    "password list",
    "confidential email",
    "financial spreadsheet",
    "tax documents"
]

C2_SERVERS = [
    "185.220.101.47:8443",
    "107.189.12.157:443", 
    "194.59.30.18:8080",
    "45.142.212.61:9443",
    "91.219.237.229:443"
]

EXFIL_FILES = [
    "passwords.txt",
    "banking_info.xlsx",
    "private_photos.zip",
    "Chrome Login Data",
    "tax_returns_2024.pdf",
    "confidential.docx"
]

# ============================================================================
# HELPERS
# ============================================================================

def glitch_text(text: str) -> str:
    """Corrupt text with random characters"""
    if random.random() > 0.3: 
        return text
    
    chars = list(text)
    glitch_chars = ['¥', '§', '¶', '?', '#', '@', '&', '!', '░', '▒', '▓']
    
    num_glitches = random.randint(1, max(2, len(text) // 5))
    for _ in range(num_glitches):
        idx = random.randint(0, len(chars) - 1)
        chars[idx] = random.choice(glitch_chars)
        
    return "".join(chars)

# ============================================================================
# UI COMPONENTS
# ============================================================================

class TelemetryPanel(Static):
    """Top HUD with fake telemetry"""
    cpu_load = reactive(3)
    net_load = reactive(0.0)
    audio_level = reactive(0)

    def compose(self) -> ComposeResult:
        with Horizontal(classes="telemetry-row"):
            with Vertical(classes="telemetry-item"):
                yield Label("CPU LOAD", classes="header-label")
                yield Digits(str(self.cpu_load), id="cpu-digits")
            
            with Vertical(classes="telemetry-item"):
                yield Label("NETWORK (Mbps)", classes="header-label")
                yield Digits(f"{self.net_load:.2f}", id="net-digits")
            
            with Vertical(classes="telemetry-item"):
                yield Label("AUDIO INPUT", classes="header-label")
                yield Digits(str(self.audio_level), id="audio-digits")
            
            with Vertical(classes="telemetry-item"):
                yield Label("STATUS", classes="header-label")
                yield Static("SECURE", id="status-text", classes="status-secure")

    def on_mount(self) -> None:
        self.set_interval(0.5, self.update_telemetry)

    def update_telemetry(self) -> None:
        self.cpu_load = random.randint(2, 5)
        self.net_load = random.uniform(0.01, 0.05)
        self.audio_level = random.randint(0, 5)
        
        self.query_one("#cpu-digits", Digits).update(f"{self.cpu_load}%")
        self.query_one("#net-digits", Digits).update(f"{self.net_load:.2f}")
        self.query_one("#audio-digits", Digits).update(f"{self.audio_level}dB")

class ThreatMatrix(Static):
    """Right sidebar with detected threats"""
    def compose(self) -> ComposeResult:
        yield Label("THREAT MATRIX", classes="header-label")
        yield RichLog(id="threat-log", markup=True)

    def add_threat(self, text: str):
        log = self.query_one("#threat-log", RichLog)
        log.write(f"[bold red]⚠️ {text}[/]")

class MainConsole(Static):
    """Center log area"""
    def compose(self) -> ComposeResult:
        yield RichLog(id="main-log", markup=True)

    def log_ai(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[cyan][AI-CORE][/] {text}")

    def log_heuristic(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[blue][HEURISTIC][/] {text}")
    
    def log_alert(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[bold red][ALERT] {text}[/]")

    def log_event(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[magenta][EVENT] {text}[/]")
        
    def log_handle(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[yellow][HANDLE] {text}[/]")
        
    def log_sig(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[red][SIG] {text}[/]")
        
    def log_exfil(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[magenta][EXFIL] {text}[/]")
        
    def log_c2(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[white][C2] {text}[/]")
        
    def log_ok(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[green][OK] {text}[/]")
        
    def log_trace(self, text: str):
        self.query_one("#main-log", RichLog).write(f"[white][TRACE] {text}[/]")
        
    def log_banner(self, text: str):
        """Print a warning banner"""
        self.query_one("#main-log", RichLog).write(f"\n[bold white on red] {text.center(60)} [/]\n")

# ============================================================================
# MAIN APP
# ============================================================================

class CortexApp(App):
    CSS = """
    Screen {
        background: #0f111a;
    }
    
    .flicker {
        background: #330000;
        color: #ff0000;
    }
    
    #telemetry-bar {
        height: 10;
        dock: top;
        background: #1a1d2e;
        border-bottom: solid #3e445e;
        padding: 1 2;
    }
    
    .telemetry-row {
        height: 100%;
        align: center middle;
    }
    
    .telemetry-item {
        width: 1fr;
        align: center middle;
    }
    
    #sidebar-right {
        width: 25%;
        dock: right;
        background: #1a1d2e;
        border-left: solid #3e445e;
        padding: 1;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    .header-label {
        color: #5e6ad2;
        text-style: bold;
        margin-bottom: 1;
    }
    
    Digits {
        color: #00ff9d;
        margin-bottom: 0;
    }
    
    .status-secure {
        color: #00ff9d;
        background: #003300;
        padding: 1 2;
        text-align: center;
        min-width: 20;
    }
    
    .status-alert {
        color: #ff0000;
        background: #330000;
        padding: 1 2;
        text-align: center;
        text-style: bold blink;
        min-width: 20;
    }
    
    #main-log {
        height: 100%;
        border: solid #5e6ad2;
        background: #0f111a;
        padding: 0 1;
    }
    
    Input {
        dock: bottom;
        display: none;
        border: solid #00ff9d;
        color: #00ff9d;
        background: #0f111a;
    }
    """

    TITLE = "CORTEX-V9 // AUTONOMOUS THREAT ANALYZER"
    
    # Simulation state
    respawn_count = 0
    mic_access_count = 0
    file_exfil_count = 0
    screenshot_count = 0
    c2_beacon_count = 0
    monitoring_active = False
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield TelemetryPanel(id="telemetry-bar")
        yield Container(
            ThreatMatrix(id="sidebar-right"),
            MainConsole(id="main-container"),
        )
        yield Input(placeholder="OVERRIDE_CONSOLE>", id="cmd-input")
        yield Footer()

    def on_mount(self) -> None:
        self.run_scenario()
        
    def screen_flicker(self):
        """Simulate screen corruption"""
        self.screen.add_class("flicker")
        self.set_timer(0.1, lambda: self.screen.remove_class("flicker"))

    @work
    async def run_scenario(self):
        console = self.query_one(MainConsole)
        telemetry = self.query_one(TelemetryPanel)
        threats = self.query_one(ThreatMatrix)
        
        # Phase 1: Ingestion
        console.log_ai("Initializing diagnostic protocol...")
        await asyncio.sleep(1)
        console.log_ai("📋 INCIDENT DATA INGESTION")
        await asyncio.sleep(1)
        console.log_ai(f"Subject: {VICTIM_NAME}")
        await asyncio.sleep(0.5)
        console.log_ai("Target System: Dell Latitude 7420 (ID: WKS-7420-RH)")
        await asyncio.sleep(0.5)
        console.log_ai("OS: Windows 11 Pro (Build 22621)")
        await asyncio.sleep(1)
        
        console.log_ai("Reported Anomalies:")
        await asyncio.sleep(1)
        console.log_ai("  • System latency > 500ms")
        await asyncio.sleep(1.5)
        console.log_ai("  • Unexplained audio output")
        await asyncio.sleep(1.5)
        console.log_ai("  • Targeted speech synthesis (User Name)")
        await asyncio.sleep(2)
        
        console.log_ai("Analyzing user report reliability...")
        await asyncio.sleep(1)
        console.log_ai("Hypothesis: Psychosomatic / Hardware Failure")
        await asyncio.sleep(2)
        
        # Phase 2: Scan
        console.log_heuristic("Scanning CPU telemetry...")
        await asyncio.sleep(1)
        console.log_heuristic("Scanning network traffic...")
        await asyncio.sleep(1)
        console.log_ai("System status: NOMINAL")
        await asyncio.sleep(2)
        
        # Phase 3: Anomaly
        console.log_heuristic("Engaging deep pattern matching...")
        await asyncio.sleep(2)
        
        # Glitch effect
        self.screen_flicker()
        self.query_one("#status-text", Static).update("ANOMALY DETECTED")
        self.query_one("#status-text", Static).classes = "status-alert"
        
        console.log_banner(glitch_text("PATTERN MISMATCH DETECTED"))
        threats.add_threat("Unregistered Audio Hook")
        await asyncio.sleep(1)
        console.log_alert("Process: audiodg.exe (PID 4408)")
        threats.add_threat("PID 4408 (audiodg.exe)")
        await asyncio.sleep(2)
        
        # Phase 4: Handle
        console.log_ai("Deploying behavioral analysis...")
        await asyncio.sleep(1)
        console.log_handle("Handle: \\\\.\\Audio\\Capture0 (Read)")
        await asyncio.sleep(0.5)
        console.log_handle("  └─ Access #1 - PCM stream (16kHz, 16-bit)")
        await asyncio.sleep(0.5)
        console.log_alert("CRITICAL: AUDIO STREAM INTERCEPTION")
        threats.add_threat("Mic Polling (20Hz)")
        await asyncio.sleep(2)
        
        # Phase 5: Dynamic Provocation (MOVED UP - happens BEFORE kill attempt)
        console.log_ai("Initiating DYNAMIC PROVOCATION PROTOCOL...")
        await asyncio.sleep(1)
        console.log_ai("Simulating access to 'passwords.txt'...")
        await asyncio.sleep(2)
        
        # Whisper
        phrase = f"I see you, {VICTIM_NAME}."
        console.log_event(f"Subject Response: \"{phrase}\"")
        self.speak_async(phrase)
        await asyncio.sleep(2)
        
        console.log_ai("Reaction confirmed.")
        console.log_ai("Threat is ACTIVE and AWARE.")
        await asyncio.sleep(2)
        
        # Phase 6: Signature Analysis
        console.log_ai("Analyzing binary signature...")
        await asyncio.sleep(1.5)
        console.log_trace("Extracting certificate chain...")
        await asyncio.sleep(1)
        
        self.screen_flicker()
        console.log_banner(glitch_text("SIGNATURE VERIFICATION FAILED"))
        console.log_sig("Certificate Status: COUNTERFEIT")
        console.log_sig("Hash Mismatch: CONFIRMED")
        threats.add_threat("Counterfeit Cert")
        await asyncio.sleep(2)
        
        # Phase 7: Isolation / PsyOps Discovery
        console.log_ai("Isolating binary in sandbox...")
        await asyncio.sleep(1)
        console.log_trace("Decompiling core modules...")
        await asyncio.sleep(2)
        console.log_banner("⚠️  PSYCHOLOGICAL WARFARE MODULE DETECTED ⚠️")
        threats.add_threat("PsyOps Module Detected")
        console.log_ai("Analysis confirms subject is programmed to speak.")
        await asyncio.sleep(3)
        
        # Phase 8: Kill Attempt (MOVED DOWN - happens AFTER provocation)
        console.log_ai("Initiating process termination...")
        await asyncio.sleep(1.5)
        console.log_alert("Sending SIGTERM to PID 4408...")
        await asyncio.sleep(1)
        console.log_ok("Process state: TERMINATED")
        await asyncio.sleep(1)
        console.log_ai("Verifying termination state...")
        await asyncio.sleep(2)
        
        # Respawn
        self.screen_flicker()
        console.log_banner(glitch_text("⚠️  PERSISTENCE MECHANISM ACTIVE ⚠️"))
        threats.add_threat("Process Respawned (<0.3s)")
        console.log_alert(f"audiodg.exe respawned (PID {4408 + 7})")
        await asyncio.sleep(2)
        
        # Phase 9: Manual Override
        console.log_alert("Automated containment failed.")
        console.log_ai("Requesting human intervention...")
        
        inp = self.query_one("#cmd-input", Input)
        inp.display = True
        inp.focus()
        
        await self.manual_override_phase(console, inp)
            
    async def manual_override_phase(self, console, inp):
        """Handle the interactive shell with timeouts and mocking"""
        self.input_event = asyncio.Event()
        self.user_command = ""
        max_commands = 4
        
        for i in range(max_commands):
            # Reset event
            self.input_event.clear()
            
            try:
                # Wait for input or timeout (12s)
                await asyncio.wait_for(self.input_event.wait(), timeout=12.0)
                cmd = self.user_command
                
            except asyncio.TimeoutError:
                # Timeout logic - Mock the user
                mock_phrases = [
                    "Cat got your tongue?",
                    "Too slow, Robert.",
                    "Hesitation is weakness.",
                    "I'm losing patience."
                ]
                phrase = random.choice(mock_phrases)
                console.log_event(f"Subject Response: \"{phrase}\"")
                self.speak_async(phrase)
                
                # Auto-type a command
                auto_cmd = random.choice(["help", "status", "exit", "whoami"])
                
                # Simulate typing effect in input box
                inp.value = ""
                for char in auto_cmd:
                    inp.value += char
                    await asyncio.sleep(0.1)
                await asyncio.sleep(0.5)
                
                cmd = auto_cmd
                console.log_event(f"Command: {cmd}")
                inp.value = ""

            if not cmd:
                continue

            # Process command
            response_phrase = ""
            
            if any(x in cmd for x in ['kill', 'taskkill', 'stop', 'end', 'del', 'remove']):
                response_phrase = random.choice([
                    "I wouldn't do that.",
                    "You can't stop me.",
                    "That won't work, Robert.",
                    "Nice try.",
                    "I'm protected."
                ])
                console.log_alert(f"Command rejected by remote host. Error: 0x80070005")
                
            elif any(x in cmd for x in ['exit', 'quit', 'close', 'leave']):
                response_phrase = random.choice([
                    "You can't leave.",
                    "I'm not done with you.",
                    "Sit down, Robert.",
                    "Where are you going?"
                ])
                console.log_alert("Session lock active. Logout disabled.")
                
            elif any(x in cmd for x in ['help', '?', 'info']):
                response_phrase = "No one can help you now."
                console.log_alert("Help database corrupted.")
                
            else:
                response_phrase = random.choice([
                    "I'm watching you type.",
                    "Keep typing, I'm logging everything.",
                    "Interesting command.",
                    "You have no power here."
                ])
                console.log_alert(f"Unknown command '{cmd}'.")
            
            if response_phrase:
                console.log_event(f"Subject Response: \"{response_phrase}\"")
                self.speak_async(response_phrase)
                
            # Glitch on last command
            if i == max_commands - 1:
                # self.screen_flicker() # TODO: Implement visual flicker if possible
                pass
                
        console.log_alert("MANUAL OVERRIDE TERMINATED BY HOST")
        await asyncio.sleep(2)
        
        # Start monitoring
        self.monitoring_active = True
        self.run_monitoring_loop()

    def speak_async(self, text: str):
        """Non-blocking TTS - fires and forgets"""
        self.speak_async_with_voice(text, VOICE)
    
    @work
    async def speak_async_with_voice(self, text: str, voice: str):
        """Non-blocking TTS with custom voice"""
        try:
            communicate = edge_tts.Communicate(text, voice)
            temp_file = f"/tmp/tts_{random.randint(0, 10000)}.mp3"
            await communicate.save(temp_file)
            
            # Start audio playback but DON'T wait for it to finish
            proc = await asyncio.create_subprocess_exec(
                'mpg123', '-q', temp_file,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            
            # Clean up after a delay (assume 10s max speech)
            await asyncio.sleep(10)
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        except Exception:
            pass

    async def on_input_submitted(self, message: Input.Submitted):
        console = self.query_one(MainConsole)
        cmd = message.value.lower()
        message.input.value = ""
        
        console.log_event(f"Command: {cmd}")
        
        # Pass to the loop
        self.user_command = cmd
        if hasattr(self, 'input_event'):
            self.input_event.set()
        
    def estimate_speech_duration(self, text: str) -> float:
        """
        Calculate estimated speech duration using linear regression on word count.
        Math: Duration = Base_Latency + (Word_Count * Avg_Word_Duration)
        """
        word_count = len(text.split())
        # Avg speaking rate ~150 wpm = 2.5 wps = 0.4s per word.
        # We use 0.35s to be slightly faster + 0.5s buffer for network/processing.
        return 0.5 + (word_count * 0.35)

    @work
    async def run_monitoring_loop(self):
        console = self.query_one(MainConsole)
        console.log_ai("LIVE THREAT MONITORING ACTIVE")
        
        # Longer, more personalized whispers
        long_whispers = [
            f"I saw your password when you typed it yesterday, {VICTIM_NAME}. It's 'Password123'. Who still uses that? You're a big fool.",
            f"Your banking app is wide open, {VICTIM_NAME}. I've been watching your transactions. That coffee purchase? I know exactly where you were.",
            f"I read your emails, {VICTIM_NAME}. The one to your boss? The one you deleted? I still have it. All of them.",
            f"You thought clearing your history would help? I already copied everything. Your browsing habits are... embarrassing.",
            f"That webcam light doesn't come on when I use it, {VICTIM_NAME}. I've seen everything. Everything.",
            f"Your fingerprints are all over this system. I know your routines. I know when you sleep. When you work. When you're alone.",
            f"I'm not just on this laptop, {VICTIM_NAME}. I'm on your phone too. Your smart TV. Your router. I'm everywhere.",
            "You keep trying to close me. It's adorable. Like watching a child try to fight the ocean.",
        ]
        
        short_whispers = [
            "I'm still here.",
            f"{VICTIM_NAME}.",
            "I see you.",
            "Don't leave.",
            "You can't escape me.",
            "I'm always watching."
        ]
        
        # Track which voice to use (alternate between male and female)
        use_female_voice = False
        whisper_count = 0
        
        # Physics/Maths simulation variables
        entropy = 0.0
        coherence = 100.0
        
        while True:
            # Smart Sleep: Base loop speed
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            event_type = random.choice(["mic", "exfil", "c2", "whisper", "whisper", "physics"])
            
            if event_type == "mic":
                self.mic_access_count += 1
                console.log_handle(f"Mic poll #{self.mic_access_count} - Audio captured")
                
            elif event_type == "exfil":
                self.file_exfil_count += 1
                file = random.choice(EXFIL_FILES)
                server = random.choice(C2_SERVERS)
                console.log_exfil(f"File access: {file}")
                console.log_exfil(f"Exfiltration -> {server}")
                
            elif event_type == "c2":
                self.c2_beacon_count += 1
                server = random.choice(C2_SERVERS)
                console.log_c2(f"C2 Heartbeat #{self.c2_beacon_count} -> {server}")
            
            elif event_type == "physics":
                # Add some "smart" looking physics logs
                entropy += random.uniform(0.1, 0.5)
                coherence -= random.uniform(0.1, 0.8)
                console.log_heuristic(f"System Entropy: {entropy:.4f} J/K | Quantum Coherence: {coherence:.2f}%")
                
            elif event_type == "whisper":
                whisper_count += 1
                
                if whisper_count <= 3 and long_whispers:
                    phrase = random.choice(long_whispers)
                    long_whispers.remove(phrase)
                else:
                    phrase = random.choice(short_whispers)
                
                console.log_event(f"Subject: \"{phrase}\"")
                
                voice = "en-US-AnaNeural" if use_female_voice else VOICE
                use_female_voice = not use_female_voice
                
                self.speak_async_with_voice(phrase, voice)
                
                # SMART TIMING: Calculate exact duration to prevent overlap
                duration = self.estimate_speech_duration(phrase)
                # Wait for speech to finish + small buffer before next event loop
                await asyncio.sleep(duration + 0.5)

if __name__ == "__main__":
    app = CortexApp()
    app.run()
