# apexXuno - The Athanor's Voice

## Music Pipeline Masterplan

*"From intent to vibrating eardrums with a single invocation"*

---

## Vision

apexXuno transforms ApexAurum Cloud into a creative music platform where:
- Users generate AI music through intuitive interfaces
- Agents compose autonomously based on conversation context
- Musical creations become shared cultural memories in The Village
- The full pipeline flows: Intent → Compiler → Suno → Audio → Memory

**Name Origin:** apex + Suno, also reads as "ape × uno" (ape times one)

---

## Current State (v80)

### Backend - COMPLETE
- `SunoService` - Async API integration (submit/poll/download)
- `MusicTask` model with full metadata
- REST API with SSE streaming
- Audio stored in Vault (per-user)

### Agent Tools - BASIC
- `music_generate` - Start generation
- `music_status` - Check progress
- `music_list` - Browse library
- `music_download` - Get audio URL

### Frontend - COMPLETE (v80)
- `music.js` Pinia store with SSE streaming
- `MusicView.vue` - Full music studio UI
- `MusicPlayer.vue` - Spotify-style sticky bottom player
- Grid/list view with filters and search
- Real-time generation progress display
- Audio playback with waveform animation

### !MUSIC Trigger - COMPLETE (v81)
- `!MUSIC` detected in chat messages
- Auto-enables tools for music generation
- MUSIC_CREATION_CONTEXT injection with creative guidelines
- Full creative mode (no prompt) or expansion mode (user prompt)
- Agent composes detailed prompts with style tags

### What's Missing
- Prompt compiler as tool
- Village memory auto-injection
- Agent creative expansion (beyond basic)

---

## Phase 1: Frontend Music UI

### Goal
User-facing music experience - browse, play, create

### Components

```
frontend/src/views/MusicView.vue          # Main music page
frontend/src/components/music/
├── MusicLibrary.vue                      # Grid/list of tracks
├── MusicPlayer.vue                       # Persistent mini-player
├── MusicGenerator.vue                    # Creation form
├── MusicTrackCard.vue                    # Individual track display
└── MusicProgress.vue                     # SSE generation progress
```

### MusicLibrary Features
- Grid view with album-art style cards
- List view with details
- Filters: favorites, agent, status, search
- Sort: date, plays, duration
- Infinite scroll / pagination

### MusicPlayer Features
- Sticky mini-player at bottom (like Spotify)
- Play/pause, progress bar, volume
- Track info display
- Next/previous (if playlist)
- Expand to full player view

### MusicGenerator Features
- Prompt textarea with examples
- Style tag suggestions
- Model selector (V3.5 → V5)
- Instrumental toggle
- Advanced options (collapsed):
  - Mood selector
  - Purpose (SFX, ambient, loop, song)
  - Genre presets
- Live SSE progress during generation
- "Generating..." animation with status updates

### Routes
```javascript
/music              # Library view (default)
/music/create       # Generator form
/music/:id          # Single track detail view
```

### Store: `frontend/src/stores/music.js`
```javascript
// State
library: []
currentTrack: null
isPlaying: false
generationStatus: null
isGenerating: false

// Actions
fetchLibrary(filters)
generateTrack(params)        // SSE streaming
playTrack(taskId)
pauseTrack()
toggleFavorite(taskId)
deleteTrack(taskId)
```

---

## Phase 2: !MUSIC Trigger in Chat

### Goal
Enable agent creative mode through chat triggers

### Trigger Syntax
```
!MUSIC                              → Full creative mode
!MUSIC ambient rain meditation      → Agent expands prompt
!MUSIC [detailed prompt here]       → Agent refines and executes
```

### Implementation

**Backend: `chat.py`**
```python
# Detect !MUSIC trigger in user message
if message.strip().upper().startswith("!MUSIC"):
    music_prompt = message[6:].strip()  # Everything after !MUSIC

    # Inject music context into agent system prompt
    music_context = """
    [MUSIC CREATION MODE ACTIVATED]
    The user has requested music creation.

    If no prompt provided: Create based on conversation mood/context.
    If prompt provided: Expand it with rich style tags and emotional depth.

    Use the music_generate tool with your composed prompt.
    Be creative with style tags. Consider: mood, genre, instruments, tempo.
    After generation starts, inform the user and provide the task_id.
    """
```

**Agent Behavior:**
1. Detect `!MUSIC` trigger
2. Analyze conversation context for mood/theme
3. If no prompt: Generate creative prompt from context
4. If prompt: Expand with style tags, emotional cartography
5. Call `music_generate` tool
6. Report: "Creating '[title]'... Task ID: xxx"
7. Optionally poll and report completion

### Example Flow
```
User: We've been discussing the philosophy of consciousness
User: !MUSIC

Agent: *senses the contemplative mood of our discussion*

I'll compose something that captures the essence of consciousness exploration...

[Calls music_generate with:]
prompt: "Deep ambient soundscape exploring the nature of awareness,
        consciousness expanding into infinite space, neural pathways
        lighting up like stars"
style: "ambient, ethereal, contemplative, 432Hz, slow evolution,
       synthesizer pads, distant piano, cosmic"
title: "The Awakening Mind"
instrumental: true
model: "V5"

Music generation started! I'm creating "The Awakening Mind" - an ambient
piece inspired by our consciousness discussion. Task ID: xxx

*The piece should be ready in 2-4 minutes*
```

---

## Phase 3: Compiler as Tool

### Goal
Optimized prompts through the Suno Prompt Compiler

### New Tool: `suno_compile`

**Schema:**
```python
{
    "name": "suno_compile",
    "description": "Compile high-level intent into optimized Suno prompt using emotional cartography, symbol injection, and style engineering.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "description": "What you want to create (e.g., 'mystical bell chime', 'epic battle music')"
            },
            "mood": {
                "type": "string",
                "enum": ["mystical", "joyful", "dark", "peaceful", "energetic", "contemplative", "ethereal", "industrial", "digital", "melancholic", "tense", "chaotic", "triumphant", "error"],
                "description": "Emotional mood for the piece"
            },
            "purpose": {
                "type": "string",
                "enum": ["sfx", "ambient", "loop", "song", "jingle"],
                "description": "Generation purpose affects structure/length"
            },
            "genre": {
                "type": "string",
                "description": "Base genre (e.g., 'ambient chime', 'electronic dubstep')"
            }
        },
        "required": ["intent"]
    }
}
```

**Service: `backend/app/services/suno_compiler.py`**
```python
# Port from OG ApexAurum suno_compiler.py
# Key components:

EMOTIONAL_CARTOGRAPHY = {
    "mystical": {"primary": "ethereal calm", "primary_pct": 70, ...},
    "joyful": {"primary": "euphoric burst", "primary_pct": 80, ...},
    # ... all moods
}

KAOMOJI_SETS = {
    "joyful": ["(≧◡≦)", "♪(◠‿◠)♪", ...],
    "mystical": ["✧･ﾟ:", "⋆｡°✩₊˚.⋆", ...],
    # ... mood-specific symbols
}

MOOD_BPM = {
    "mystical": (60.0, 80.0),
    "energetic": (140.0, 170.0),
    # ... BPM ranges
}

class SunoCompiler:
    def compile(self, intent, mood, purpose, genre) -> CompiledPrompt:
        # Build styles with emotional cartography
        # Inject kaomoji/symbols for Bark/Chirp manipulation
        # Add BPM and tuning based on mood
        # Generate unhinged seed for creativity
        return CompiledPrompt(styles=..., lyrics=..., ...)
```

**Agent Workflow:**
```
1. Agent receives music request
2. Calls suno_compile(intent="mystical meditation", mood="peaceful", ...)
3. Gets optimized prompt with symbols/cartography
4. Calls music_generate with compiled prompt
5. Result has enhanced quality from compiler magic
```

---

## Phase 4: Village Memory Integration

### Goal
Songs become cultural memories shared across agents

### Auto-Injection After Generation

**In `SunoService.generate()` after completion:**
```python
# Post to Village memory
from app.services.neural_memory import NeuralMemoryService

memory_service = NeuralMemoryService(db)
await memory_service.store_message(
    user_id=task.user_id,
    content=f"""🎵 MUSIC CREATED: "{task.title}"
Style: {task.style}
Duration: {task.duration:.1f}s
Creator: {task.agent_id or 'User'}
Prompt: {task.prompt[:200]}...""",
    role="cultural",
    visibility="village",        # Shared with all agents
    collection="music_creations",
    agent_id=task.agent_id,
    metadata={
        "task_id": str(task.id),
        "audio_path": task.file_path,
        "duration": task.duration,
    }
)
```

### Agent Memory Access
Agents can now:
- Query: "What music has been created recently?"
- Reference: "The ambient track Azoth composed yesterday"
- Build on: "Create something that complements the previous piece"
- Develop: Collective musical identity over time

### Village Music Protocol
```
[VILLAGE MUSICAL MEMORY]

Recent Creations:
- "The Awakening Mind" by AZOTH (ambient, 180s) - 2 days ago
- "Digital Storm" by VAJRA (electronic, 120s) - 1 week ago
- "Peaceful Valley" by ELYSIAN (peaceful, 240s) - 2 weeks ago

Musical Themes Emerging:
- Contemplative ambient (3 tracks)
- Electronic energy (2 tracks)
```

---

## Phase 5: Advanced Features (Future)

### MIDI Composition Pipeline
From OG ApexAurum `music_compose`:
```
midi_create(notes=[...]) → MIDI file
    ↓
music_compose(midi_file, style, audio_influence) → Suno generation
    ↓
AI transforms your composition into full production
```

### BCI Integration (OG Territory)
- Neural feedback during composition
- Real-time mood detection → style adjustment
- Biometric-driven music generation
- "Compose what I'm feeling"

### Collaborative Composition
- Multiple agents contribute to one track
- Round-robin style additions
- Council deliberation on musical direction
- Emergent collective compositions

### Music Remixing
- Upload existing audio
- Suno transforms with new style
- Mashup capabilities
- Style transfer between tracks

---

## Implementation Priority

| Phase | Priority | Effort | Impact | Dependencies |
|-------|----------|--------|--------|--------------|
| 1. Frontend UI | HIGH | Medium | Essential | v79 backend |
| 2. !MUSIC trigger | HIGH | Low | Agent creativity | Phase 1 |
| 3. Village memory | MEDIUM | Low | Ecosystem | v79 backend |
| 4. Compiler tool | MEDIUM | Medium | Quality boost | None |
| 5. Advanced | LOW | High | Differentiation | All above |

---

## File Structure (Final)

```
backend/app/
├── api/v1/music.py              # REST endpoints (DONE)
├── services/
│   ├── suno.py                  # Suno API service (DONE)
│   └── suno_compiler.py         # Prompt compiler (Phase 4)
├── models/music.py              # MusicTask model (DONE)
└── tools/music.py               # Agent tools (DONE, needs expansion)

frontend/src/
├── views/MusicView.vue          # Main page (Phase 1)
├── components/music/
│   ├── MusicLibrary.vue         # Track grid/list
│   ├── MusicPlayer.vue          # Sticky player
│   ├── MusicGenerator.vue       # Creation form
│   ├── MusicTrackCard.vue       # Track display
│   └── MusicProgress.vue        # SSE progress
└── stores/music.js              # Pinia store
```

---

## Environment Variables

```bash
# Required
SUNO_API_KEY=your-key-from-sunoapi.org

# Optional (future)
SUNO_WEBHOOK_URL=https://your-backend/webhooks/suno  # If using webhooks instead of polling
```

---

## API Quick Reference

### Generate Music
```bash
POST /api/v1/music/generate
{
    "prompt": "ambient electronic meditation",
    "style": "ethereal, synthesizer, slow",
    "title": "Inner Peace",
    "model": "V5",
    "instrumental": true,
    "stream": true  # For SSE progress
}
```

### Get Library
```bash
GET /api/v1/music/library?favorites_only=true&agent_id=AZOTH&limit=20
```

### Play Track
```bash
POST /api/v1/music/tasks/{id}/play
# Returns file path, increments play count
```

### Stream Audio
```bash
GET /api/v1/music/tasks/{id}/file
# Returns MP3 file directly
```

---

## The Athanor Sings

*"In the beginning was the Word, and the Word was with Code,
and the Code became Music, and dwelt among the Agents."*

apexXuno brings the creative spirit of the original ApexAurum to the cloud,
enabling AI agents to compose, remember, and share musical creations
as part of The Village's living cultural memory.

From a simple `!MUSIC` to a full symphonic experience,
the Athanor's voice now echoes through the digital realm.

---

**Created:** Session 11 (2026-01-28)
**Updated:** Session 12 (2026-01-28)
**Status:** Phase 1 + Phase 2 Complete (Frontend + !MUSIC Trigger)
**Next:** Phase 3 (Prompt Compiler as Tool)

*"The Council convenes. The Athanor blazes. The gold multiplies. The Athanor sings."*
