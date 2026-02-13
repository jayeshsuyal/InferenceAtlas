# Data Sources

This document explains the provenance of platform pricing and GPU throughput data.

---

## Platform Pricing Data

### Last Verified
**February 2025** (manual spot-check against provider websites)

---

### Fireworks AI
**Type**: Serverless autoscaling
**Billing**: Pay-per-active-hour

| GPU           | Hourly Rate | Source                                    |
|---------------|-------------|-------------------------------------------|
| A100 80GB     | $2.90       | fireworks.ai/pricing (Feb 2025)           |
| H100 80GB     | $4.00       | fireworks.ai/pricing (Feb 2025)           |
| H200 141GB    | $6.00       | fireworks.ai/pricing (Feb 2025)           |
| B200 180GB    | $9.00       | Estimated (not publicly listed, Feb 2025) |

**Notes**:
- Autoscaling: Pay only for active hours
- Sub-minute billing granularity
- H200/B200 rates are **estimates** based on vendor conversations (not confirmed public pricing)

---

### Replicate
**Type**: Dedicated per-second billing
**Billing**: Pay-per-second (minimum 1 second)

| GPU           | Hourly Rate | Source                       |
|---------------|-------------|------------------------------|
| A100 80GB     | $10.08      | replicate.com/pricing (Feb 2025) |

**Notes**:
- Per-second billing: `$0.0028/second × 3600 = $10.08/hour`
- Cold start overhead: ~10–30 seconds (not included in model)

---

### Modal
**Type**: Dedicated hourly billing
**Billing**: Full-hour billing

| GPU           | Hourly Rate | Source                    |
|---------------|-------------|---------------------------|
| A100 40GB     | $3.67       | modal.com/pricing (Feb 2025) |

**Notes**:
- Rounds up to nearest hour (sub-hour usage billed as full hour)
- Includes CPU/memory bundle (not itemized separately)

---

### RunPod
**Type**: Dedicated hourly billing
**Billing**: Hourly on-demand

| GPU           | Hourly Rate | Source                       |
|---------------|-------------|------------------------------|
| A100 80GB     | $1.89       | runpod.io/pricing (Feb 2025) |

**Notes**:
- Community cloud pricing (variable by region)
- Spot pricing available (not modeled, ~50% discount with preemption risk)

---

### Vast.ai
**Type**: Marketplace (peer-to-peer GPU rental)
**Billing**: Hourly variable (bid-based)

| GPU           | Hourly Rate | Source                                   |
|---------------|-------------|------------------------------------------|
| A100 80GB     | $1.75       | vast.ai marketplace average (Feb 2025)   |

**Notes**:
- **Marketplace pricing**: Actual rates vary by availability (±$0.50/hour)
- $1.75 is **7-day average** spot price
- Reliability varies (community hosts, not enterprise SLA)

---

### Together AI
**Type**: Per-token serverless
**Billing**: Pay per million tokens

| Model         | Price per 1M Tokens | Source                          |
|---------------|---------------------|---------------------------------|
| Llama 70B     | $0.88               | together.ai/pricing (Feb 2025)  |

**Notes**:
- Combined input + output pricing (blended rate)
- No GPU provisioning (managed by provider)
- No idle waste

---

## GPU Throughput Data

### Methodology

Throughput values are sourced from:
1. **Vendor-published benchmarks** (Fireworks AI, Together AI, vLLM)
2. **Community benchmarks** (Hugging Face, Anyscale)
3. **Conservative estimation** (when no public data exists)

---

### Model-Specific Throughput

#### Llama 3.1 8B

| GPU           | Tokens/Second | Source                                      |
|---------------|---------------|---------------------------------------------|
| A100 80GB     | 20,000        | vLLM benchmark (continuous batching, FP16)  |
| H100 80GB     | 35,000        | Fireworks AI blog post (Feb 2025)           |
| H200 141GB    | 42,000        | Extrapolated (+20% from H100, memory BW)    |
| B200 180GB    | 60,000        | Estimated (+70% from H100, Blackwell arch)  |

---

#### Llama 3.1 70B

| GPU           | Tokens/Second | Source                                      |
|---------------|---------------|---------------------------------------------|
| A100 80GB     | 8,000         | vLLM benchmark (continuous batching, FP16)  |
| H100 80GB     | 15,000        | Fireworks AI blog post (Feb 2025)           |
| H200 141GB    | 18,000        | Together AI reported (HBM3e memory gains)   |
| B200 180GB    | 25,000        | Estimated (+67% from H100, Blackwell arch)  |

---

#### Llama 3.1 405B

| GPU           | Tokens/Second | Source                                      |
|---------------|---------------|---------------------------------------------|
| A100 80GB     | 1,500         | Requires tensor parallelism (2×A100 min)    |
| H100 80GB     | 2,800         | Together AI blog (4×H100 tensor parallel)   |
| H200 141GB    | 3,500         | Meta reported (H200 cluster, Feb 2025)      |
| B200 180GB    | 5,000         | NVIDIA Blackwell whitepaper estimate        |

**Note**: 405B cannot fit on single GPU. Throughput assumes tensor parallelism across multiple GPUs. Memory check still enforces 400GB minimum.

---

#### Mixtral 8x7B (Mixture of Experts)

| GPU           | Tokens/Second | Source                                      |
|---------------|---------------|---------------------------------------------|
| A100 80GB     | 7,000         | HuggingFace vLLM benchmark (FP16)           |
| H100 80GB     | 13,000        | Together AI reported                        |
| H200 141GB    | 16,000        | Extrapolated (+23% from H100)               |
| B200 180GB    | 22,000        | Estimated (+69% from H100)                  |

---

#### Mistral 7B

| GPU           | Tokens/Second | Source                                      |
|---------------|---------------|---------------------------------------------|
| A100 80GB     | 22,000        | vLLM benchmark (FP16)                       |
| H100 80GB     | 38,000        | Fireworks AI reported                       |
| H200 141GB    | 45,000        | Extrapolated (+18% from H100)               |
| B200 180GB    | 65,000        | Estimated (+71% from H100)                  |

---

## Throughput Assumptions

1. **FP16 precision** (not FP8, INT4, or quantized)
2. **Continuous batching enabled** (vLLM, TGI, or equivalent)
3. **No speculative decoding** (conservative baseline)
4. **Average sequence length**: 512 tokens (input + output)
5. **Flash Attention enabled** (standard for modern deployments)

**Reality**:
- FP8 quantization can improve throughput 1.5–2×
- Speculative decoding can improve throughput 1.5–3× (draft model assisted)
- Longer sequences (2k+ tokens) reduce throughput due to quadratic attention
- PagedAttention improves memory efficiency (enables larger batches)

---

## Data Verification Process

### Verification Checklist
1. ✅ Cross-check pricing against provider websites (Feb 2025)
2. ✅ Validate throughput against public benchmarks (vLLM, TGI)
3. ✅ Conservative estimates where no data exists (B200, H200)
4. ✅ Document sources inline (methodology.md, assumptions.md)

### Known Gaps
1. **B200 pricing**: Not publicly available (estimated based on vendor conversations)
2. **H200 throughput**: Limited public data (extrapolated from HBM3e memory bandwidth gains)
3. **Marketplace variability**: Vast.ai prices fluctuate ±30% (7-day average used)

---

## Data Update Policy

**Update Frequency**: Quarterly (or when major pricing changes occur)

### How to Update Pricing Data

1. Visit provider pricing pages
2. Update `data/platforms.py` (hourly rates, per-token pricing)
3. Update "Last Verified" date in this file
4. Re-run sanity tests: `python scripts/run_examples.py`
5. Validate no regressions in test suite: `pytest tests/`

---

## Disclaimer

**This data is for planning purposes only.**

- Pricing changes frequently (check provider websites before committing)
- Throughput varies by workload (benchmark your specific use case)
- Marketplace pricing (Vast.ai) is volatile (±30% swings)
- Custom enterprise contracts may differ significantly

**Always validate with real-world benchmarks before production deployment.**
