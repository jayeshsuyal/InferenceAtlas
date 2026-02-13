# Model Assumptions

This document explicitly lists all assumptions embedded in the InferenceAtlas recommendation engine.

---

## Time Model

| Constant            | Value      | Notes                                |
|---------------------|------------|--------------------------------------|
| `HOURS_PER_MONTH`   | 720        | 30 days × 24 hours                   |
| `DAYS_PER_MONTH`    | 30         | Simplified month model               |
| `SECONDS_PER_DAY`   | 86,400     | 24 hours × 60 min × 60 sec           |

**Implication**: February (28 days) and long months (31 days) are not distinguished. Real costs will vary ±3% based on calendar month length.

---

## Traffic Pattern Assumptions

### Steady (24/7 Load)
- Traffic is **uniformly distributed** across all hours
- Batching efficiency is **high** (0.85) due to consistent load
- No burst spikes (burst_factor = 1.0)
- Batching provides **25% throughput gain**

### Business Hours (40 hours/week)
- Traffic occurs only during **weekday work hours** (8 AM–5 PM, Mon–Fri)
- **23.8%** of total hours are active (40/168)
- No weekend or overnight traffic
- Batching provides **10% throughput gain**

### Bursty (Irregular Spikes)
- Traffic is concentrated in **40% of hours**
- Peak traffic is **3× the hourly average** during active periods
- Lower batching efficiency (0.70) due to irregular request patterns
- Batching provides **35% throughput gain** (better gains under load)

**Reality Check**: Real traffic patterns are more complex (gradual ramps, seasonal variation, geographic distribution). These profiles are simplified reference models.

---

## GPU Efficiency Factors

| Pattern         | Efficiency | Interpretation                           |
|-----------------|------------|------------------------------------------|
| Steady          | 0.85       | 15% overhead (batching, scheduling)      |
| Business Hours  | 0.80       | 20% overhead                             |
| Bursty          | 0.70       | 30% overhead (irregular load, cold GPUs) |

**Sources**:
- Based on reported efficiency factors from Fireworks AI, Together AI, and vLLM benchmarks
- Conservative estimates (real-world may vary ±10%)

**Not Modeled**:
- Warmup time after idle periods
- Cache hit rates
- Speculative decoding gains
- Flash Attention improvements

---

## Batching Multipliers

| Pattern         | Batch Mult | Interpretation                              |
|-----------------|------------|---------------------------------------------|
| Steady          | 1.25       | +25% throughput from continuous batching    |
| Business Hours  | 1.10       | +10% throughput from moderate batching      |
| Bursty          | 1.35       | +35% throughput from large batch bursts     |

**Assumptions**:
- Assumes dynamic batching is enabled (e.g., vLLM continuous batching)
- Larger batches → better GPU utilization → higher throughput
- Bursty traffic allows larger batch sizes during spikes

**Not Modeled**:
- Batch size limits (max tokens per batch)
- Latency impact of waiting for batch fill
- KV cache memory constraints

---

## Multi-GPU Scaling

| Parameter       | Value | Rationale                                    |
|-----------------|-------|----------------------------------------------|
| `U_TARGET`      | 0.75  | Target utilization ceiling (75%)             |
| `MAX_GPUS`      | 8     | Maximum GPUs before architectural changes    |

### 75% Utilization Target
- Provides **25% headroom** for traffic bursts
- Reduces latency variance (queue depth remains low)
- Industry standard for production GPU deployments

**If utilization_ratio > 0.75**: Scale to multiple GPUs via `ceil(utilization_ratio / 0.75)`.

### 8-GPU Limit
- Beyond 8 GPUs, alternative approaches are more efficient:
  - Tensor parallelism (split model across GPUs)
  - Pipeline parallelism
  - Model sharding (e.g., DeepSpeed, Megatron)
- Configurations requiring >8 GPUs incur **$50k/GPU penalty** to flag architectural rethinking

**Not Modeled**:
- Inter-GPU communication overhead (NVLink, PCIe bandwidth)
- Load balancing efficiency across GPUs
- GPU failure modes (redundancy, failover)

---

## Memory Model

### Model Memory Requirements

| Model           | Recommended Memory | Source                          |
|-----------------|--------------------|---------------------------------|
| Llama 3.1 8B    | 16 GB              | FP16 weights + 4GB KV cache     |
| Llama 3.1 70B   | 80 GB              | FP16 weights + 10GB KV cache    |
| Llama 3.1 405B  | 400 GB             | FP16 weights + tensor parallel  |
| Mixtral 8x7B    | 90 GB              | MoE architecture (sparse)       |
| Mistral 7B      | 16 GB              | FP16 weights + 4GB KV cache     |

**Assumptions**:
- **FP16 precision** (not FP8, INT8, or quantized)
- **KV cache overhead**: ~10–20% of model size
- **No PagedAttention** or memory optimizations
- **Single-instance deployment** (not tensor parallel)

**Reality**:
- Quantization (FP8, INT4) can reduce memory by 2–4×
- PagedAttention (vLLM) reduces KV cache overhead
- Tensor parallelism allows larger models on smaller GPUs

---

## Cost Model Assumptions

### Autoscaling Platforms (Fireworks, etc.)
- **Active hours**: `HOURS_PER_MONTH × active_ratio`
- **Idle waste**: 0 (pay only for active hours)
- **Instant scaling**: No cold start delays

### Dedicated Platforms (RunPod, Modal, etc.)
- **Always-on billing**: 720 hours/month regardless of utilization
- **Idle waste**: `(720 - active_hours) × hourly_rate × gpu_count`
- **No spot pricing**: Uses on-demand rates

### Per-Token Platforms (Together AI, etc.)
- **No GPU provisioning**: Pay per token consumed
- **No idle waste**
- **No multi-GPU scaling** (managed by provider)

---

## Latency Risk Model

| Utilization After | Risk Band | Assumptions                               |
|-------------------|-----------|-------------------------------------------|
| ≤ 50%             | Low       | Queue depth < 2, P99 latency acceptable   |
| 51–75%            | Medium    | Queue depth 2–5, P99 latency tolerable    |
| > 75%             | High      | Queue depth > 5, P99 latency spikes       |

**Strict Latency Threshold**: 300ms
- Requests < 300ms are considered "strict" (real-time, chat apps)
- High-risk configurations incur $30k penalty

**Not Modeled**:
- Actual P50/P95/P99 latency distributions
- TTFT (time-to-first-token) vs. TPOT (throughput)
- Network latency (assumes local inference)
- Cold start overhead (serverless platforms)

---

## Pricing Assumptions

### Data Currency
- Pricing data is **snapshot-based** (February 2025)
- Actual pricing changes over time (check provider websites)
- Marketplace pricing (Vast.ai) uses **average prices**, not spot/bid

### Billing Granularity
- **Hourly billing**: Assumes sub-hour usage rounds up to full hour
- **Per-second billing**: Assumes true second-level billing (e.g., Replicate)
- **No egress costs**: Assumes all traffic is within-region

### No Discounts
- **On-demand rates only** (no reserved instances, volume discounts)
- **No spot pricing** (no preemption risk)
- **No custom enterprise contracts**

---

## What We DO NOT Model

### Infrastructure
- ❌ Network latency (region, CDN)
- ❌ Storage costs (model weights, logs)
- ❌ Egress/bandwidth costs
- ❌ Load balancer overhead

### Inference Engine
- ❌ Speculative decoding gains
- ❌ Quantization (FP8, INT4)
- ❌ Flash Attention impact
- ❌ PagedAttention memory savings
- ❌ Prefix caching benefits

### Operational
- ❌ Cold start times (serverless)
- ❌ Autoscaling lag (spin-up delays)
- ❌ GPU failure rates
- ❌ Request queueing dynamics (M/M/1, M/M/c models)
- ❌ Retry logic, circuit breakers

### Workload
- ❌ Sequence length distribution (assumes average)
- ❌ Input vs. output token ratio
- ❌ Concurrent user behavior
- ❌ Geographic traffic patterns

---

## Model Confidence

| Component                | Confidence | Notes                                    |
|--------------------------|------------|------------------------------------------|
| Cost formulas            | High       | Simple arithmetic, vendor-confirmed      |
| Multi-GPU scaling math   | High       | Based on established patterns            |
| Traffic pattern profiles | Medium     | Simplified reference models              |
| Efficiency factors       | Medium     | Based on public benchmarks (±10% variance)|
| Latency risk bands       | Low        | Heuristic thresholds, not empirical      |
| Penalty magnitudes       | Low        | Arbitrary values to nudge recommendations|

---

## Validation Strategy

1. **Sanity tests**: 6 example scenarios with known expected behavior
2. **Unit tests**: Mathematical consistency (no division by zero, cost monotonicity)
3. **Comparative benchmarking**: Results should directionally align with real-world costs

**Use InferenceAtlas for initial planning. Validate with real-world benchmarks before production deployment.**
