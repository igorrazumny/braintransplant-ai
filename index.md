# 🧠 BrainTransplant

**Portable LLM chat with memory that never forgets.**

BrainTransplant is a cross-platform chat app that preserves your full LLM conversation history — even when switching between models or providers. With built-in RAG and multi-provider support, BrainTransplant ensures continuity, context, and control across every interaction.

> 📅 **Pay-per-use, no fixed subscription.** If you stop using it, you stop paying. While it's theoretically possible to exceed the cost of a fixed ChatGPT Pro plan, most power users will likely see cost savings — explained in the pricing section below.

But cost savings aren't the main point.

> 🧠 **The core idea is continuity.** Your currently chosen LLM never forgets (unless you want it to) what you discussed with any other LLM you previously talked to via BrainTransplant.

That's the essence of the name: you can transplant the brain of your chat — the LLM itself — but keep your memory and personality consistent across all models.

---

## 🚀 What It Does
- ✅ Stores and manages your full chat history across sessions and models
- 🔄 Lets you switch between GPT-4o, Claude, Gemini (and more) while preserving context
- 📚 Uses RAG (Retrieval-Augmented Generation) to reinject relevant memory automatically
- 🧩 Built to support multiple providers and pluggable model adapters
- 🔐 You own your data — long-term memory, logs, and context are not locked into any vendor

---

## 💡 Why BrainTransplant?
Most LLM chat platforms (e.g., ChatGPT, Claude, Gemini) silo your history. When you hit usage limits or switch models, context is lost, and you’re forced to start from scratch. BrainTransplant eliminates that problem:

> 💬 "Never lose your train of thought — even if you change models or hit a usage cap."

BrainTransplant acts as your personal AI continuity layer.

---

## 💸 Pricing Notes
BrainTransplant is built to give **average power users** a better, more predictable experience than traditional LLM subscriptions — **without throttling, resets, or provider lock-in.**

### Estimated User Cost
- Most **average power users** will pay **$50–100/month**, all-inclusive
- Includes access to high-end LLMs, persistent memory, and model switching
- ✨ This estimate assumes you're currently using GPT-4o via a **$200/month ChatGPT Pro subscription**, and is based on the author's own experience after switching to BrainTransplant-style usage via API
- ⚠️ Actual usage patterns and costs may vary. These projections are based on early testing and are intended only as a general guideline.

> 💡 **All pricing estimates are based on API rates and infrastructure costs as of summer 2025**

### About the Savings
- Savings are based on continued use of GPT-4o via BrainTransplant vs. $200/month ChatGPT Pro
- **ChatGPT Pro usage limits are not transparent**, and power users may be throttled
- With BrainTransplant, there’s **no throttling**, and performance scales with your needs

### What Happens to History When Switching Models?
- In the ChatGPT UI, switching models preserves the chat thread visually — but the new model **loses awareness of previous turns**
- BrainTransplant reinjects memory across model switches — **you retain continuity and context**

---

## 🔧 Tech Stack (WIP)
- Python backend with support for OpenAI, Anthropic, and Google APIs
- RAG layer with document and chat memory indexing
- Pluggable model architecture with per-provider adapters
- UI: web-based frontend (mobile friendly)
- Hosting: cloud-based, fully managed for non-technical users

---

## 📅 Status
BrainTransplant is currently under development. First closed alpha expected Q3 2025.

---

## 📜 License
Apache License 2.0 — see `LICENSE` file for details.

