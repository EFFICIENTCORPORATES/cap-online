# Content Creation Tool Stack
### YouTube & LinkedIn Tutorial Videos — AI-Powered Pipeline

---

## Stage 1: Script & Content Generation

| Tool | Purpose |
|------|---------|
| **ChatGPT / Claude** | Write timestamped scripts with SSML markup, generate use case descriptions |
| **GitHub Copilot** | Generate Python code, convert scripts to `.ipynb` notebooks |
| **Claude / ChatGPT** | Generate HTML slides with background, input/output explanations, use cases |

---

## Stage 2: Voice Generation

| Tool | Purpose |
|------|---------|
| **ElevenLabs** | Clone your voice using voice samples; generate voiceover from SSML-tagged script |

> **Note:** ElevenLabs supports SSML syntax for controlling stress, pauses, excitement, and tone. Ask AI to embed SSML tags directly in the script before sending to ElevenLabs.

---

## Stage 3: Avatar / Picture-in-Picture

| Tool | Purpose |
|------|---------|
| **D-ID** | Generate talking head video from your photo + cloned voice |
| **Synthesia** | Alternative avatar tool for picture-in-picture talking head |

> Use either for the small (5%) bottom-right corner avatar that appears while the screen is being recorded.

---

## Stage 4: Screen Recording

| Tool | Purpose |
|------|---------|
| **OBS Studio** | Free, cross-platform screen recording (recommended) |
| **ScreenFlow** | Mac-only alternative with built-in editing |

> **Workflow:** Intern listens to the generated voiceover through headphones and moves the screen accordingly in real time, following the timestamped script.

---

## Stage 5: Video Editing & Syncing

| Tool | Purpose |
|------|---------|
| **DaVinci Resolve** | Free, professional-grade editing; supports timestamp markers and batch operations |
| **Adobe Premiere Pro** | Alternative if intern is already familiar with Adobe ecosystem |
| **Descript** | Semi-automated syncing based on audio transcription (optional assist) |

> **Workflow:** Import timestamped markers from the script into the editor. Stitch screen recording + voiceover + avatar. Edit any fumbles manually.

---

## Stage 6: Code & Asset Hosting

| Tool | Purpose |
|------|---------|
| **GitHub** | Host Python files, notebooks, and source code linked in video description |
| **Simple HTML/Portfolio Site** | Host use case pages with input/output demos |

---

## Full Pipeline Summary

```
Idea / Use Case
     ↓
AI generates: Script (timestamped + SSML) + HTML Slides + Jupyter Notebook
     ↓
ElevenLabs generates: Voiceover (cloned voice)
     ↓
D-ID / Synthesia generates: Talking head avatar
     ↓
Intern records: Screen recording (listening to voiceover in ear)
     ↓
Editor stitches: Screen + Voice + Avatar → Final Video
     ↓
Genuine Intro (you) + Tutorial Body (AI-assisted) + Genuine Outro (you)
     ↓
Upload to YouTube / LinkedIn with GitHub link in description
```

---

## Division of Labour

| Who | What |
|-----|------|
| **You** | Idea, use case, genuine intro/outro (10 sec each), final review |
| **AI Tools** | Script, code, slides, notebook, voice, avatar |
| **Intern/Editor** | Screen recording, video stitching, timestamp syncing, final edit |

---

*Stack designed for 5–12 minute Python tutorial videos for YouTube and LinkedIn.*
