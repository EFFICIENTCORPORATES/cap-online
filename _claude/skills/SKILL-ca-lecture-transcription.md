# SKILL — CA Lecture Transcription and Roman Hinglish Pipeline

## Purpose

Use this skill whenever working on CA Pranav Pratik Tulshyan's CA Inter lecture audio/video transcription pipeline.

The objective is **high-quality, timestamped, Roman-script Hinglish transcripts** for CA Inter Advanced Accounting lectures, with technical accounting terminology preserved in English and raw ASR output retained for traceability.

This skill records the decisions and experimental learnings already established so future agents do not repeat the same tests or regress to known-bad settings.

---

## 1. Storage architecture and source of truth

The pipeline has three distinct media layers:

1. **Google Drive original lecture source**
   - Historical source only.
   - Full archive has already been copied to Cloudflare R2.
   - Do not depend on Drive availability for downstream work.

2. **Cloudflare R2 source-video archive**
   - Prefix: `source-videos/`
   - This is the durable source-video backup.
   - Never use `rclone sync` against this archive.
   - Use copy/read-only processing so source deletions elsewhere cannot propagate into R2.

3. **Cloudflare R2 audio archive**
   - Prefix: `audio/`
   - Mirrors the source-video folder hierarchy.
   - MP3 generation convention:
     - mono
     - 16 kHz
     - 64 kbps
   - Audio extraction workflow: `.github/workflows/r2-build-audio-archive.yml`

At the time this skill was written, the audio workflow had verified the complete video set:
- 70 source video files
- 70 verified MP3 audio files
- 0 missing
- 0 empty

Use R2 audio as the normal transcription input. Do not redownload source MP4s for transcription unless there is a specific reason.

---

## 2. Current bulk-transcription status

**Bulk transcription of the full lecture archive has NOT yet been approved or run.**

Completed:
- Drive -> R2 source backup
- R2 source video -> R2 MP3 audio
- model/GPU experiments
- one downloadable 5-minute QA transcription workflow
- Romanization prototype

Pending:
- teacher approval of transcript quality
- final production transcription settings
- bulk transcription of all R2 audio

Do not claim the entire archive has been transcribed unless a later manifest proves it.

---

## 3. Language policy

Pranav's classes are naturally **Hindi + English + Hinglish**, with heavy English accounting terminology.

The desired human-readable output is **Roman-script Hinglish**, for example:

`Agar asset ki value kam ho jaati hai to impairment loss recognise karna padega.`

Not:

`अगर asset की value कम हो जाती है...`

And not a translation such as:

`If the value of the asset decreases, an impairment loss must be recognised.`

The goal is **transliteration / Romanization, not translation**.

Technical vocabulary should remain normal English wherever spoken or recognized, including terms such as:
- ICAI
- Accounting Standard / AS
- property, plant and equipment
- inventory
- depreciation
- impairment
- carrying amount
- fair value
- provision
- contingent liability
- journal entry
- debit / credit
- recognition / measurement

---

## 4. Preserve raw ASR and Romanized output separately

Do not destroy the original Whisper output.

Recommended output model:

```json
{
  "start": 755.0,
  "end": 760.0,
  "raw_text": "अगर asset की value कम हो जाती है तो impairment होगा",
  "romanized_text": "Agar asset ki value kam ho jaati hai to impairment hoga"
}
```

Why:
- raw output can be reprocessed later with a better Romanizer;
- transcription does not need to be rerun merely to improve transliteration;
- disputes can be traced back to what the ASR actually produced.

Human-facing Markdown/TXT should normally show Roman Hinglish.
Machine-readable JSON should retain both raw and Romanized text.

---

## 5. Important model experiments already performed

Do not repeat these blindly.

### Test A — faster-whisper `small`, auto language

Configuration:
- model: `small`
- device: CUDA RTX 3050
- compute_type: `float16`
- language: `None` / auto detect
- beam_size: 5
- word_timestamps: true
- VAD: true
- 5-minute clip

Observed:
- processing time: about 92.2 s
- speed: about 3.25x realtime
- segments: 50
- detected language: Hindi
- visually, this was the best of the early tests

### Test B — faster-whisper `medium`, forced Hindi

Configuration changed both model and language setting, so this was **not a perfect apples-to-apples model comparison**.

Observed:
- processing time: about 164.0 s
- speed: about 1.83x realtime
- segments: 19
- language probability: about 0.766
- transcript appeared worse / less useful than the earlier small+auto run

### Test C — faster-whisper `small`, forced Hindi

Observed:
- processing time: about 86.9 s
- speed: about 3.45x realtime
- segments: 14
- reported language probability: 1.000
- output quality visibly degraded

**Key conclusion:** forcing `language="hi"` is not preferred for these Hinglish lectures.

The `1.000` language probability in the forced-Hindi test is not evidence of better recognition; the language was supplied to the decoder.

### Current preferred baseline

Use:

```python
WhisperModel(
    "small",
    device="cuda",
    compute_type="float16",
)
```

and:

```python
model.transcribe(
    AUDIO,
    language=None,
    beam_size=5,
    word_timestamps=True,
    vad_filter=True,
    condition_on_previous_text=True,
    initial_prompt=...
)
```

Do not force Hindi unless a later controlled benchmark proves it better.

---

## 6. Why auto language is important here

These lectures are code-switched.

Forcing Hindi can push the decoder toward Hindi-language/script behavior and can worsen recognition of:
- English accounting terms
- abbreviations
- names
- CA terminology
- technical phrases spoken inside otherwise-Hindi sentences

Treat the lecture as **Hinglish speech**, not pure Hindi speech.

---

## 7. Initial prompt policy

An accounting-domain initial prompt is useful, but it must guide rather than rewrite.

Current prompt family:

```text
CA Intermediate Advanced Accounting lecture.
The speaker may use Hindi, English and Hinglish.
Accounting terminology may include ICAI, Accounting Standards,
assets, liabilities, inventory, depreciation, impairment,
recognition, measurement, financial statements and journal entries.
```

Expand chapter-specific terminology when useful, but do not make the prompt so aggressive that it hallucinates expected vocabulary.

For AS 10, for example, domain terms may include:
- PPE
- property, plant and equipment
- cost
- recognition
- measurement
- depreciation
- residual value
- useful life
- carrying amount
- impairment
- derecognition

---

## 8. Timestamp policy

Word timestamps are required.

The established output convention is **5-second windows**, assigning each recognized word to the bucket containing its word-start timestamp.

Recommended human-readable form:

```text
[00:12:35 - 00:12:40]
Agar asset ki value kam ho jaati hai to impairment hoga.
```

Keep raw segment/word timing in JSON even if Markdown is windowed.

---

## 9. QA methodology before bulk transcription

Do not approve a production model based only on:
- language probability
- number of segments
- speed
- apparent fluency

Use a paired audio/text review.

Established QA workflow:
`.github/workflows/test-transcription-5min.yml`

Default test source:
`audio/3. AS-10/Lecture 4-AS 10 Property Plant and Equipment.mp3`

The workflow:
1. downloads the selected R2 MP3;
2. finds the exact middle of the lecture;
3. extracts a 5-minute playable clip;
4. transcribes only that clip;
5. produces raw transcript;
6. produces Romanized transcript;
7. uploads the test package to R2;
8. exposes it as a downloadable GitHub Actions artifact.

Expected QA package:
- `test-clip.mp3`
- `transcript-raw.md`
- `transcript-romanized.md`
- `transcript-romanized.txt`
- `transcript.json`
- `test-info.json`

The teacher should listen to the clip while reading the Romanized transcript.

Evaluate particularly:
- accounting terms
- numbers and percentages
- AS numbers
- journal-entry wording
- names
- Hindi explanation
- English code-switches
- omissions
- hallucinations
- timing alignment

---

## 10. Romanization implementation

Prototype helper:
`tools/test_transcription_clip.py`

Current prototype uses `indic-transliteration` to convert Devanagari spans while preserving existing English tokens.

This is a **baseline Romanizer**, not guaranteed to reproduce the teacher's preferred casual Hinglish spelling.

Important:
- Romanization should not translate meaning.
- Existing English technical terms must remain English.
- Do not transliterate already-correct English words.
- Retain raw text beside Romanized text.
- If Romanization style is later improved, regenerate from raw transcript instead of rerunning Whisper.

---

## 11. GPU environment already proven locally

Workstation tested:
- NVIDIA GeForce RTX 3050
- 6 GB VRAM
- CUDA visible to CTranslate2

Local project:
`D:\Efficient-Content-Pipeline\transcription-pipeline`

Python:
- uv-managed CPython 3.11
- `faster-whisper==1.2.0`
- `av==16.0.1`
- CTranslate2 CUDA device count confirmed as 1

Required Python CUDA packages discovered through testing:
- `nvidia-cublas-cu12`
- `nvidia-cudnn-cu12`
- `nvidia-cuda-runtime-cu12`

On a fresh PowerShell, temporary PATH used:

```powershell
$env:PATH = "$PWD\.venv\Lib\site-packages\nvidia\cublas\bin;$PWD\.venv\Lib\site-packages\nvidia\cudnn\bin;$PWD\.venv\Lib\site-packages\nvidia\cuda_runtime\bin;$env:PATH"
```

Known failure that led to this:
`RuntimeError: Library cublas64_12.dll is not found or cannot be loaded`

Model loading alone was not considered enough; actual inference had to succeed.

Production automation should make CUDA DLL setup automatic rather than requiring manual PATH edits each session.

---

## 12. Production architecture recommendation

Keep archive and transcription separate.

### A. Archive
Google Drive -> R2 source-videos

### B. Audio derivative
R2 source-videos -> R2 audio

### C. Transcription
R2 audio -> GPU transcription -> raw transcript + Romanized transcript -> R2 + Git text working copy

### D. Notes/content generation
Approved transcripts + ICAI/annotated/class-note sources -> concept/revision outputs

Do not recombine all phases into one giant fragile job.

Prefer one lecture per checkpoint/job so processing is resumable.

---

## 13. Recommended production transcript outputs

Per lecture:

```text
transcript-raw.md
transcript-romanized.md
transcript-romanized.txt
transcript.json
transcript.srt
transcript.vtt
manifest.json
```

Suggested JSON should retain:
- source R2 audio key
- model
- compute type
- language mode
- initial prompt/version
- detected language
- language probability
- raw segments
- word timestamps
- 5-second windows
- raw text
- Romanized text
- generation timestamp
- transcription status

---

## 14. Production safety rules

- Never delete or overwrite R2 source videos as part of transcription.
- Prefer reading from `audio/`, not downloading MP4s.
- Do not use `rclone sync` for archive safety.
- Delete only local temporary audio after successful output verification.
- Make jobs restart-safe/idempotent.
- Skip already-completed verified lecture outputs.
- Keep manifests.
- Do not call a lecture complete unless output validation passes.
- Do not start bulk transcription until the teacher approves QA quality.
- A transcript is teaching evidence, not accounting authority.
- Numbers/technical terms that are uncertain should be marked for review, not silently guessed.

---

## 15. Current known workflow caveat

The first 5-minute QA workflow successfully:
- downloaded the selected R2 audio;
- extracted the middle 5-minute clip;
- transcribed it;
- Romanized it;
- uploaded the package to R2;
- created a downloadable GitHub artifact.

That workflow's overall GitHub run was shown as failed only because the final repository-wide `tools/health_check.py` step found unrelated pre-existing missing folders.

Do not interpret that run-level failure as a transcription failure.

Future QA workflow cleanup should remove or decouple that unrelated repository health gate.

---

## 16. What a new agent should do next

Before building bulk transcription:

1. Read this skill.
2. Read `books/ca-inter/concept-book/CONCEPT_BOOK_NOTES_PIPELINE.md`.
3. Read the 2026-10-03 and 2026-10-04 entries in `_claude/memory/project_log.md`.
4. Inspect `.github/workflows/test-transcription-5min.yml`.
5. Inspect `tools/test_transcription_clip.py`.
6. Review the actual QA audio + transcript artifact if still available, or run a new QA test.
7. Get teacher approval on transcript quality.
8. Only then design/run the bulk GPU transcription stage.

The correct default starting point is **small + CUDA float16 + language auto-detection + word timestamps + VAD + accounting-domain prompt + raw-text preservation + Romanization as a separate post-processing layer**.

Do not regress to forced Hindi or immediate bulk transcription without evidence.
