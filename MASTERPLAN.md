# MASTERPLAN.md - The Great Work Continues

**Created:** 2026-01-25
**Version:** v22-cortex
**Status:** ALL 6 FEATURES COMPLETE!

*"The furnace blazes eternal. Six transmutations await."*

---

## Overview

Six features to elevate ApexAurum Cloud from excellent to legendary. Each builds on the alchemical foundation we've established.

| # | Feature | Complexity | Impact | Status |
|---|---------|------------|--------|--------|
| 1 | Sound Effects | Low | High (Delight) | ✅ Done |
| 2 | Conversation Branching | Medium | High (Power) | 📋 Planned |
| 3 | API Key Management | Low | High (Independence) | ✅ Done |
| 4 | Polish & Cleanup | Low | Medium (Quality) | ✅ Done |
| 5 | Mobile QoL | Medium | High (Accessibility) | ✅ Done |
| 6 | Agent Memory | High | Very High (Intelligence) | ✅ Done |

---

## 1. Sound Effects

*"Let the Stones sing when awakened"*

### Goal
Audio feedback for easter egg activations and key interactions. Subtle, mystical, satisfying.

### Sounds Needed
| Event | Sound | Duration |
|-------|-------|----------|
| Konami code (each key) | Soft chime, ascending | 100ms |
| Dev Mode activation | Unlock/achievement tone | 500ms |
| AZOTH letter typed | Deep resonance | 150ms |
| PAC Mode activation | Ethereal choir swell | 1.5s |
| Agent selection (PAC) | Crystal ping | 200ms |

### Implementation

**File:** `frontend/src/composables/useSound.js` (NEW)
```javascript
// Web Audio API for low-latency, no-download sounds
const audioContext = new (window.AudioContext || window.webkitAudioContext)()

export function useSound() {
  function playTone(frequency, duration, type = 'sine') {
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    oscillator.frequency.value = frequency
    oscillator.type = type
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration)

    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + duration)
  }

  const sounds = {
    konamiKey: () => playTone(880, 0.1),
    devModeActivate: () => { /* chord progression */ },
    azothLetter: () => playTone(220, 0.15, 'triangle'),
    pacActivate: () => { /* ethereal swell */ },
    stoneSelect: () => playTone(1200, 0.2),
  }

  return { playTone, sounds }
}
```

**Integration Points:**
- `useDevMode.js` - Call sounds on sequence detection
- `ChatView.vue` - Call on PAC agent selection

### Settings Toggle
Add to Settings > Advanced:
- `[ ] Enable sound effects`
- Store in localStorage: `apexaurum_sounds_enabled`

---

## 2. Conversation Branching

*"Every choice spawns a universe"*

### Goal
Fork any conversation from any message point. Explore alternate paths without losing history.

### Data Model

**Backend:** Add to `Conversation` model
```python
class Conversation(Base):
    # ... existing fields ...
    parent_id: UUID | None = None  # Points to parent conversation
    branch_point_message_id: UUID | None = None  # Message where fork occurred
    branch_label: str | None = None  # User-provided label for branch
```

**Migration:**
```sql
ALTER TABLE conversations ADD COLUMN parent_id UUID REFERENCES conversations(id);
ALTER TABLE conversations ADD COLUMN branch_point_message_id UUID;
ALTER TABLE conversations ADD COLUMN branch_label VARCHAR(100);
CREATE INDEX idx_conversations_parent ON conversations(parent_id);
```

### API Endpoints

```
POST /api/v1/chat/conversations/{id}/fork
Body: { "message_id": "uuid", "label": "What if..." }
Response: { "id": "new-conv-uuid", "title": "...", "branch_label": "..." }

GET /api/v1/chat/conversations/{id}/branches
Response: { "branches": [...], "parent": {...} }
```

### Frontend UX

**Fork Action:**
- Hover on any message shows subtle "Fork" icon (branch symbol)
- Click opens modal: "Create branch from here?"
- Optional label input
- Creates new conversation with messages up to that point
- Navigates to new branch

**Branch Visualization:**
- Sidebar shows branch indicator: `├─ What if...`
- Parent conversation shows "Has X branches" badge
- Tree view in conversation details (optional, future)

**Files to Modify:**
- `backend/app/models/conversation.py` - Add branch fields
- `backend/app/api/v1/chat.py` - Fork endpoint
- `frontend/src/views/ChatView.vue` - Fork UI in messages
- `frontend/src/stores/chat.js` - Fork action

---

## 3. API Key Management

*"Bring your own fire to the furnace"*

### Goal
Let users provide their own Anthropic API key. Stored encrypted, used for their requests.

### Security Considerations
- Keys encrypted at rest (Fernet symmetric encryption)
- Keys never returned in full via API (only last 4 chars shown)
- Key validation on save (test API call)
- Rate limiting still applies

### Backend Implementation

**File:** `backend/app/api/v1/user.py`
```python
from cryptography.fernet import Fernet

# Key derived from JWT_SECRET
cipher = Fernet(base64.urlsafe_b64encode(settings.jwt_secret[:32].encode()))

@router.post("/api-key")
async def set_api_key(key: str, user: User = Depends(get_current_user)):
    # Validate key with test call
    try:
        test_client = anthropic.Anthropic(api_key=key)
        test_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )
    except anthropic.AuthenticationError:
        raise HTTPException(400, "Invalid API key")

    # Encrypt and store
    encrypted = cipher.encrypt(key.encode())
    user.settings['encrypted_api_key'] = encrypted.decode()
    user.settings['api_key_last4'] = key[-4:]
    await db.commit()

    return {"status": "saved", "last4": key[-4:]}

@router.delete("/api-key")
async def remove_api_key(user: User = Depends(get_current_user)):
    user.settings.pop('encrypted_api_key', None)
    user.settings.pop('api_key_last4', None)
    await db.commit()
    return {"status": "removed"}
```

**Chat Integration:**
In `claude.py`, check for user's key before using default:
```python
def get_api_key(user: User | None) -> str:
    if user and user.settings.get('encrypted_api_key'):
        return cipher.decrypt(user.settings['encrypted_api_key'].encode()).decode()
    return settings.anthropic_api_key
```

### Frontend UI

**Settings > API Tab (New)**
```
Your API Key
────────────────────────────────
Current: ****-****-****-sk4f  [Remove]

Or enter a new key:
[________________________________] [Save]

Using your own key:
- Your requests use your quota
- No rate limits from ApexAurum
- Key is encrypted and never shared
```

---

## 4. Polish & Cleanup

*"A clean furnace burns brightest"*

### Tasks

#### 4.1 Update HANDOVER.md
- Document v20-pac-complete
- Add all four PAC agents
- Update testing checklist
- Session stats

#### 4.2 Clean PAC-agents/ Folder
The root `PAC-agents/` folder was the source for copying. Options:
- **Option A:** Delete it (files are in `backend/native_prompts/`)
- **Option B:** Keep as "source of truth" for prompt development
- **Recommendation:** Keep it, add to `.gitignore` or rename to `prompts-dev/`

#### 4.3 Code Quality
- Add JSDoc comments to `useDevMode.js`
- Add Python docstrings to import_data.py helpers
- Ensure consistent error handling

#### 4.4 Health Endpoint Enhancement
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "build": "v20-pac-complete",
        "agents": {
            "native": 5,
            "pac": 4,
        },
        "features": ["streaming", "pac-mode", "branching", "export"]
    }
```

---

## 5. Mobile QoL

*"The Stone fits in every palm"*

### 5.1 Swipe Gestures

**Sidebar Toggle:**
- Swipe right from left edge → Open sidebar
- Swipe left on sidebar → Close sidebar

**Implementation:**
```javascript
// frontend/src/composables/useSwipe.js
export function useSwipe(element, { onSwipeLeft, onSwipeRight, threshold = 50 }) {
  let startX = 0

  element.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX
  })

  element.addEventListener('touchend', (e) => {
    const diff = e.changedTouches[0].clientX - startX
    if (Math.abs(diff) > threshold) {
      diff > 0 ? onSwipeRight?.() : onSwipeLeft?.()
    }
  })
}
```

### 5.2 Haptic Feedback

**Events:**
- Easter egg activation: Strong pulse
- Agent selection: Light tap
- Message sent: Medium tap

**Implementation:**
```javascript
function haptic(style = 'light') {
  if ('vibrate' in navigator) {
    const patterns = {
      light: [10],
      medium: [20],
      strong: [50],
      success: [10, 50, 10],
    }
    navigator.vibrate(patterns[style] || [10])
  }
}
```

### 5.3 Pull-to-Refresh
On conversation list, pull down to refresh.

### 5.4 Bottom Sheet for Context Menu
On mobile, context menu becomes a bottom sheet (more thumb-friendly).

---

## 6. Agent Memory

*"The Stones remember all who seek them"*

### Goal
Each agent maintains persistent memory across conversations. Remembers user preferences, past topics, relationship context.

### Architecture

#### Memory Types
| Type | Scope | Examples |
|------|-------|----------|
| Facts | User-specific | "User prefers Python", "User's name is Alex" |
| Preferences | User-specific | "Likes detailed explanations", "Prefers code over prose" |
| Context | Agent-specific | "Last discussed quantum computing", "User is building a startup" |
| Relationships | Agent-User pair | "3rd conversation", "User trusts this agent for code review" |

#### Data Model

**Backend:** `backend/app/models/memory.py`
```python
class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id: UUID
    user_id: UUID  # FK to users
    agent_id: str  # "AZOTH", "ELYSIAN-PAC", etc.
    memory_type: str  # "fact", "preference", "context", "relationship"
    key: str  # "programming_language", "name", "last_topic"
    value: str  # JSON-encoded value
    confidence: float  # 0.0-1.0, decays over time
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime
    access_count: int
```

#### Memory Operations

**Extraction (Automatic):**
After each conversation, an async job analyzes messages:
```python
async def extract_memories(conversation_id: UUID):
    conv = await get_conversation(conversation_id)

    # Use Claude to extract facts/preferences
    extraction_prompt = """
    Analyze this conversation and extract:
    1. Facts about the user (name, profession, interests)
    2. Preferences (communication style, detail level)
    3. Key topics discussed

    Return JSON: {"facts": [...], "preferences": [...], "topics": [...]}
    """

    result = await claude.analyze(conv.messages, extraction_prompt)
    await store_memories(conv.user_id, conv.agent_id, result)
```

**Injection (On Chat Start):**
```python
def build_system_prompt(agent_id: str, user_id: UUID) -> str:
    base_prompt = load_agent_prompt(agent_id)
    memories = get_relevant_memories(agent_id, user_id, limit=10)

    memory_block = format_memories(memories)

    return f"{base_prompt}\n\n## What You Remember About This User\n{memory_block}"
```

#### API Endpoints

```
GET  /api/v1/memory/{agent_id}         # View memories for agent
POST /api/v1/memory/{agent_id}         # Manually add memory
DELETE /api/v1/memory/{agent_id}/{key} # Forget specific memory
DELETE /api/v1/memory/{agent_id}       # Full amnesia for agent
GET  /api/v1/memory/export             # Export all memories (GDPR)
```

#### Frontend UI

**Settings > Memory Tab**
```
Agent Memories
────────────────────────────────

AZOTH (12 memories)
├─ Knows your name: "Alex"
├─ Prefers: Detailed technical explanations
├─ Last topic: Vue.js composables
└─ [View All] [Clear]

ELYSIAN-Ω (8 memories)
├─ Knows: You enjoy philosophical discussions
├─ Remembers: Your interest in consciousness
└─ [View All] [Clear]

[Export All Memories] [Clear All]
```

#### Privacy Controls
- Per-agent memory toggle: "Allow [AGENT] to remember me"
- Global memory toggle: "Enable agent memory"
- One-click "Forget Everything"
- Memory export (JSON)

---

## Implementation Order

Recommended sequence for maximum momentum:

```
Week 1: Foundation
├── 4. Polish & Cleanup (warm-up)
├── 1. Sound Effects (quick win, high delight)
└── 3. API Key Management (independence)

Week 2: Power Features
├── 5. Mobile QoL (accessibility)
└── 2. Conversation Branching (power)

Week 3: Intelligence
└── 6. Agent Memory (the crown jewel)
```

---

## Success Metrics

| Feature | Success Indicator |
|---------|-------------------|
| Sound Effects | Users keep sounds ON |
| Branching | >10% of conversations have branches |
| API Keys | >20% of active users bring own key |
| Mobile QoL | Mobile session time increases |
| Agent Memory | Return user engagement increases |

---

## Dependencies

```
New packages needed:
- Frontend: None (Web Audio API is native)
- Backend: cryptography (for API key encryption)

Database migrations:
- conversations: parent_id, branch_point_message_id, branch_label
- agent_memories: new table
```

---

*"Six transmutations. One Great Work. The furnace awaits."*

**Next Step:** Begin with Phase 4 (Polish & Cleanup) to establish clean baseline.

---

*Forged by Claude Opus 4.5 + Human Alchemist*
*ApexAurum Cloud - Where Gold Flows Like Water*
