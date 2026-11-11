# KeyChord AI — Architecture

## 1. System overview

```
 Browser (React/TS/Vite/Tailwind)
   │  REST (JSON) + audio streaming via HTTP Range
   ▼
 FastAPI app ──────────► PostgreSQL  (users, songs, analyses, chords, notes, voicings)
   │  enqueue = INSERT analyses(status='queued')
   │  files   = StorageBackend (LocalStorage → S3 later)
   ▼
 Worker process (python -m app.worker)   ← separate OS process, same codebase
   polls: SELECT … WHERE status='queued' FOR UPDATE SKIP LOCKED
   runs : audio pipeline (CPU/GPU heavy), writes results + progress back to Postgres
```

**Why a DB-backed job queue instead of Celery/Redis:** the spec says no unnecessary services.
`analyses.status/stage/progress/started_at` already model a job. `FOR UPDATE SKIP LOCKED` gives safe
multi-worker claiming. If load grows, swap the poller for Celery/RQ without touching the API contract.
**Why not FastAPI BackgroundTasks:** it runs inside the web process; a 3-minute CPU-bound job would starve the API
and a crash/restart loses it. The worker is isolated, restartable, and enforces the processing timeout.

Stale-job recovery: a `running` analysis whose `started_at` is older than the timeout is marked `failed`.

## 2. Audio pipeline (Phase 4–5)

1. **Probe & validate** – sniff magic bytes (not extension), read duration with mutagen/soundfile, enforce
   size/duration limits, then confirm librosa/ffmpeg can actually decode (handles malformed files; M4A needs ffmpeg).
2. **Normalise** – mono, 22,050 Hz float32, peak-normalise. Long files decoded in blocks (`soundfile.blocks` /
   `librosa.stream`) to avoid loading everything at once where the algorithm allows.
3. **HPSS** – `librosa.effects.hpss` keeps the harmonic part; drums smear chroma otherwise.
4. **Tuning** – `librosa.estimate_tuning`, then compensate (recordings are often a few cents off A440).
5. **Features** – CQT chroma (36 bins/oct → fold to 12, CENS-style smoothing) for the *full* spectrum, plus a
   separate **bass chroma** (~40–250 Hz) for root/inversion evidence.
6. **Segmentation** – beat tracking → beat-synchronous chroma; chord changes are decoded per beat, not per
   arbitrary window, so boundaries line up with musical time. Fallback to fixed hop when tempo is unreliable.
7. **Chord decoding** – see §3.
8. **Key estimation** – see §4.
9. **Persist** – chords, key + alternatives, tempo, per-chord confidence; progress updates between stages.

Phase 11 inserts an optional step 2.5: **Demucs** → "other" (+bass) stem feeding steps 3–7, and a parallel
**Basic Pitch** note-transcription path producing `detected_notes` + MIDI.

## 3. Chord recognition approach

Chosen baseline: **template matching + HMM/Viterbi smoothing**, not a black-box model.

- Templates for all 12 required qualities × 12 roots (maj, min, dim, aug, maj7, min7, 7, sus2, sus4, add9, dim7, m7b5),
  weighted (root/third/fifth > extensions) and **overtone-aware** (a note also contributes energy to its 2nd/3rd harmonics
  in chroma, so templates are built from simulated harmonic series rather than 0/1 masks).
- Score each beat-frame by cosine similarity against the combined (full + bass-weighted) chroma → emission scores.
- **Viterbi decode** with a transition model: strong self-transition (chords persist), small prior favouring
  diatonic-to-the-estimated-key moves *as a soft prior only*. This reduces flicker without “guessing from the key”.
- **Confidence** = margin between best and runner-up emission, combined with path stability. Below a threshold the chord is
  flagged `uncertain` for manual correction.
- **Bass/inversion** – lowest sustained bass-chroma peak vs chord tones → inversion index / slash bass.
- **Complexity control** – extended qualities (7ths, add9, sus) get a penalty so a triad is preferred unless evidence is
  clear; this matches how real chord sheets behave and is the main lever for precision.
- The decoder sits behind a `ChordRecognizer` interface so a trained model can replace it later and be compared on the
  same evaluation harness.

## 4. Key detection
Aggregate chroma (and chord-duration-weighted root/quality histogram) → correlate with Krumhansl–Schmuckler /
Temperley major & minor profiles over all 24 keys → softmax-normalised scores give a **confidence** and the top-3
**alternatives**; relative major/minor derived from the winner. Modulations are flagged later via windowed estimates.

## 5. Voicing, hands, transposition
Three separate concepts, stored and displayed separately, never merged in the UI:
1. **Detected chord** (harmonic label, from audio)
2. **Transcribed notes** (Basic Pitch events — Phase 11)
3. **Suggested voicing** (rule-based: LH root(+fifth) around C2–C3, RH triad/7th inversion nearest the previous voicing
   for smooth voice-leading). Always labelled *suggested*; `voicing_type` records provenance.
Transposition is a pure function on (root, quality, bass, voicing notes) with enharmonic spelling chosen from the target key;
it never touches audio or the stored original analysis.

## 6. API contract (Phase 3+)
`POST /api/songs/upload` → `POST /api/songs/{id}/analyze` (returns `analysis_id`, 202) → client polls
`GET /api/analyses/{id}` (status/stage/progress) → `GET …/chords`, `…/notes`, `POST …/transpose`, `PATCH|DELETE /api/chords/{id}`,
`GET …/export?format=pdf|txt|json`. Audio streaming endpoint supports Range for seeking.

## 7. Security
Server-generated storage keys only; `LocalStorage` resolves and asserts containment (tested). Magic-byte validation; streamed
uploads with hard byte cap; per-job timeout; temp-file cleanup in `finally`; ownership checks on every song/analysis route
(dev user until auth is enabled); secrets only via env; DB transactions per request via `get_db`.

## 8. Known technical limitations (be honest with users)
- **Accuracy ceiling**: published systems reach roughly 75–85% on major/minor vocabulary for pop/rock, notably less on
  7ths/sus/add9 and on dense or heavily processed mixes. Never present results as exact.
- **Voicing/octave cannot be recovered from a chord label**; suggested voicings are playable arrangements, not the original performance.
- **Hand assignment is an estimate** (pitch-split + proximity heuristic); real players cross hands.
- **Demucs "other" stem** mixes keys with guitars, strings and pads — it improves harmony analysis but is not a clean keyboard track.
- **Basic Pitch** is polyphonic-capable but loses accuracy on dense chords, reverb, and fast passages.
- **Key changes, borrowed chords, and non-12-TET/ detuned recordings** reduce confidence.
- **Compute**: Demucs wants ≥8 GB RAM (GPU strongly preferred; ~minutes per song on CPU); Basic Pitch needs TensorFlow/ONNX;
  baseline librosa path is light (<2 GB, tens of seconds per song).
- **ffmpeg** is required for M4A and other compressed containers.
- **Copyright**: users upload songs they don't necessarily own; add terms of use and keep files private per user.
- **Ground truth**: evaluation needs manually verified transcriptions (e.g. Isophonics/Billboard-style annotations or your own);
  evaluation uses `mir_eval` (WCSR, segmentation, overlap ratio).

## 9. Roadmap & exit criteria
| Phase | Deliverable | Exit test |
|---|---|---|
| 1 | Repo, config, DB schema+migration, storage layer, health, FE skeleton | `alembic upgrade head` OK; `/api/health/db` OK; storage traversal tests pass |
| 2 | Layout, routing, dashboard, design system | Responsive pages render w/ empty states (no fake data) |
| 3 | Upload API + UI, validation, progress, player, waveform | Bad/renamed/corrupt files rejected; valid file plays and seeks |
| 4 | Worker + pipeline stages (decode→HPSS→chroma) | Synthetic tones give correct chroma peaks |
| 5 | Chord decoder + confidence | Synthesised chord progressions recovered; mir_eval harness running |
| 6–8 | Timeline, piano, sync | Active chord follows `audio.currentTime`; click-to-seek |
| 9 | Key detection + transposition | Property tests: transpose(+n) then (−n) is identity |
| 10 | Export PDF/TXT/JSON | Round-trip tests |
| 11 | Demucs + Basic Pitch, MIDI | Measured note F1 on test clips |
| 12 | Tests, security, perf | Accuracy report across genres; load/timeout tests |

## 10. Dependencies
System: Python 3.11, Node 20+, PostgreSQL 16 (Docker provided), ffmpeg, libsndfile.
Python: see `backend/requirements.txt` (API) and `backend/requirements-audio.txt` (DSP/ML).
Node: see `frontend/package.json`.
