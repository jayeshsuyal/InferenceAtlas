# Methodology

This document explains the mathematical models underlying InferenceAtlas recommendations.

## Overview

InferenceAtlas is a **planning model**, not a real-time simulator. It estimates:
- GPU requirements for serving LLM workloads
- Multi-GPU scaling behavior
- Monthly infrastructure costs across platforms
- Latency risk exposure

The model is intended for initial capacity planning and comparative analysis. Real-world performance should be validated with provider-specific benchmarks.

---

## Traffic Modeling

### 1. Daily Volume → Average Throughput

Given daily token volume, compute average tokens per second:

```
avg_tps = tokens_per_day / 86,400
```

This represents **global average throughput** distributed uniformly across 24 hours.

---

### 2. Traffic Patterns

Real workloads are not uniformly distributed. We model three patterns:

#### Steady (24/7 uniform load)
- **Active ratio**: 1.0 (traffic 100% of time)
- **Efficiency**: 0.85 (high batching efficiency)
- **Burst factor**: 1.0 (no spikes)
- **Batch multiplier**: 1.25 (25% throughput gain from batching)

#### Business Hours (40 hours/week)
- **Active ratio**: 0.238 (40/168 hours)
- **Efficiency**: 0.80 (moderate batching)
- **Burst factor**: 1.0 (predictable daytime load)
- **Batch multiplier**: 1.10 (10% gain)

#### Bursty (irregular spikes)
- **Active ratio**: 0.40 (traffic ~40% of time)
- **Efficiency**: 0.70 (lower batching due to irregular patterns)
- **Burst factor**: 3.0 (peak is 3× average)
- **Batch multiplier**: 1.35 (35% gain under load)

---

### 3. Peak Load Calculation

Peak throughput during active periods:

```
required_peak_tps = (avg_tps / active_ratio) × burst_factor
```

**Example (Business Hours)**:
- avg_tps = 100 tokens/sec (global)
- active_ratio = 0.238
- burst_factor = 1.0
- **required_peak_tps** = (100 / 0.238) × 1.0 = **420 tokens/sec**

---

## GPU Throughput Modeling

### 1. Effective Throughput

Raw GPU specs (e.g., "15,000 tokens/sec") represent theoretical maximum. Real-world throughput accounts for:
- Batching/scheduling overhead (**efficiency** factor)
- Throughput gains from request batching (**batch_mult** factor)

```
effective_gpu_tps = gpu_tokens_per_second × efficiency × batch_mult
```

**Example (H100 80GB, Steady pattern)**:
- Raw: 15,000 tokens/sec
- Efficiency: 0.85
- Batch mult: 1.25
- **Effective**: 15,000 × 0.85 × 1.25 = **15,937 tokens/sec**

---

### 2. Model-Specific Throughput

Different models have different memory/compute profiles. The platform catalog includes per-model throughput overrides:

```python
"throughput_by_model": {
    "llama_8b": 35000,
    "llama_70b": 15000,
    "llama_405b": 2800,
}
```

If a model-specific value exists, it replaces the default `tokens_per_second`.

---

## Multi-GPU Scaling

### 1. Utilization Ratio (Single GPU)

```
utilization_ratio = required_peak_tps / effective_gpu_tps
```

This represents **per-GPU utilization** if deployed on a single GPU.

---

### 2. Scaling to Multiple GPUs

If `utilization_ratio > 0.75` (target threshold), scale to multiple GPUs:

```
gpu_count = ceil(utilization_ratio / 0.75)
```

**75% Target Utilization Rule**:
- Provides 25% headroom for bursts
- Reduces latency variance
- Allows safe operation without saturation

---

### 3. Post-Scaling Utilization

```
utilization_after = utilization_ratio / gpu_count
```

This is the **actual utilization per GPU** after scaling.

**Example**:
- utilization_ratio = 1.8 (180% on single GPU)
- gpu_count = ceil(1.8 / 0.75) = ceil(2.4) = **3 GPUs**
- utilization_after = 1.8 / 3 = **0.60** (60% per GPU)

---

## Latency Risk Bands

Latency is not directly modeled but inferred from utilization:

| Utilization After | Risk Band | Interpretation                     |
|-------------------|-----------|------------------------------------|
| ≤ 50%             | **Low**   | Ample headroom, low queue depth    |
| 51–75%            | **Medium**| Target range, acceptable latency   |
| > 75%             | **High**  | Approaching saturation, tail spikes|

For strict latency requirements (< 300ms), configurations with "high" risk incur a **$30k penalty**.

---

## Cost Calculation

### 1. GPU-Backed Platforms

#### Autoscaling (e.g., Fireworks)
Pay only for active hours:
```
monthly_cost = active_hours_per_month × hourly_rate × gpu_count
idle_waste = 0
```

#### Dedicated (e.g., RunPod, Modal)
Pay for full month (720 hours):
```
monthly_cost = 720 × hourly_rate × gpu_count
idle_hours = 720 - active_hours_per_month
idle_waste = idle_hours × hourly_rate × gpu_count
idle_waste_pct = (idle_waste / monthly_cost) × 100
```

---

### 2. Per-Token Platforms (e.g., Together AI)

```
monthly_tokens = tokens_per_day × 30
monthly_cost = (monthly_tokens / 1,000,000) × price_per_m_tokens
```

No idle waste (only charged for tokens consumed).

---

### 3. Cost per Million Tokens

Unified metric for cross-platform comparison:

```
cost_per_m_tokens = (monthly_cost / monthly_tokens) × 1,000,000
```

---

## Penalty Model

Recommendations are ranked by: **monthly_cost + penalties**

### 1. Overload Penalty (>90% utilization)
```
if utilization_after > 0.90:
    penalty += $20,000 × ((utilization_after - 0.90) / 0.10)
```
- Linear ramp from 90% → 100%
- Reaches $20k at 100% utilization

### 2. Scaling Penalty (>8 GPUs)
```
if gpu_count > 8:
    penalty += $50,000 × (gpu_count - 8)
```
- Penalizes excessive multi-GPU configurations
- Flags workloads requiring architectural changes (tensor parallelism, model sharding)

### 3. Strict Latency Penalty
```
if latency_risk == "high" and latency_requirement_ms < 300:
    penalty += $30,000
```
- Applied only for strict latency requirements
- Discourages high-utilization configs for latency-sensitive apps

---

## Month Model

All calculations use a **30-day month**:
- **720 hours** per month
- **30 days** per month

This is a simplified model. Actual calendar months vary (28–31 days).

---

## What This Model Does NOT Account For

- **Network latency** (assumes local inference only)
- **Cold start overhead** (serverless platforms)
- **Model loading time** (startup latency)
- **Dynamic batching behavior** (assumes static efficiency)
- **Tensor parallelism** (multi-GPU within a single model instance)
- **Preemption/spot pricing** (marketplace variability)
- **Request queueing dynamics** (Markovian queueing theory)
- **TTFT (time-to-first-token)** vs. TPOT (tokens-per-output-token)
- **KV cache size impact** on memory requirements

---

## Validation Approach

The model is validated through:
1. **Sanity tests** (examples/): Known workload scenarios with expected outcomes
2. **Unit tests** (tests/): Mathematical consistency checks
3. **Comparative benchmarking**: Results should directionally match real-world costs

**Use this model for planning, not production SLA guarantees.**
