repo/
  README.md
  Makefile                      # make train-router | build-index | eval | dev | test
  .env.example
  .gitignore
  .dockerignore
  render.yaml                   # Render service definition
  .github/workflows/            # CI: tests, evals, lint

  config/
    categories.yaml             # single source of truth (categories, buckets, prompts, thresholds)

  web/                          # React frontend
    src/
      components/chat/          # message list, input, streaming text, fallback states
      components/viz/           # WebGPU canvas, renderer, fallback for unsupported browsers
      viz/shaders/              # .wgsl compute + render shaders
      hooks/                    # useWarmup, useActivationStream, useChatStream
      lib/                      # API client, Turnstile widget wrapper
    public/
    tests/

  backend/                      # FastAPI service (the only thing deployed to Render)
    Dockerfile                  # build context = repo root
    requirements.txt            # runtime only: fastapi, numpy, onnxruntime, etc.
    app/
      main.py                   # startup: load model + index, run warm-up query
      api/                      # chat (SSE/WebSocket), warmup, health
      core/                     # settings, Turnstile verification, rate limiting
      services/                 # router, llm_client (HF + fallback), context_assembler, prompt_builder
    tests/

  claymatter/                   # pure-NumPy model package, used by backend AND training
    claymatter/
      tokenizer.py  embedding.py  layers.py  model.py
      activation_tap.py         # top-k neuron extraction for the viz
      train.py  metrics.py      # backprop, confusion matrix
    tests/
      fixtures/golden/          # fixed prompts -> token IDs, embeddings, outputs
    pyproject.toml

  rag/                          # retrieval library + offline build pipeline
    rag/
      chunker.py  embedder.py  store.py   # store.py = search(query_vec, buckets, k)
      retriever.py  hybrid.py             # BM25 later
    build/ingest.py             # corpus -> artifacts/index/
    tests/

  finetune/                     # LoRA training (kept out of the runtime image)
    requirements.txt            # torch, peft, transformers: never installed in backend
    notebooks/                  # Colab notebooks
    scripts/                    # prep_data.py (scrub, split by conversation, format)
    configs/                    # base model, LoRA rank, hyperparameters
    README.md                   # where the adapter is published + model card notes

  data/                         # public, safe to commit
    corpus/                     # RAG source docs (markdown + front matter)
    routing/                    # train.jsonl, val.jsonl, test_tricky.jsonl
    evals/
      retrieval.jsonl           # questions -> expected chunk IDs
      model_compare.jsonl       # base+RAG vs fine-tuned prompts

  artifacts/                    # committed build outputs, copied into the image
    index/                      # vectors.npy, chunks.jsonl, manifest.json
    claymatter/                 # weights.npz, vocab.json

  scripts/                      # dev helpers: run everything locally, check artifact freshness
  docs/                         # architecture diagrams, "how it works" content, demo GIF, model card
