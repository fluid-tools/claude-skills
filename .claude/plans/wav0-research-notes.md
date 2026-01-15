# wav0 Research Notes

## Sources & Findings

### AI SDK v6

- **URL**: https://ai-sdk.dev/docs/introduction
- **Status**: Stable (officially released, not beta)
- **Key Features**:
  - Tools Registry with pre-built tools (Exa, Firecrawl, etc.)
  - `streamText()` with tool calling
  - `generateText()` for non-streaming
  - Model Context Protocol (MCP) native support
  - Vercel AI Gateway integration
- **Breaking Change**: @convex-dev/agent has 53 build errors with v6 (Issue #202)

### @convex-dev/agent Compatibility

- **GitHub Issue**: https://github.com/get-convex/agent/issues/202
- **Status**: NOT compatible with AI SDK v6
- **Decision**: Replace with custom implementation

### Convex Workflows (@convex-dev/workflow)

- **Install**: `npm install @convex-dev/workflow`
- **Config**: Add to `convex.config.ts` via `app.use(workflow)`
- **Features**:
  - Step-based execution (survives crashes)
  - Retry configuration (exponential backoff)
  - `step.runAction()`, `step.runMutation()`, `step.runQuery()`
  - Parallel execution with `Promise.all()`
  - Event waiting with `ctx.awaitEvent()`
- **Limits**: 1MiB per step, 8MiB journal size

### xmcp (basementstudio)

- **URL**: https://xmcp.dev/docs
- **GitHub**: https://github.com/basementstudio/xmcp
- **Features**:
  - File-based tool routing (`src/tools/` → auto-registered)
  - Better-Auth native plugin
  - Middleware patterns (API key, JWT, custom)
  - Next.js adapter
- **Setup**:
  ```bash
  npx init-xmcp@latest  # In existing project
  ```
- **Config Required**: `xmcp.config.ts`, tsconfig paths for `.xmcp`

### @vercel/mcp-adapter (Alternative)

- **URL**: https://www.npmjs.com/package/@vercel/mcp-adapter
- **Features**:
  - Official Vercel support
  - Redis URL for SSE transport
  - Simpler but manual tool registration
- **Decision**: Using xmcp instead (file-based routing preferred)

### Replicate JavaScript SDK

- **URL**: https://github.com/replicate/replicate-javascript
- **Webhook Support**: Yes
  ```javascript
  await replicate.predictions.create({
    version: "...",
    input: {...},
    webhook: "https://my.app/webhooks/replicate",
    webhook_events_filter: ["completed"],
  });
  ```
- **Models**:
  - MusicGen: `meta/musicgen:melody-large`
  - Demucs: `cjwbw/demucs:htdemucs_ft`

### Upstash Redis

- **Compatibility**: Works with @vercel/mcp-adapter via `redisUrl`

- **Setup**: Grab connection string from Upstash console

- **Use Case**: SSE transport for Claude Desktop compatibility

---

## Current Codebase State

### Existing Structure

```
apps/web/          # Next.js 16, React 19
packages/backend/  # Convex with Better-Auth, @convex-dev/agent
packages/config/   # Shared config
packages/env/      # Environment validation
```

### Current Dependencies (packages/backend)

- `ai`: ^5.0.117 (need upgrade to v6)
- `@convex-dev/agent`: catalog (need to remove)
- `@convex-dev/better-auth`: catalog (keep)
- `convex`: catalog (keep)

### Current Schema

- Empty: `defineSchema({})`

### Current Auth

- Better-Auth with email/password

- Integrated with Convex via `@convex-dev/better-auth`

---

## Implementation Patterns

### AI SDK v6 Chat Endpoint Pattern

```typescript
// apps/web/src/app/api/ai/chat/route.ts
import { streamText, tool } from "ai";
import { gateway } from "ai";
import { z } from "zod";
import { ConvexHttpClient } from "convex/browser";

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

export async function POST(req: Request) {
  const { messages, threadId, userId } = await req.json();

  const result = streamText({
    model: gateway("anthropic/claude-sonnet-4-5"),
    system: `You are an expert music producer...`,
    messages,
    tools: {
      generateSample: tool({
        description: "Generate audio sample from text",
        parameters: z.object({
          prompt: z.string(),
          duration: z.number().min(1).max(30).default(8),
        }),
        execute: async ({ prompt, duration }) => {
          const workflowId = await convex.mutation(
            api.workflows.startGeneration,
            {
              userId,
              threadId,
              prompt,
              duration,
            }
          );
          return { status: "processing", workflowId };
        },
      }),
      // ... more tools
    },
    maxSteps: 5,
  });

  return result.toDataStreamResponse();
}
```

---

### xmcp Tool Pattern

```typescript
// apps/web/src/tools/generate-sample.ts
import { type ToolMetadata } from "xmcp";
import { z } from "zod";

export const metadata: ToolMetadata = {
  name: "generate_sample",
  description: "Generate audio sample from text description",
};

export const schema = {
  prompt: z.string(),
  duration: z.number().min(1).max(30).default(8),
};

export default async function generateSample(args: z.infer<typeof schema>) {
  // Implementation
  return {
    content: [{ type: "text", text: "..." }],
  };
}
```

### Convex Workflow Pattern

```typescript
// packages/backend/convex/workflows.ts
import { WorkflowManager } from "@convex-dev/workflow";
import { components, internal } from "./_generated/api";

export const workflow = new WorkflowManager(components.workflow, {
  workpoolOptions: {
    maxParallelism: 10,
    retryActionsByDefault: true,
    defaultRetryBehavior: {
      maxAttempts: 3,
      initialBackoffMs: 1000,
      base: 2,
    },
  },
});

export const generateSampleWorkflow = workflow.define({
  args: { userId: v.string(), prompt: v.string(), duration: v.number() },
  handler: async (step, args) => {
    // Step 1: Start Replicate job
    const jobId = await step.runAction(internal.audio.startGeneration, args);

    // Step 2: Wait for completion (with retries)
    const result = await step.runAction(
      internal.audio.waitForCompletion,
      { jobId },
      { retry: { maxAttempts: 20, initialBackoffMs: 5000 } }
    );

    // Step 3: Store sample
    await step.runMutation(internal.samples.create, {
      userId: args.userId,
      ...result,
    });

    return { success: true, sampleId: result.sampleId };
  },
});
```
