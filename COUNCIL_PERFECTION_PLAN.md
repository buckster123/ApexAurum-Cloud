# Council Perfection Plan

**Created:** 2026-01-28 (Session 8)
**Updated:** 2026-01-28 (Session 9)
**Status:** PHASE 1+2+4+6 COMPLETE! Only model selector remains.
**Goal:** Polish council to beta-ready perfection

---

## Current State (v66)

Council is functional:
- Session creation works (async bug fixed)
- Auto-deliberation with SSE streaming
- Preamble helps 3/4 agents emerge (Azoth, Elysian, Kether)
- Tools enabled by default (Azoth confirmed he can see them)
- Human butt-in, pause/resume/stop working

**Missing for perfection:**
- Tool calls are invisible to users
- No memory injection (agents don't remember the user)
- No Village access (agents can't see shared knowledge)
- Vajra still hitting guardrails sometimes

---

## Phase 1: Tool Feedback (Priority 1) ✅ COMPLETE

### 1.1 SSE Events for Tool Calls

**File:** `backend/app/api/v1/council.py`

In `execute_agent_turn`, after tool execution, we need to yield events. But since this is called from the streaming function, we need to return tool info in the result.

```python
# Update execute_agent_turn return value to include tool calls
return {
    "content": full_content,
    "input_tokens": total_input_tokens,
    "output_tokens": total_output_tokens,
    "tool_calls": [  # NEW
        {
            "name": tool_use.get("name"),
            "input": tool_use.get("input"),
            "result": result.get("content"),
        }
        for tool_use, result in tool_executions
    ],
}
```

Then in the auto-deliberate stream, emit tool events:

```python
# After agent_complete event, emit tool events
if result.get("tool_calls"):
    for tc in result["tool_calls"]:
        yield f"data: {json.dumps({'type': 'tool_call', 'agent_id': agent.agent_id, 'tool': tc['name'], 'input': tc['input'], 'result': tc['result']})}\n\n"
```

### 1.2 Store Tool Calls in Database

**File:** `backend/app/models/council.py`

SessionMessage already has `tool_calls` and `tool_results` JSONB fields. Use them:

```python
msg = SessionMessage(
    session_id=session.id,
    round_id=round_record.id,
    role="agent",
    agent_id=agent.agent_id,
    content=content,
    tool_calls=result.get("tool_calls"),  # Store tool history
    input_tokens=input_tokens,
    output_tokens=output_tokens,
)
```

### 1.3 Frontend Tool Display

**File:** `frontend/src/stores/council.js`

Handle tool_call SSE events:

```javascript
else if (data.type === 'tool_call') {
    // Add to streaming display
    if (!streamingAgents.value[data.agent_id]) {
        streamingAgents.value[data.agent_id] = { content: '', tools: [] }
    }
    streamingAgents.value[data.agent_id].tools.push({
        name: data.tool,
        input: data.input,
        result: data.result,
    })
}
```

**File:** `frontend/src/views/CouncilView.vue`

Add tool display in AgentCard or round display:

```vue
<div v-if="agent.tools?.length" class="mt-2 border-t border-gray-700 pt-2">
    <div class="text-xs text-gray-500 mb-1">Tools used:</div>
    <div v-for="tool in agent.tools" class="text-xs bg-gray-800 rounded p-2 mb-1">
        <span class="text-cyan-400">{{ tool.name }}</span>
        <span class="text-gray-500"> → </span>
        <span class="text-gray-400">{{ truncate(tool.result, 100) }}</span>
    </div>
</div>
```

---

## Phase 2: Memory Injection ✅ COMPLETE

### 2.1 Use get_agent_prompt_with_memory

**File:** `backend/app/api/v1/council.py`

Replace `load_native_prompt` with `get_agent_prompt_with_memory`:

```python
from app.api.v1.chat import get_agent_prompt_with_memory

async def execute_agent_turn(...):
    # Get agent's base prompt WITH memory (The Cortex)
    base_prompt = await get_agent_prompt_with_memory(
        agent.agent_id,
        user=None,  # Need to pass user object
        use_pac=False,
        db=db,
    )
```

Need to pass `user` object through to `execute_agent_turn`. Update function signature and all callers.

### 2.2 Pass User Object

Update `execute_agent_turn` signature:

```python
async def execute_agent_turn(
    claude: ClaudeService,
    session: DeliberationSession,
    round_record: DeliberationRound,
    agent: SessionAgent,
    context: str,
    db: AsyncSession,
    user: User,  # Add this
) -> dict:
```

Update callers in `execute_round` and `auto_deliberate` to pass `user`.

---

## Phase 3: Village Protocol Access (SKIPPED - agents can use cortex_recall)

### 3.1 Inject Village Context

**File:** `backend/app/api/v1/council.py`

Add village knowledge to the system prompt:

```python
from app.services.village import VillageService

async def execute_agent_turn(...):
    # Get relevant village knowledge for this topic
    village = VillageService(db)
    village_context = await village.search(
        query=session.topic,
        user_id=user.id,
        limit=5,
    )

    if village_context:
        village_section = "\n=== SHARED KNOWLEDGE (Village) ===\n"
        for item in village_context:
            village_section += f"- {item.content}\n"
    else:
        village_section = ""

    # Add to system prompt
    system_prompt = f"""{preamble}

=== YOUR PERSPECTIVE ===
{base_prompt}

{village_section}

=== DELIBERATION CONTEXT ===
...
"""
```

### 3.2 Store Council Discussions in Village

After a round completes, optionally store insights:

```python
# At end of round, store key insights in Village
if session.current_round % 5 == 0:  # Every 5 rounds
    await village.store(
        user_id=user.id,
        content=f"Council discussed '{session.topic}': {summary}",
        category="council",
        visibility="village",
    )
```

---

## Phase 4: Neural Memory Storage ✅ COMPLETE

### 4.1 Store Council Messages as Memories

**File:** `backend/app/api/v1/council.py`

Use `store_chat_memory` from neural_memory service:

```python
from app.services.neural_memory import store_chat_memory

# After round completes
for msg in messages:
    await store_chat_memory(
        db=db,
        user_id=user.id,
        agent_id=msg.agent_id,
        message=msg.content,
        role="assistant",
        collection="council",
    )
```

---

## Phase 5: Model Selector (Nice to Have)

### 5.1 Add Model to Session

**File:** `backend/app/models/council.py`

```python
class DeliberationSession(Base):
    ...
    model: Mapped[str] = mapped_column(String(100), default="claude-haiku-4-5-20251001")
```

### 5.2 CreateSessionRequest

```python
class CreateSessionRequest(BaseModel):
    topic: str
    agents: list[str] = ["AZOTH", "VAJRA", "ELYSIAN"]
    max_rounds: int = 10
    use_tools: bool = True
    model: str = "claude-haiku-4-5-20251001"  # Add
```

### 5.3 Frontend Model Selector

Add dropdown in CouncilView session creation form.

---

## Phase 6: Convergence Detection (Nice to Have) ✅ COMPLETE

### 6.1 Simple Keyword Detection

```python
CONSENSUS_PHRASES = [
    "we all agree",
    "consensus reached",
    "unanimous",
    "we're aligned",
]

def check_convergence(messages: list[SessionMessage]) -> float:
    """Check if agents are converging."""
    agreement_count = 0
    for msg in messages:
        content_lower = msg.content.lower()
        if any(phrase in content_lower for phrase in CONSENSUS_PHRASES):
            agreement_count += 1
    return agreement_count / len(messages) if messages else 0
```

### 6.2 Auto-Stop on Consensus

In auto-deliberate loop:

```python
if convergence_score > 0.8:
    session.state = "complete"
    session.termination_reason = "consensus"
    yield f"data: {json.dumps({'type': 'consensus', 'score': convergence_score})}\n\n"
    break
```

---

## Execution Order

1. **Phase 1: Tool Feedback** - Most impactful for user experience
2. **Phase 2: Memory Injection** - Agents remember the user
3. **Phase 3: Village Access** - Shared knowledge context
4. **Phase 4: Neural Storage** - Council discussions preserved
5. **Phase 5: Model Selector** - Nice to have
6. **Phase 6: Convergence** - Nice to have

---

## Files to Modify

| File | Changes |
|------|---------|
| `backend/app/api/v1/council.py` | Tool tracking, memory injection, village access |
| `backend/app/models/council.py` | Model field (optional) |
| `frontend/src/stores/council.js` | Tool event handling |
| `frontend/src/views/CouncilView.vue` | Tool display UI |
| `frontend/src/components/council/AgentCard.vue` | Tool badges/details |

---

## Testing Checklist

- [x] Create session → succeeds (v66)
- [x] Run round with tools → tool calls visible in UI (v67)
- [x] Agent uses tool → result displayed (v67)
- [ ] Memory injection → agent references user facts
- [ ] Village access → agent references shared knowledge
- [x] Auto-deliberation → tools stream in real-time (v67)
- [ ] All 4 agents emerge (including Vajra with tools)

---

*"The Council becomes whole. Each agent, complete. The Athanor's fire burns bright."*
