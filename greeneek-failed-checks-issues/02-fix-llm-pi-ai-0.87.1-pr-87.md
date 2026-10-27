# fix(llm-pi-ai): adapt catalog, compat table, and transcript replay to @earendil-works/pi-ai 0.87.1 (failing CI #183 on PR #87)

- **Target Repository:** `Mostafa-Taher-git/Greeneek`
- **Labels:** `bug`, `dependencies`, `llm`

---

## Problem

Open Dependabot PR #87 (`chore(deps): bump @earendil-works/pi-ai from 0.84.2 to 0.87.1`, branch `dependabot/npm_and_yarn/earendil-works/pi-ai-0.87.1` @ `e942566`) is currently failing **All checks have failed** in [`CI #183`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128309126) (`ci (22)` → `Run pnpm lint`, exit code `2`).

`@earendil-works/pi-ai` `0.87.1` introduces breaking TypeScript contract changes across provider compatibility flags, thinking capability keys, API identifiers, JSON argument types, and transcript replay structures that `packages/llm/llm-pi-ai` exhaustively type-checks.

### Exact compiler / type-aware lint diagnostics from `CI #183`

1. **`packages/llm/llm-pi-ai/src/catalog.ts:159`** — new `"thinking.budget"` capability key required:
   ```text
   Property '"thinking.budget"' is missing in type '{ 'thinking.enabled': true; 'thinking.effort': true; }'
   but required in type 'Record<"thinking.enabled" | "thinking.effort" | "thinking.budget", true>'.
   ```
2. **`packages/llm/llm-pi-ai/src/catalog.ts:263`** — removed `deferredToolsMode` in `OpenAICompletionsCompat`:
   ```text
   Object literal may only specify known properties, and 'deferredToolsMode' does not exist in type
   'Record<keyof OpenAICompletionsCompat, CompatDisposition>'.
   ```
3. **`packages/llm/llm-pi-ai/src/catalog.ts:277`** — updated key set on `OpenAIResponsesCompat`:
   ```text
   Type '{ ... }' does not satisfy the expected type 'Record<keyof OpenAIResponsesCompat, CompatDisposition>'.
   ```
4. **`packages/llm/llm-pi-ai/src/catalog.ts:289`** — removed `supportsToolReferences` in `AnthropicMessagesCompat`:
   ```text
   Object literal may only specify known properties, and 'supportsToolReferences' does not exist in type
   'Record<keyof AnthropicMessagesCompat, CompatDisposition>'.
   ```
5. **`packages/llm/llm-pi-ai/src/catalog.ts:315`** — new `"mistral-conversations"` entry required in `ApiWithCompat`:
   ```text
   Property '"mistral-conversations"' is missing in type '{ 'openai-completions': ...; 'bedrock-converse-stream': ... }'
   but required in type 'Readonly<Record<ApiWithCompat, Readonly<Record<string, CompatDisposition>>>>'.
   ```
6. **`packages/llm/llm-pi-ai/src/replay.ts:155`** — stricter `JsonObject` tool-call argument typing:
   ```text
   Type 'Record<string, unknown>' is not assignable to type 'JsonObject'.
   ```
7. **`packages/llm/llm-pi-ai/src/replay.ts:184`** — updated assistant content block union (`TextContent | ThinkingContent | ToolCall`):
   ```text
   Type '(... )[]' is not assignable to type '(TextContent | ThinkingContent | ToolCall)[]'.
   ```
8. **`packages/llm/llm-pi-ai/tests/catalog.spec.ts:514–515`** — updated `TranscriptContext` shape in tests:
   ```text
   Argument of type '{ messages: { role: "user"; content: string; timestamp: number; }[]; }'
   is not assignable to parameter of type 'TranscriptContext'.
   ```

## Affected Failed Checks (1 active open-PR run)

| Failed Check Run | Trigger | Ref / PR / Tag | Commit | Failing Job & Step | Diagnostic / Title | Status |
|---|---|---|---|---|---|---|
| [CI #183](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128309126) | `pull_request` | PR #87 (open) | `e942566` | `ci (22)` → `Run pnpm lint` | Argument of type '{ messages: { role: "user"; content: string; timestamp: number; }[]; }' is not assignable to | 🔴 Active |

## Work

- [ ] Decide whether to adapt `packages/llm/llm-pi-ai` incrementally for `@earendil-works/pi-ai@0.87.1` on PR #87 now, **or** close PR #87 in favor of the parked `#70` wave in #86 (`llm route split plus pi-ai 1.3.0`) and add an `ignore` rule in `.github/dependabot.yml` until `#70` lands.
- [ ] If adapting to `0.87.1` now:
  - [ ] Update `packages/llm/llm-pi-ai/src/catalog.ts` (`thinking.budget`, `OpenAICompletionsCompat`, `OpenAIResponsesCompat`, `AnthropicMessagesCompat`, and `"mistral-conversations"` disposition).
  - [ ] Narrow tool-call arguments to `JsonObject` and align content block types in `packages/llm/llm-pi-ai/src/replay.ts`.
  - [ ] Update `TranscriptContext` fixtures in `packages/llm/llm-pi-ai/tests/catalog.spec.ts` while preserving 100% coverage.

## Acceptance criteria

- [ ] Either PR #87 passes `pnpm lint`, `pnpm typecheck`, and `pnpm test -- --coverage`, or PR #87 is intentionally superseded with a `.github/dependabot.yml` `ignore` pin referencing #86 (`#70`) so no red PR remains open.

## References

- PR #87 (`chore(deps): bump @earendil-works/pi-ai from 0.84.2 to 0.87.1`)
- Failed check run: [`CI #183`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128309126) / job [`120974377441`](https://github.com/Mostafa-Taher-git/Greeneek/actions/runs/40128309126/job/120974377441)
- Roadmap tracking: #86 (`#70 — llm route split plus pi-ai 1.3.0`)
