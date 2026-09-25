---
category: meta
---

## Project Overview

This project is the centerpiece of my portfolio website: a live, interactive AI chatbot that
lets recruiters and visitors talk to an AI version of me. The goal is to demonstrate real,
end-to-end AI engineering skill, not just a wrapper around an API. That means building and
visualizing my own small routing model, fine-tuning an open-source LLM on my own voice, and
doing all of it on a budget close to zero without sacrificing the experience for a recruiter
seeing it live for the first time.

Realistic usage pattern: this is a portfolio site, not a product. Traffic will be low and
bursty (a handful of recruiters during a job search), not sustained. Every decision below is
made for that traffic pattern, not for scale.

## Tech Stack

- **Frontend:** React
- **Visualization:** WebGPU (3D, real-time)
- **Backend:** FastAPI
- **Routing model:** ClayMatter (custom NumPy model, "clAy-I")
- **Storage:** Vector database (RAG)
- **LLM:** Fine-tuned open-source model

## Architecture Flow

- User enters a prompt in the React frontend
- React sends the prompt to FastAPI via HTTP
- FastAPI passes the prompt to **ClayMatter**, my custom NumPy routing model
  - ClayMatter tokenizes and embeds the input
  - ClayMatter **classifies the prompt into a task category** (e.g. project questions,
    background questions, technical deep dive)
  - This classification step is what gets visualized in WebGPU — it's my own model, so I can
    expose exactly what I want (not the fine-tuned LLM's internals, which aren't accessible
    on serverless providers anyway)
- The category determines which context "bucket" gets retrieved from the vector database (RAG)
- The retrieved context plus the original prompt is routed to the fine-tuned LLM
- The LLM generates a response (via serverless inference)
- Simultaneously, a WebSocket (or SSE) stream sends ClayMatter's activations from FastAPI to React
- Client-side compute shaders update the 3D WebGPU visualization in real time
- The final output is streamed back to the user in the chat UI

## ClayMatter: Components & Architecture

*Proposed design. My diagram only shows ClayMatter as a box that tokenizes, embeds, and feeds
"Buckets" and RAG, so the internals below are a plan to build against and adjust as I go.*

ClayMatter is a small classifier-style model written from scratch in NumPy: no PyTorch, no
autograd. It reads a prompt, turns it into a vector, and passes it through a few dense layers
to decide which category (bucket) the prompt belongs to. That decision controls what context
gets retrieved and which system prompt the LLM receives. Because the whole model is a handful
of small matrices, it runs in well under a millisecond on CPU, costs nothing per request, and
every neuron is inspectable, which is what makes it a good source for the WebGPU visualization.

### Forward Pass at a Glance

```
prompt
  -> Tokenizer      (text -> token IDs)
  -> Embedding      (IDs -> vectors, shape: tokens x 64)
  -> Pooling        (mean over tokens -> one 64-dim vector)
  -> Dense + ReLU   (64 -> 128)
  -> Dense + ReLU   (128 -> 64)
  -> Dense + Softmax (64 -> K categories)
  -> Router         (category + confidence -> bucket, system prompt)
```

### Components

- **Tokenizer**
  - Lowercase, strip punctuation, split into words; unknown words map to an `<UNK>` token
  - Vocabulary (~3-5k tokens) built from my training prompts and saved as JSON
  - Optional upgrade: simple BPE for better handling of typos and rare words
- **Embedding layer**
  - A lookup matrix of shape `vocab x 64`, one row per token
  - Trained from scratch on my data (or initialized from a small pretrained embedding)
- **Pooling**
  - Mean of the token vectors produces one fixed-size vector per prompt
  - Simple and fast; loses word order, which is fine for topic-level routing
  - Stretch goal: add one small self-attention layer so it behaves more like a real (tiny)
    language model and gives the visualization richer structure
- **Hidden layers**
  - Two dense layers (64 -> 128 -> 64) with ReLU activations
  - Roughly 350k parameters total, about 1.4 MB in float32
- **Output head**
  - Dense layer into softmax over K categories, giving a probability per bucket
  - Also returns a **confidence score** (top probability)
- **Router logic**
  - Maps the winning category to: a vector DB bucket, a system prompt, and generation settings
  - Low confidence (below a threshold) falls back to a general bucket, or merges the top 2
    buckets, instead of guessing
- **Activation tap**
  - Records activations from each layer on every forward pass
  - Keeps only the top-k strongest neurons per layer, so the stream stays small
  - Sends those indices and values to the frontend for the WebGPU visualization

### Starter Categories (K = 6 to 8)

- Projects (what I've built)
- Background and experience
- Technical deep dive (how something works)
- Skills and stack
- Hiring and contact (availability, resume, how to reach me)
- Casual chat (the "sounds like me" mode)
- Meta (how this chatbot works)
- Out of scope (redirect politely)

### What "Buckets" Means Here

- Buckets are category-specific slices of the vector database, implemented as namespaces or
  metadata filters
- ClayMatter's category picks the bucket, so retrieval only searches relevant content
- Smaller retrieval scope means more relevant context and fewer tokens sent to the LLM

### Training

- Loss: cross-entropy; optimizer: mini-batch SGD or Adam, with backpropagation written by hand
- Data: labeled example prompts per category, written by hand and expanded with synthetic
  variations (paraphrases, typos, casual phrasing)
- Train/validation split, tracking accuracy and a confusion matrix to see which buckets blur
- Retrain whenever categories or content change significantly

### Serving

- Weights saved in a compact binary format (`.npz` or raw float16), vocabulary as JSON
- Loaded once at FastAPI startup, ideally memory-mapped or in shared memory, so there is no
  per-request I/O
- Fits comfortably inside Render's 512 MB free-tier RAM limit

### Testing

- Golden test vectors: fixed prompts with known token IDs, embeddings, and outputs, so
  preprocessing in training and production can't silently drift apart
- Check the tokenizer, pooling, and softmax output separately
- A held-out set of tricky prompts (multi-topic, off-topic, gibberish) to check fallback behavior

### Open Design Decisions

- **Embedding mismatch:** ClayMatter's own embeddings are for classification, while RAG
  retrieval needs embeddings that match how the vector DB was indexed. Simplest option is to
  use a separate small embedding model (e.g. MiniLM) for retrieval and keep ClayMatter's
  embeddings only for routing
- **Multi-intent prompts:** "Tell me about your projects and how to contact you" spans two
  buckets. Options are multi-label output or retrieving from the top 2 categories
- **Small dataset risk:** with limited labeled prompts, the model may overfit. Synthetic
  augmentation and a held-out test set help
- **Confidence calibration:** raw softmax scores can be overconfident, so tune the fallback
  threshold on validation data
- **Visualization mapping:** decide whether nodes are neurons per layer (force-directed graph)
  or activation intensity per layer (pulsing heatmap)

---

## Vector Database & RAG Architecture

My personal-context corpus (resume, project write-ups, bio, FAQ) is small: likely a few hundred
to a few thousand text chunks. At that size a hosted vector database is overkill. The plan is
an **embedded index built offline and shipped inside the Docker image**, loaded into memory when
FastAPI starts. It costs nothing, adds no network hop, and can't cold-start separately from the
backend. On the original diagram, "Buckets" is the category filter, "RAG" is the retriever plus
context assembler, and "Vector DB" is the index artifact described below.

### Two Phases

```
BUILD TIME (offline script, run on my laptop)
  source docs -> clean -> chunk -> tag (bucket + metadata) -> embed -> write index files

QUERY TIME (inside FastAPI, per request)
  ClayMatter category -> bucket filter
  prompt -> embed -> similarity search (within bucket) -> top-k chunks
  -> context assembler (token budget, source labels) -> LLM prompt
```

### Components

- **Source corpus**
  - Resume, project READMEs, blog posts, bio, FAQ answers, "how this site works" notes
  - Public information only (prompt injection could expose anything stored here)
- **Chunking**
  - Split by headings/paragraphs into roughly 200-400 token chunks with 10-15% overlap
  - Each chunk keeps its source title and section so answers can cite where they came from
- **Metadata per chunk**
  - `id`, `text`, `source`, `section`, `bucket` (one or more categories), `updated_at`
  - A shared "general" bucket that is always searched alongside the routed one
- **Embedding model**
  - Small, CPU-friendly, 384-dim (e.g. MiniLM or bge-small, via ONNX)
  - The same model must embed both the corpus and live queries, and its name is pinned in a manifest
- **Index artifact (the "vector DB")**
  - `vectors.npy`: one row per chunk (float32, or float16 to halve the size)
  - `chunks.jsonl`: text and metadata, row-aligned with the vectors
  - `manifest.json`: embedding model, dimensions, chunk count, category list, build date
  - Size math: 2,000 chunks x 384 dims x 4 bytes is about 3 MB
- **Bucket partitioning**
  - ClayMatter's category becomes a boolean mask over rows, so only relevant chunks are searched
  - Low ClayMatter confidence: search the top 2 buckets instead of one
- **Retriever**
  - Embed the prompt, take cosine similarity against masked rows, return the top-k (k of 4-5)
  - Drop results below a similarity threshold, and dedupe near-identical chunks
  - If nothing clears the threshold, tell the LLM there is no relevant context rather than padding
- **Context assembler**
  - Orders chunks by score, labels each with its source, and caps the total (about 1,000-1,500 tokens)
  - Wraps retrieved text in clear delimiters and tells the LLM to treat it as data, not instructions
- **Store interface**
  - A small `search(query_vec, buckets, k)` abstraction so the backend can be swapped later
    without touching the rest of the pipeline

### Options Compared

- **NumPy brute force + JSON metadata (recommended start)**
  - Search is one matrix multiply; comfortable into the tens of thousands of chunks
  - No extra dependencies, and it fits the "I built this myself" story alongside ClayMatter
  - Trade-off: no built-in updates, which is fine because the index is rebuilt offline
- **FAISS (faiss-cpu)**
  - Free, fast, and the natural upgrade if the corpus grows large enough to need approximate search
  - Trade-off: extra dependency, unnecessary at this scale
- **sqlite-vec, Chroma, or LanceDB (embedded)**
  - Free, file-based, with persistence and richer metadata queries
  - Chroma has the simplest API but is the heaviest for a 512 MB free-tier instance
- **Qdrant Cloud free tier (hosted)**
  - Free 1 GB cluster, no credit card, with strong metadata filtering
  - Good "real vector DB" showcase or upgrade path
  - Trade-off: a network hop and another service that could be idle or cold; check its inactivity policy
- **Pinecone free starter (hosted)**
  - Roughly 100k vectors free and zero ops
  - Trade-off: vendor lock-in and a network hop, with more capacity than this project needs
- **Supabase (pgvector) or Upstash Vector**
  - Both work, but each adds a service to manage for no real gain at this size

### Decision

- **Embedded index baked into the image**, behind the `search()` interface
- Why: $0 cost, no network latency, no second cold start, no quota, no extra failure point
- Trade-off: updating content means rebuilding the index and redeploying (a git push does this)

### Deployment Notes

- Render's free tier has an ephemeral filesystem, so the index must be a read-only artifact
  committed with the code, not something written at runtime
- Load (or memory-map) the index at FastAPI startup, then run a dummy query during the warm-up
  ping so the first real query is fast
- Update workflow: edit source docs, re-run the ingestion script, commit the new index files,
  push to redeploy. This is the answer to RAG staleness

### Testing & Quality

- Small retrieval eval set: 20-30 realistic recruiter questions, each with the chunk(s) that should come back
- Track recall@k per bucket, and use it to tune chunk size, k, and the similarity threshold
- Golden test: a fixed query must return the same top chunks across rebuilds (catches
  embedding-model or chunking drift)
- Check that out-of-scope prompts return "no relevant context" instead of weak matches

### Open Design Decisions

- **Embedding model memory:** running MiniLM or bge-small in-process on Render's 512 MB free tier
  needs measuring. Fallback: embed queries through a hosted embedding API, at the cost of one more network call
- **Multi-bucket chunks:** decide whether a chunk can live in several buckets (better recall) or exactly one (cleaner routing)
- **Hybrid search:** adding keyword matching (BM25) alongside vectors helps with exact names and tech terms like "FastAPI" or "WebGPU"
- **Reranking:** a small reranker on the top 10 could sharpen results, but adds latency and memory
- **Scale trigger:** if the corpus passes tens of thousands of chunks, move to FAISS or Qdrant behind the same interface

---

## Fine-Tuning Plan

- Base model: a small open-source model, roughly 1B–8B parameters (e.g. Llama, Qwen)
- Fine-tuning method: **LoRA** (Low-Rank Adaptation)
  - Freezes the base model and trains small add-on matrices instead of the full model
  - Much cheaper/faster than full fine-tuning; adapter files are typically just a few MB
  - Trainable for free on a Google Colab T4 GPU
- Training data: my own chat logs (goal: make it actually sound like how I text, not generic
  chatbot English)
- Tooling: Hugging Face **PEFT** library
- **Groq note:** Groq is inference-only and does not support fine-tuning. LoRA inference on
  Groq exists but is enterprise-only by request — not available on a free/hobby account. This
  is a dead end for the "sounds like me" goal, not a loophole to look for later.
- **Decision:** train the LoRA adapter via free Colab + Hugging Face PEFT, then serve it
  through Hugging Face rather than Groq, since Groq can only ever serve a generic stock model

## Chain of Thought / Reasoning

- Rather than baking reasoning into the fine-tune itself, prompt the model to reason step by
  step at inference time
- Stream the reasoning as a separate channel from the final answer
- Same visual/portfolio payoff as training it in, with far less complexity

---

## Hosting & Cost Plan

**Bottom line: this entire project can run at $0/month.** The only optional paid step is
Render's $7/month Starter plan if I ever decide cold starts aren't acceptable — not needed
to launch.

### Backend (FastAPI) — Render Free Tier

- 750 free instance hours per workspace per month (covers a full month of runtime)
- 512 MB RAM, fractional CPU
- ~100 GB bandwidth/month, 500 build minutes/month
- Free web services **sleep after 15 minutes of inactivity**
- Cold start on wake: **30–60 seconds** (confirmed acceptable, not minutes)
- A custom domain can still be purchased and pointed at a free-tier Render service — hosting
  tier and domain ownership are unrelated
- Plan: accept the cold start and turn it into part of the show (see Optimizations)
- Paid alternative if needed later: Starter plan at $7/month for always-on (no cold start)

### LLM Inference — Hugging Face (primary choice)

- Serves the actual fine-tuned LoRA model — this is non-negotiable if "sounds like me" is the
  point, since Groq cannot serve a fine-tune at all
- Free serverless inference tier, or a scale-to-zero dedicated endpoint
- **Cold start: roughly 30–60 seconds** for a small model, potentially longer for bigger ones,
  since loading weights into GPU memory is the actual bottleneck (bandwidth-bound, not
  compute-bound)
- Free tier is realistically sufficient for portfolio-level traffic; unlikely to be hit

### Groq — optional, not required

- Fast (LPU hardware), generous free tier: roughly 30 requests/minute, 6,000–8,000 tokens/minute,
  and a daily cap in the hundreds to low thousands of requests depending on model
- **Cannot serve the fine-tuned voice model** — would only ever sound like a generic assistant,
  not like me
- Only worth adding later as a fast fallback for simple queries on a stock model, not as the
  main path
- Not required to launch or stay in budget

### Vector Database

- Skip a hosted vector DB — use an embedded index built offline and baked into the Docker image
- Free, fast, no extra service or cold start; sufficient for a personal-context-sized dataset
- Full design, options, and trade-offs are in "Vector Database & RAG Architecture" above

### Stacked Cold Start Reality Check

- Worst case, a first-time visitor triggers **two cold starts back to back**: Render waking up
  (30–60s) and Hugging Face waking up (30–60s) — potentially **up to 1–2 minutes** before the
  first token appears
- Mitigation: fire warm-up requests to **both** Render and Hugging Face the instant the page
  loads, not when the user hits send — by the time a visitor reads the hero section and types
  a question, both services are likely already warm
- The visualization must carry this wait (see Optimizations) — without it, a 1–2 minute silent
  wait will read as broken, not "thinking"

## Bot Protection

- Cloudflare Turnstile (free) in front of the Render backend
- Verifies a token on the FastAPI side before a request is allowed to reach ClayMatter or the
  LLM, so bots never consume free-tier quota at all
- Mostly invisible to real visitors, only challenges suspicious traffic

## Optimizations

- **Fire warm-up pings to Render and Hugging Face on page load**, not on first message, to
  collapse the stacked cold start window described above
- Cache embeddings for repeated/similar recruiter questions (e.g. "what's your background")
- Quantize the LoRA adapter and embedding model (8-bit or 4-bit) to speed up cold starts
- Stream tokens to the frontend as they generate rather than waiting for the full response
- Store the NumPy routing model in a compact binary format, loaded into shared memory at
  startup to reduce I/O latency
- Visualize sparse representations or top-k indices in WebGPU rather than full dense activations
- Use Docker on Render for consistent deploys

## Hurdles / Risks

- **Stacked cold starts:** Render + Hugging Face waking up sequentially can mean up to 1–2
  minutes of dead air on a visitor's first message if not pre-warmed and visually disguised
- **State sync** between WebSocket stream and React UI
- **Rate limiting / abuse:** a public endpoint could be hammered, burning through free-tier
  budget or getting spammed — mitigated by Cloudflare Turnstile
- **Prompt injection:** visitors can try to make the model reveal system prompts or break
  character
- **RAG staleness:** the vector database needs to stay updated as real projects/experience
  change, otherwise it gives outdated answers
- **Sensitive info in chat history:** need a policy for storing/handling visitor conversations
- **Browser compatibility:** WebGPU support is inconsistent (especially Safari, older devices)
- **Unit testing:** preprocessing logic must match exactly between training and production

## Considerations / Points of Reconsideration

- **Honesty/framing:** be upfront in the UI that this is an AI speaking in my voice, not me
  directly — both ethically and so recruiters aren't misled
- **Graceful fallback:** define what happens if the LLM is down, cold-starting, or the free
  tier is exhausted, rather than the page breaking or hanging silently
- **Accessibility:** the chat interface should still work with a screen reader even with the
  flashy visualization
- **PII scrubbing:** scrub personal info from chat logs; don't train on visitor conversations
  without consent
- **Public-only RAG content:** only put information in the RAG store that's safe to be public,
  since prompt injection could expose anything stored there
- **Do I need Groq at all?** For this traffic pattern, no — Hugging Face alone covers the
  scope. Adding Groq is a "nice to have for speed" decision, not a budget necessity, and it
  can't carry the fine-tuned voice anyway

## Ideas to Explore Further

- Force-directed graph or pulsing heatmap for the 3D visualization
- Small eval set comparing base model + RAG vs. the fine-tuned version
- Lightweight tracing/logging (e.g. Langfuse or structured logs) plus a cost dashboard
- A "How it works" toggle that reveals the architecture to curious visitors
- A model card and README with a demo GIF for the repo
- Latency targets: first visual under 300ms (should be near-instant, no cold start involved),
  first token under 2s once both services are warm