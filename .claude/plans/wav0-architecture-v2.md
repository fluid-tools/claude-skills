# wav0 Architecture Implementation Plan v2

## Goal

Build a production-ready AI music production platform with:

- AI SDK v6 custom agent with Convex persistence
- xmcp MCP server integrated into existing Next.js app
- Durable workflows via Convex Workflows for Replicate jobs
- Sample generation (MusicGen) and stem splitting (Demucs)

## User Decisions (Finalized)

| Decision          | Choice                                       | Rationale                              |
| ----------------- | -------------------------------------------- | -------------------------------------- |
| MCP Server        | xmcp in existing Next.js app                 | File-based routing, Better-Auth native |
| AI Agent          | Custom AI SDK v6 (replace @convex-dev/agent) | v6 features, no compatibility issues   |
| AI Provider       | Vercel AI Gateway                            | Single gateway, model flexibility      |
| Package Structure | Keep `packages/backend`                      | Already working, pragmatic             |
| MCP Auth          | Better-Auth only                             | Single auth system, simpler            |
| Deployment        | Vercel + Upstash Redis                       | User confirmed                         |
| MVP Scope         | Web + MCP (no native app)                    | User confirmed                         |

## Architecture Overview

```
apps/
├── web/                          # Next.js (existing)
│   ├── src/app/
│   │   ├── studio/              # Main interface (NEW)
│   │   ├── ai/                  # AI chat (UPGRADE to v6)
│   │   ├── api/
│   │   │   ├── ai/chat/         # AI SDK v6 streaming endpoint (NEW)
│   │   │   └── webhooks/replicate/ # Replicate callbacks (NEW)
│   │   └── mcp/                 # xmcp route handler (NEW)
│   ├── src/tools/               # xmcp tools directory (NEW)
│   │   ├── generate-sample.ts
│   │   ├── split-stems.ts
│   │   └── check-job-status.ts
│   └── src/lib/
│       └── opfs/                # OPFS caching layer (NEW)
│
packages/
├── backend/                     # Convex (existing, EXPAND)
│   └── convex/
│       ├── schema.ts            # EXPAND with new tables
│       ├── workflows.ts         # NEW: Convex Workflows
│       ├── audio.ts             # NEW: Replicate integration
│       ├── samples.ts           # NEW: Sample CRUD
│       ├── threads.ts           # NEW: Thread management
│       └── messages.ts          # NEW: Message persistence
```

---

## Phases

### Phase 1: Core Infrastructure

- [ ] 1.1 Update Convex schema (samples, jobs, threads, messages)
- [ ] 1.2 Install & configure @convex-dev/workflow
- [ ] 1.3 Create Replicate integration service (audio.ts)
- [ ] 1.4 Define producer workflow (durable job handling)
- [ ] 1.5 Create Replicate webhook handler

### Phase 2: AI Agent (AI SDK v6)

- [ ] 2.1 Remove @convex-dev/agent dependency
- [ ] 2.2 Create custom thread/message management (Convex)
- [ ] 2.3 Build AI SDK v6 chat endpoint with tools
- [ ] 2.4 Define tools: generateSample, splitStems, checkJobStatus
- [ ] 2.5 Update AI chat UI to use new endpoint
- [ ] 2.6 Implement streaming responses

### Phase 3: MCP Server (xmcp)

- [ ] 3.1 Initialize xmcp in apps/web
- [ ] 3.2 Configure xmcp.config.ts
- [ ] 3.3 Create MCP route handler with Better-Auth
- [ ] 3.4 Implement generate_sample tool
- [ ] 3.5 Implement stem_split tool
- [ ] 3.6 Implement check_job_status tool
- [ ] 3.7 Test with Claude Desktop / MCP inspector

### Phase 4: OPFS & UI Polish

- [ ] 4.1 Implement OPFS audio caching layer
- [ ] 4.2 Create sample player component
- [ ] 4.3 Sample library browser
- [ ] 4.4 Basic waveform display
- [ ] 4.5 Playback controls

---

## Convex Schema (Final)

```typescript
// packages/backend/convex/schema.ts
import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // ============ AUDIO ============
  samples: defineTable({
    userId: v.string(),
    name: v.string(),
    storageId: v.id("_storage"),
    duration: v.number(),
    bpm: v.optional(v.number()),
    key: v.optional(v.string()),
    format: v.union(v.literal("wav"), v.literal("mp3")),
    type: v.union(
      v.literal("generated"),
      v.literal("uploaded"),
      v.literal("stem")
    ),
    sourceId: v.optional(v.id("samples")), // Parent sample for stems
    metadata: v.object({
      model: v.optional(v.string()), // musicgen, demucs
      prompt: v.optional(v.string()), // Generation prompt
      stemType: v.optional(v.string()), // drums, bass, vocals, other
      lufs: v.optional(v.number()),
      peakDb: v.optional(v.number()),
    }),
    createdAt: v.number(),
  })
    .index("by_user", ["userId"])
    .index("by_type", ["type"])
    .index("by_source", ["sourceId"]),

  jobs: defineTable({
    userId: v.string(),
    workflowId: v.optional(v.string()),
    type: v.union(v.literal("generate"), v.literal("stem_split")),
    status: v.union(
      v.literal("pending"),
      v.literal("processing"),
      v.literal("completed"),
      v.literal("failed")
    ),
    replicateId: v.optional(v.string()),
    input: v.any(),
    output: v.optional(v.any()),
    error: v.optional(v.string()),
    progress: v.optional(v.number()), // 0-100
    createdAt: v.number(),
    completedAt: v.optional(v.number()),
  })
    .index("by_user_status", ["userId", "status"])
    .index("by_replicate", ["replicateId"])
    .index("by_workflow", ["workflowId"]),

  // ============ CHAT ============
  threads: defineTable({
    userId: v.string(),
    title: v.optional(v.string()),
    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_user", ["userId"]),

  messages: defineTable({
    threadId: v.id("threads"),
    role: v.union(
      v.literal("user"),
      v.literal("assistant"),
      v.literal("system"),
      v.literal("tool")
    ),
    content: v.string(),
    toolCalls: v.optional(
      v.array(
        v.object({
          id: v.string(),
          name: v.string(),
          args: v.any(),
        })
      )
    ),
    toolResults: v.optional(
      v.array(
        v.object({
          toolCallId: v.string(),
          result: v.any(),
        })
      )
    ),
    metadata: v.optional(
      v.object({
        model: v.optional(v.string()),
        tokens: v.optional(v.number()),
        workflowId: v.optional(v.string()),
      })
    ),
    createdAt: v.number(),
  })
    .index("by_thread", ["threadId"])
    .index("by_thread_created", ["threadId", "createdAt"]),
});
```

---

## Key Dependencies to Add

```json
{
  "dependencies": {
    "@convex-dev/workflow": "latest",
    "@vercel/ai-gateway": "latest",
    "ai": "^6.0.0",
    "@ai-sdk/anthropic": "latest",
    "replicate": "latest",
    "xmcp": "latest",
    "@xmcp/adapter": "latest"
  }
}
```

---

## Environment Variables Required

```bash
# Already set (user confirmed)
REPLICATE_API_TOKEN=...
REDIS_URL=...                    # Upstash

# To add
ANTHROPIC_API_KEY=...            # For AI Gateway fallback
VERCEL_AI_GATEWAY_URL=...        # If using gateway
```

---

## Errors Encountered

(None yet - planning phase)

---

## Status

**Currently in Phase 0** - Plan finalized, ready for implementation

---

## Next Steps

1. User to confirm plan looks good
2. Begin Phase 1: Core Infrastructure
3. Work on Phase 2 & 3 in parallel (AI Agent + MCP)
