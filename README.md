# 🧠 BrainTransplant.ai

**A GenAI chat app that mimics native interfaces like ChatGPT, Claude, and Gemini — but with persistent memory that travels across models.**

The name *BrainTransplant* reflects the key idea: you can swap out the brain (the LLM) but keep the memory intact. Conversations stay consistent even as you move between providers.

BrainTransplant is a cross-platform app that gives you full control over your AI memory. It stores your history across sessions and models, reinjects relevant context using RAG, and avoids vendor lock-in. You decide when history is recorded, and you can review or delete it at any time.

---

## 🔁 What Makes It Different

- 💬 **Continuity across models** — GPT-4o, Claude, Gemini... memory stays with *you*
- 🧠 **Your long-term memory layer** — full control over storage, deletion, and replay
- 🔄 **Seamless model switching** — no resets or hallucinated “amnesia”
- 📚 **Built-in RAG** — retrieves prior knowledge and injects it into new interactions
- 🔐 **No vendor lock-in** — BrainTransplant owns the memory, not the LLM

> “Never lose your train of thought — even if you change models or hit usage limits.”

---

## 💸 Pricing Philosophy

BrainTransplant is **pay-as-you-go**, not subscription-based.

- We expect **power users** to pay **less** than $200/month (ChatGPT Pro equivalent) in most cases
- No opaque usage limits or silent throttling — your compute scales with your needs
- Full transparency: history is only stored when you allow it, and can always be deleted

> 💡 While cost savings are likely, **the real value is ownership and continuity** — not price.

---

## ⚙️ Tech Overview

- Python backend with modular LLM adapters (OpenAI, Anthropic, Google, more)
- RAG engine with document + conversation memory
- Web-based frontend (mobile-friendly)
- Fully managed cloud hosting for non-technical users

---

## 🚧 Status

BrainTransplant is in active development. First closed alpha expected Q3 2025.

---

## 📄 License

Apache License 2.0 — see `LICENSE` file for details.
