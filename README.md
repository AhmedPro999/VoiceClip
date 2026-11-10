# 🎙 VoiceClip

**Talk ⇒ Write ⇒ Trans** · Windows
**Hold, speak Arabic, release.. and the text is in your clipboard.**

A lightweight Windows utility that sits in your system tray next to the clock. Hold a hotkey and speak in Arabic (Modern Standard Arabic or Egyptian dialect), and the moment you release the key, your speech is transcribed and copied directly to your clipboard—ready to paste anywhere: WhatsApp, chat apps, documents, or emails. It also includes a second hotkey that instantly translates your spoken Arabic into natural, professional English.

---

## Features

|  |  |
| --- | --- |
| 🎙 **Push-to-Talk** | No second key to stop. As long as you hold the hotkey, it records; the moment you let go, it starts processing. |
| 🇪🇬 **Understands Egyptian Arabic** | Not limited to formal Arabic. Everyday Egyptian phrases like *"إزيك عامل إيه النهارده"* are transcribed just as you say them. |
| 🌍 **Professional Translation** | `Alt+E` translates your spoken Arabic into natural, idiomatic English based on meaning—not literal word-for-word translation. |
| 📋 **Straight to Clipboard** | Text is copied automatically. Includes an optional setting to auto-paste directly at your cursor without pressing `Ctrl+V`. |
| 💊 **Modern Status Pill** | A sleek, non-intrusive pill overlay at the bottom of the screen: red for recording, yellow for processing, green when done. Fades in and out smoothly without stealing window focus. |
| 🧠 **Powered by Gemini** | Uses Google Gemini with a free API key. It processes the audio natively, handling both transcription and translation in a single request. |
| 🔁 **Automatic Fallback** | If the primary model is busy, hits a rate limit, or encounters a network hiccup, it automatically retries with a fallback model. |
| 🔇 **Silence Detection** | If no audio is detected, it alerts you immediately without sending a request—saving your API quota. |
| 📜 **20-Item History** | Access your last 20 transcriptions from the tray icon menu; click any past entry to copy it again. |
| 🔌 **Offline Mode (Optional)** | Run Whisper + a local translation model completely offline on your machine if you have an NVIDIA GPU and don't mind a one-time large download. |

---

## Installation (One-time setup, 5 minutes)

### 1. Python

If not already installed, download it from [python.org/downloads](https://www.python.org/downloads/) (version 3.11 or newer).
**Make sure to check "Add Python to PATH" during installation**—without it, `install.bat` won't be able to find Python.

### 2. Run `install.bat`

Double-click it and wait a minute or two (it downloads around 150 MB once). If your internet drops, just run it again and it will resume where it left off.

### 3. Gemini API Key (Free)

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and sign in with your Google account.
2. Click **Create API key** and copy the key.
3. Open `config.json` (automatically generated next to `install.bat`) using Notepad and paste your key between the quotes on this line:
```json
"api_key": "AIza...."

```


Save the file. *(Alternative: Set an environment variable named `VOICECLIP_API_KEY`.)*

### 4. Run `run.bat`

You will see a blue microphone icon appear in your system tray next to the clock (if hidden, click the little upward arrow `^`).

### 5. (Optional) Run on Windows Startup

Double-click `add_to_startup.bat` once. To remove it from startup later, delete:
`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\VoiceClip.lnk`

> **Did Windows Defender block the file?** This is common with new `.bat` scripts. Click **More info** and then **Run anyway**.

---

## Usage

| Action | Result |
| --- | --- |
| Hold **`Alt + A`**, speak Arabic, release | **Arabic** transcript in clipboard |
| Hold **`Alt + E`**, speak Arabic, release | **English** translation in clipboard |
| Press `Ctrl + V` anywhere | Pastes the text |

* **Audio cues:** Short beep = recording started. Higher-pitched beep = text copied. Low-pitched beep = failed.
* The status pill at the bottom of the screen shows the current stage and target language.
* Hotkeys work regardless of whether your keyboard layout is set to Arabic or English.
* The letters `A` and `E` are suppressed while holding the hotkey, so they won't be typed into your active window.

### Tray Icon Menu (Right-click the tray icon)

| Menu Item | Function |
| --- | --- |
| **Status & Hotkeys** | Display only |
| **On-Screen Status Pill** | Toggle the floating status pill at the bottom of the screen |
| **Auto-Paste at Cursor** | When enabled, inserts text directly at your active cursor without pressing `Ctrl+V` |
| **Windows Notifications** | Standard Windows toast notifications with the text (disabled by default; clipboard is populated either way) |
| **Sound Effects (Beeps)** | Toggle audio feedback beeps on or off |
| **Mode** | Switch between Online (Gemini) and Offline (Local) |
| **Re-copy Last Text** / **Re-copy Last Arabic Text** | Handy if you accidentally overwrote your clipboard |
| **History** | Shows your last 20 entries; click any item to copy it again |
| **Open Config File** / **Open Log File** | Quick access to `config.json` and `voiceclip.log` |
| **Exit** | Closes the application |

### When Something Fails

The status pill turns red and displays **"Recording Failed · Arabic/English"** along with the reason:

| Message | Meaning |
| --- | --- |
| **Recording too short** | You pressed and released the hotkey too quickly. Keep holding the key while you speak. |
| **No audible speech detected** | Your mic is muted or too far away. Nothing is sent to Google. |
| **Could not hear clear speech** | Audio was captured, but the model couldn't make out any words. Speak closer to the mic. |
| **Gemini free quota exceeded** | You hit the per-minute or daily rate limit. Wait a moment and try again. |
| **Invalid or revoked Gemini API key** | Double-check `api_key` in `config.json`. |
| **Cannot reach Google servers** | Check your internet connection. |

---

## Configuration (`config.json`)

| Key | Default | Description |
| --- | --- | --- |
| `hotkeys.arabic` / `hotkeys.english` | `alt+a` / `alt+e` | Global hotkeys. Examples: `ctrl+shift+r`, `alt+f9`, `win+space` |
| `mode` | `online` | `online` (Gemini/API) or `offline` (local processing) |
| `overlay` | `true` | Show the on-screen status pill |
| `auto_paste` | `false` | Automatically paste text at the active cursor |
| `notifications` | `true` | Enable Windows toast notifications |
| `sounds` | `true` | Enable audio feedback beeps |
| `online.provider` | `gemini` | `gemini`, `openai`, or `groq` |
| `online.api_key` |  | Your API key (or use the `VOICECLIP_API_KEY` environment variable) |
| `online.gemini.model` | `gemini-3.5-flash` | Primary model used for translation (more accurate) |
| `online.gemini.fast_model` | `gemini-3.5-flash-lite` | Fast model used for Arabic transcription (faster) |
| `online.gemini.fallback_models` | `["gemini-3.8-flash"]` | Automatically tried in order if the primary model fails |
| `online.gemini.reasoning_effort` | `low` | `low` is faster. Set to `medium` for more nuanced translations of long, complex sentences |
| `online.gemini.timeout_seconds` | `40` | Timeout per individual API request |
| `online.gemini.total_budget_seconds` | `100` | Maximum total time allowed (including retries) before giving up |
| `audio.min_seconds` | `0.4` | Minimum recording duration accepted |
| `audio.silence_peak` | `0.01` | Minimum audio peak threshold. If your mic is very quiet and triggers "No audible speech" while speaking, lower this to `0.005` |
| `offline.whisper_model` | `large-v3-turbo` | Or use `medium` / `small` for lower-spec hardware |
| `offline.device` | `auto` | `cuda` / `cpu` |

The tool reloads `config.json` before every recording, so any changes take effect immediately without restarting the app (except hotkey changes, which require a restart).

---

## Models & Free Quota

* VoiceClip communicates with Gemini via the **API** using your personal key. This is completely separate from the consumer Gemini web chat and has its own dedicated quota.
* The free tier has **per-minute (RPM) and per-day (RPD) limits** for each model, which reset daily. The API key itself never expires.
* Every hotkey press-and-release equals **one API request**. Normal daily usage rarely hits the limit.
* Arabic transcription uses `flash-lite` (faster response, higher quota), while English translation uses `flash` (higher accuracy). If either model hits its rate limit, VoiceClip automatically falls back to the other.
* Audio is compressed to MP3 in memory before uploading (12 seconds ≈ 47 KB) to keep requests fast even on slow connections.
* If Google updates or deprecates model names in the future, simply update `model` and `fast_model` in `config.json`.

### Alternative Providers

Change `online.provider` to `openai` or `groq` and put their respective API key in `api_key`. These providers use Whisper for speech-to-text followed by an LLM for translation (two sequential API calls instead of one).

---

## Offline Mode (Optional)

If you want to run VoiceClip with zero internet connection or without any external APIs:

1. Run `install_offline.bat` (downloads ~4 GB of packages: Whisper, CUDA, PyTorch, and the translation library). If your connection drops, re-run it to resume.
2. Switch the mode to **Offline** from the system tray menu.
3. On your first offline recording, it will perform a one-time download of the Whisper model (1.6 GB) and the NLLB translation model (2.4 GB).

* Runs on an NVIDIA GPU if available (4 GB VRAM is plenty); otherwise falls back to CPU (slower).
* Offline Arabic transcription quality is excellent. Offline translation via NLLB is solid, though less idiomatic than Gemini when handling heavy Egyptian slang.
* If you try switching to Offline Mode without installing the offline packages first, the tool will block the switch and notify you.

---

## Privacy

* **Online Mode:** Audio is sent directly from your machine to Google's Gemini API (or your chosen provider) for processing. No third-party middleman servers are involved.
* **Offline Mode:** Nothing ever leaves your computer.
* `voiceclip.log` is stored locally on your machine and logs transcribed text for troubleshooting. Delete it anytime, and avoid sharing it publicly.
* `config.json` contains your private API key. Never share it or commit it to GitHub (it is already listed in `.gitignore`).

---

## Troubleshooting

| Issue | Solution |
| --- | --- |
| **No icon in the system tray** | Run `run_debug.bat` to keep a console window open and see the exact error message. |
| **Hotkey doesn't work inside a specific app** | Apps running as Administrator block global hotkeys from standard-privilege apps. Run `run.bat` as Administrator. |
| **"API key required" error** | Your key is missing from `config.json` or formatted incorrectly. |
| **Slow response times** | Usually network latency. Try setting `fast_model` for everything, or switch to Offline Mode. |
| **Auto-paste isn't pasting** | The target window is likely running as Administrator (see above). |
| **"No audible speech" while speaking clearly** | Lower `audio.silence_peak` in `config.json` to `0.005`. |
| **Need more details?** | Open `voiceclip.log` from the tray menu—every step is logged with timestamps. |

---

## Project Structure

```text
VoiceClip/
├── app.py                   # Entry point: system tray icon and menu (Qt)
├── voiceclip/
│   ├── hotkeys.py           # Global hotkeys: push-to-talk via scan codes (pynput, layout-independent)
│   ├── recorder.py          # 16 kHz microphone audio capture
│   ├── pipeline.py          # Core workflow: record → transcribe → translate → clipboard → paste → overlay
│   ├── gemini.py            # Gemini integration: direct audio upload, JSON output (AR + EN), auto-fallback
│   ├── transcriber.py       # Offline Whisper / Online Whisper via OpenAI or Groq
│   ├── translator.py        # Offline translation (NLLB) / LLM-based translation
│   ├── overlay.py           # Floating status pill (Qt): rounded corners, shadow, fade animations, pulsing dot
│   ├── notifier.py          # Windows toast notifications and audio beeps
│   ├── settings.py          # Read/write handler for config.json
│   └── log.py               # Logging setup for voiceclip.log
├── config.example.json      # Template—copy to config.json and add your API key
├── requirements.txt         # Core dependencies (Online Mode)
├── requirements-offline.txt # Optional dependencies (Offline Mode)
├── install.bat / install_offline.bat / run.bat / run_debug.bat / add_to_startup.bat
└── LICENSE                  # MIT

```

**How it works under the hood:** A low-level keyboard hook listens for hotkey press and release events using hardware scan codes (ensuring reliability regardless of whether Windows is set to Arabic or English input). Audio is recorded into memory, compressed to MP3 on the fly, and sent to Gemini with a system prompt requesting a structured JSON response containing both the Arabic transcript and English translation. The result is copied to the clipboard, optionally pasted, and displayed on the status pill.

---

## For Developers

```bash
git clone https://github.com/AhmedPro999/VoiceClip.git
cd VoiceClip
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy config.example.json config.json   # Then add your API key
.venv\Scripts\python app.py

```

* **Requirements:** Python 3.11+ on Windows. Core packages: `pynput`, `sounddevice`, `numpy`, `pyperclip`, `PySide6-Essentials`, `winotify`, `openai`, `lameenc`.
* **Adding a new provider:** Create a processor class similar to `GeminiProcessor` in `gemini.py` and wire it into `pipeline.py`.
* **Customizing the status pill UI:** Everything lives in `overlay.py` (adjust colors in `COLORS`, border radius in `RADIUS`, and padding in `row.setContentsMargins`).

## License

MIT. Free to use, modify, and distribute.
