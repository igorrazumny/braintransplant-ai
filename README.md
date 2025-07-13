# 🧠 BrainTransplant.ai

**A GenAI chat app that mimics native interfaces like ChatGPT, Gemini, and Claude — but with memory that travels across models.**

The name *BrainTransplant* reflects the key idea behind the app: you can swap out the brain of the chat — the LLM that powers it — but keep the memory and context fully intact across every provider while changing seamlessly between them.

BrainTransplant is a cross-platform GenAI chat app that preserves your full LLM conversation history — even when switching between models or vendors. With built-in RAG and multi-provider support, BrainTransplant ensures continuity, context, and control across every interaction.

> 📅 **Pay-per-use, no fixed subscription.** If you're currently using ChatGPT Pro, BrainTransplant delivers a similar level of service with multi-LLM flexibility — and in most cases, **lower monthly costs.**

> 🧠 **The core idea is continuity.** Your currently chosen LLM never forgets (unless you want it to) what you discussed with any other LLM you've previously talked to via BrainTransplant.

That's the foundation of BrainTransplant: consistent context and memory across any model you choose.
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
