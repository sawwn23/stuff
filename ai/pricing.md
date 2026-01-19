# LLM Provider Pricing Comparison

| Provider                      | Model                        | Input ($/1M tokens) | Output ($/1M tokens) | Notes                                                                                                           |
| ----------------------------- | ---------------------------- | ------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------- |
| **OpenAI (direct API)**       | GPT-5.2 Pro (flagship)       | $1.75               | $14.00               | Multimodal support; cached input discounts (up to 90%); Batch API ~50% off. Strong in general/multimodal tasks. |
|                               | GPT-5 (standard flagship)    | $1.25               | $10.00               |                                                                                                                 |
| **Anthropic (Claude direct)** | Claude Sonnet 4.5 (mid-tier) | $3.00               | $15.00               | Excels in reasoning/coding; prompt caching (up to 90% savings); Batch API 50% off; 200K-1M context.             |
|                               | Claude Opus 4.5 (flagship)   | $15.00              | $75.00               |                                                                                                                 |
| **Google (Gemini API)**       | Gemini 2.5 Flash (fast)      | $0.30               | $2.50                | Free tier available; strong multimodality (audio/video); 1M+ context. Official: ai.google.dev/pricing           |
|                               | Gemini 2.5 Pro (flagship)    | $1.25–$2.50         | $5–$10               | Tiered pricing by context length; grounding with Search free (limits apply).                                    |
| **AWS Bedrock**               | Claude Sonnet 4.5            | $3.00               | $15.00               | Matches Anthropic direct pricing; enterprise features (VPC, unified billing).                                   |
|                               | Claude Opus 4.5              | $15.00              | $75.00               | Also hosts Gemini, Llama, etc.; Batch 50% off on select models.                                                 |

Prompt Caching Overview and Pricing
Prompt caching reuses repeated context (e.g., system prompts, documents, conversation history) across API calls, reducing input costs and latency significantly. All providers support it, but mechanics and pricing differ.

OpenAI:
How it works: Automatic (no code changes needed). Applies to prompts >1,024 tokens. Caches exact prefix matches (place static content first). Cache lasts ~5–60 minutes of inactivity (cleared after 1 hour max). Reduces latency up to 80%.
Pricing: Cached input tokens charged at reduced rate (often ~90% discount, e.g., GPT-5.2: $0.175 vs $1.75 input; GPT-5 mini: $0.025 vs $0.25). No extra fees.
Best for: Multi-turn chats, agents with tools/codebases.

Anthropic (Claude direct):
How it works: Explicit—mark blocks with cache_control (ephemeral). Default TTL 5 minutes (refreshes on use); optional 1-hour TTL (beta header). Min tokens per cache point (e.g., 1,024+). Up to 90% savings on reads.
Pricing: Cache write (first time): +25% premium over base input (e.g., Sonnet ~$3.75/M). Cache read (reuse): 90% discount (~$0.30/M for Sonnet). No effect on output.
Best for: Long documents, repeated queries.

Google (Gemini):
How it works: Mix of implicit (automatic for Gemini 2.5 models; default on, min 1K–2K tokens, place static first) and explicit (manual creation, custom TTL). Implicit: up to 90% discount on hits. Explicit: separate storage charge.
Pricing: Implicit: automatic discount on hits (75–90%). Explicit: Reduced access rate (e.g., $0.025–$0.40/M) + hourly storage ($1–$4.50/M tokens/hour).
Best for: Multimodal/long-context reuse; free grounding.

AWS Bedrock (Claude models):
How it works: Supports Anthropic Claude caching (explicit checkpoints). Simplified management; cache lasts ~5 minutes (account-isolated). Latency up to 85% lower.
Pricing: Matches/similar to Anthropic—cache read heavily discounted (e.g., ~$0.0006 per 1K tokens read); write slight premium. Batch adds 50% off.
Note: Also supports caching on Amazon Nova models (preview/GA varying).
