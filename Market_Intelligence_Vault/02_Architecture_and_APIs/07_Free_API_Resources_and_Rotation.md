# Free High-Speed API Resources & Key Rotation Guide

This document maps out the fastest, zero-cost AI API providers, their exact limits, and production-grade key rotation architectures to ensure your Market Intelligence Engine runs continuously without hitting rate limit walls.

---

## 1. Ultra-Fast Free Inference Providers (LPU & Custom Silicon)

These providers run open-weight models on specialized hardware (Groq LPUs, Cerebras Wafer-Scale, SambaNova Reconfigurable Dataflow), delivering inference speeds up to 2,000 tokens/second.

| Provider | Top Free Models | Free Tier Rate Limits | Real-world Speed | Best Used For |
| :--- | :--- | :--- | :--- | :--- |
| **[Groq Console](https://console.groq.com)** | `llama-3.3-70b-versatile`<br>`llama-3.1-8b-instant`<br>`deepseek-r1-distill-llama-70b`<br>`mixtral-8x7b-32768` | • **14,400 req/day** (8B)<br>• **1,000–3,000 req/day** (70B)<br>• 30 RPM / 6,000 TPM | ~300–800 t/s | Near-instant classification, JSON extraction, and high-frequency Reddit comment filtering. |
| **[Cerebras](https://cloud.cerebras.ai)** | `llama3.3-70b`<br>`llama3.1-8b` | • **1,000,000 tokens/day**<br>• 30 RPM / 60,000 TPM | **~1,800–2,100 t/s** | High-volume batch processing; summarizing 50 forum posts in under 2 seconds. |
| **[SambaNova Cloud](https://cloud.sambanova.ai)** | `Meta-Llama-3.3-70B-Instruct`<br>`Qwen2.5-72B-Instruct`<br>`DeepSeek-R1` | • Generous daily free quota<br>• 20–30 RPM | ~200–450 t/s | Multi-lingual analysis, coding, and DeepSeek-R1 reasoning models. |

---

## 2. Massive Context & Heavy Reasoning Free Tiers

| Provider | Top Free Models | Free Limits | Context Window | Best Used For |
| :--- | :--- | :--- | :--- | :--- |
| **[Google AI Studio](https://aistudio.google.com)** | `gemini-2.0-flash`<br>`gemini-1.5-flash`<br>`gemini-1.5-pro` | • **1,500 req/day** (Flash)<br>• 15–60 RPM<br>• 1,000,000 TPM | **1,000,000 to 2,000,000 tokens** | Ingesting entire subreddits, 100+ PDF industry reports, or competitor landing pages in a single call. |
| **[GitHub Models](https://github.com/marketplace/models)** | `gpt-4o`<br>`gpt-4o-mini`<br>`claude-3.5-sonnet` (preview)<br>`phi-4`, `llama-3.3-70b` | • **50–150 req/day** (High-end)<br>• **1,000 req/day** (Mini) | 128k tokens | Complex synthesis, business plan structuring, and high-IQ market gap verification. |
| **[Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/)** | `@cf/meta/llama-3.1-8b-instruct`<br>`@cf/baai/bge-large-en-v1.5` (Embeddings) | • **10,000 Neurons/day** (5,000+ calls/day) | Varies | Serverless micro-tasks, background embeddings, and vector similarity search. |
| **[OpenRouter Free Tier](https://openrouter.ai/models?max_price=0)** | Models ending with `:free` (e.g., `meta-llama/llama-3.3-70b-instruct:free`) | • 20–50 req/day per free endpoint | 32k–128k tokens | Automatic fallback routing when primary providers fail. |

---

## 3. Key Rotation & Pooling Architecture

When running automated agents, a single API key will eventually trigger a `429 Too Many Requests` error during heavy scraping runs. Implementing a **Round-Robin Key Pool** resolves this completely.

### The `.env` Key Pool Structure
Store multiple keys (from multiple free accounts or projects) as comma-separated lists:

```env
# D:\Start\.env

# Google AI Studio (Create 2-3 free project keys)
GEMINI_KEY_POOL=AIzaSy_key1_xxx,AIzaSy_key2_yyy,AIzaSy_key3_zzz

# Groq Console (Free keys)
GROQ_KEY_POOL=gsk_key1_xxx,gsk_key2_yyy,gsk_key3_zzz

# Cerebras Cloud
CEREBRAS_KEY_POOL=csk_key1_xxx,csk_key2_yyy

# GitHub Personal Access Tokens (Fine-grained for Models)
GITHUB_TOKEN_POOL=ghp_token1_xxx,ghp_token2_yyy
```

### Key Rotation Logic (Zero-Downtime Fallback)
```javascript
class KeyRotator {
  constructor(envKeyString) {
    this.keys = (envKeyString || '').split(',').map(k => k.trim()).filter(Boolean);
    this.index = 0;
  }

  getKey() {
    if (!this.keys.length) throw new Error("No keys available in pool.");
    const key = this.keys[this.index];
    this.index = (this.index + 1) % this.keys.length;
    return key;
  }

  async runWithRetry(apiCallFn) {
    let attempts = 0;
    while (attempts < this.keys.length) {
      const activeKey = this.getKey();
      try {
        return await apiCallFn(activeKey);
      } catch (error) {
        if (error?.status === 429 || error?.response?.status === 429) {
          console.warn(`[KeyPool] Rate limit (429) on key ...${activeKey.slice(-4)}. Rotating to next key.`);
          attempts++;
        } else {
          throw error;
        }
      }
    }
    throw new Error("All keys in pool exhausted. Wait for reset window.");
  }
}
```

---

## 4. Key Rotation Best Practices & Guidelines

1. **Separate Projects, Same Account:** In Google Cloud / Google AI Studio, you can create multiple Google Cloud Projects under one email. Each project has its own independent 1,500 daily quota.
2. **Model Fallback Chaining:** If `gemini-2.0-flash` reaches quota, fall back automatically to `llama-3.3-70b` on Groq, then `llama-3.3-70b` on Cerebras.
3. **Exponential Backoff:** If all keys in a specific pool are rate-limited, wait 15–30 seconds before retrying rather than hammering the endpoints.
