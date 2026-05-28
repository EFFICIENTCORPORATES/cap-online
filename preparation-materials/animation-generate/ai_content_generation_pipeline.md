# AI-Based Content Generation Pipeline
### Principle: 95% Automation > 100% Manual Accuracy. Speed wins.

---

## Section 1: YouTube Long-Form Video

### Video Type: Tutorial Video (Python / Finance Automation)

**Format:** 5–12 minutes | Screen-heavy | Small avatar bottom-right | Genuine intro + outro

---

### Pre-Production (Fully Automated)

#### Step 1 — Build the Use Case & Code
- Collect input files and sample data
- Use **GitHub Copilot / ChatGPT** to generate Python code for the use case
- Test the code yourself — confirm it runs
- Ask AI to convert the script to `.ipynb` (Jupyter Notebook) format with step-by-step explanations per cell

#### Step 2 — Generate HTML Slides
- Ask **Claude / ChatGPT** to generate an HTML file containing:
  - Background: what is being automated
  - Input → Output explanation
  - Use cases and real-world context
  - Embedded Jupyter-style code blocks
- This HTML file will be the visual backdrop during screen recording

#### Step 3 — Generate the Script
- Feed the use case, HTML content, and notebook to **Claude / ChatGPT**
- Ask it to generate a **timestamped script** — every 3 seconds, what to say and what to show
- Ask it to embed **SSML tags** for ElevenLabs:
  - Stress, pauses, excitement, tone markers
- Output: a production-ready script with timestamps + SSML markup

**Sample Prompt:**
```
You are writing a voiceover script for a 7-minute Python tutorial video 
about automating GST reconciliation. Generate a timestamped script 
(every 3 seconds) with SSML tags for ElevenLabs. Include stress markers, 
pause durations, and excitement cues where appropriate.
```

---

### Voice & Avatar Generation (Fully Automated)

#### Step 4 — Generate Voiceover
- Feed the SSML-tagged script to **ElevenLabs**
- Use your cloned voice (trained on your voice samples)
- Output: a `.mp3` voiceover file that sounds exactly like you

#### Step 5 — Generate Talking Head Avatar
- Use **D-ID or Synthesia**
- Input: your photo + the ElevenLabs `.mp3`
- Output: a short video of your face nodding and moving lips — used as the 5% bottom-right picture-in-picture

---

### Production (Intern-Assisted)

#### Step 6 — Screen Recording
- Intern wears headphones, listens to the generated voiceover
- Intern moves the screen — HTML slides, Jupyter Notebook, VS Code — exactly as the timestamped script says
- Records using **OBS Studio** (free) or ScreenFlow (Mac)
- No speaking required. No fumbling. Screen follows the voice.

#### Step 7 — Video Stitching & Editing
- Editor imports into **DaVinci Resolve** (free):
  - Layer 1: Screen recording
  - Layer 2: ElevenLabs voiceover (already timestamped)
  - Layer 3: Avatar video (bottom-right corner, ~5% screen)
- Use timestamp markers from script to align layers
- Add genuine intro (you, 10 seconds) at the start
- Add genuine outro (you, 10–15 seconds) at the end
- Edit any fumbles manually if needed

---

### Post-Production (Fully Automated)

#### Step 8 — Title Generation
- Input: the full script
- Tool: **Claude / ChatGPT**
- Prompt:
```
Based on this Python tutorial script, generate 5 YouTube titles. 
Each title must hook in the first 3 words. Focus on problem-solution angle. 
Keep under 60 characters.
```
- Pick one. Done.

#### Step 9 — Description Generation
- Input: the full script + timestamps
- Tool: **Claude / ChatGPT**
- Prompt:
```
Generate a YouTube description for this tutorial. Include:
- Hook paragraph (2 lines)
- Bullet-pointed key learnings
- Timestamp markers for each section
- Placeholder for GitHub link
```
- Paste and upload. Done.

---

## Section 2: Thumbnail Generation (Common Across All Video Types)

**Style:** Bold text + your face on colored background
**Principle:** Full automation. No Canva. No manual design.

### Flow:

#### Step 1 — Generate Thumbnail Text
- Tool: **Claude**
- Input: video topic / script summary
- Prompt:
```
This video is about [topic]. Generate 3 thumbnail text options.
Each must be 5–7 words, bold and punchy. Also suggest a background 
colour from orange (#F7941D), green (#2D7D32), or blue.
```
- Pick the best option

#### Step 2 — Generate Thumbnail Image
- Tool: **ChatGPT (GPT Image / gpt-image-1)**
- Input: your photo + Claude's thumbnail text suggestion
- Prompt:
```
Take this photo of me. Place me on a bold [orange/green] background. 
Add large bold white text saying "[THUMBNAIL TEXT]". 
Make my expression look [shocked/confident/curious]. 
Style it like a high-CTR YouTube thumbnail. 1280x720 pixels.
```
- Regenerate 3–4 times
- Pick the best version
- Download. Upload directly to YouTube.

**Total time: under 5 minutes per thumbnail. Zero manual design.**

---

## Full Pipeline at a Glance

```
Use Case Idea
     ↓
AI → Code + Notebook + HTML Slides          [Copilot / ChatGPT]
     ↓
AI → Timestamped Script + SSML Tags         [Claude / ChatGPT]
     ↓
AI → Voiceover (.mp3)                       [ElevenLabs]
     ↓
AI → Talking Head Avatar                    [D-ID / Synthesia]
     ↓
Intern → Screen Recording (follows voice)   [OBS Studio]
     ↓
Intern → Video Stitching + Edit             [DaVinci Resolve]
     ↓
You → Genuine Intro + Outro (20 sec total)
     ↓
AI → Title + Description                    [Claude / ChatGPT]
AI → Thumbnail                              [ChatGPT GPT Image]
     ↓
Manual → Upload to YouTube / LinkedIn
```

---

## Division of Labour

| Who | What | Time Estimate |
|-----|------|---------------|
| **You** | Use case idea, code testing, intro/outro recording, final approval | ~30 min |
| **AI Tools** | Code, slides, script, voice, avatar, title, description, thumbnail | ~15 min |
| **Intern/Editor** | Screen recording, video stitching, timestamp sync | ~60–90 min |

**Total your time per video: ~30–45 minutes.**

---

## Tools Summary

| Stage | Tool | Cost |
|-------|------|------|
| Code generation | GitHub Copilot / ChatGPT | Paid |
| Slides + Script | Claude / ChatGPT | Paid |
| Voice cloning | ElevenLabs | Paid |
| Talking head avatar | D-ID / Synthesia | Paid |
| Screen recording | OBS Studio | Free |
| Video editing | DaVinci Resolve | Free |
| Title + Description | Claude / ChatGPT | Paid |
| Thumbnail image | ChatGPT GPT Image | Paid (Plus) |

---

*Built for solo CA educators running tutorial-based YouTube and LinkedIn channels.*
*Optimised for speed and automation. Manual intervention only where unavoidable.*
