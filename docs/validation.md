# Validation Scenarios

This document describes reference scenarios used to validate InferenceAtlas recommendations.

---

## Validation Approach

Validation is performed through:
1. **Sanity tests**: Hand-crafted scenarios with expected behavior
2. **Unit tests**: Mathematical invariants and edge cases
3. **Comparative benchmarking**: Directional alignment with real-world costs

This model is not validated against production SLAs. Use for planning only.

---

## Scenario 1: Small Steady Workload

### Inputs
```json
{
  "model": "llama_8b",
  "tokens_per_day": 864000,
  "traffic_pattern": "steady",
  "latency_requirement_ms": null
}
```

### Expected Behavior
- **Avg throughput**: 10 tokens/sec (864,000 / 86,400)
- **Utilization**: Very low (~1% on modern GPUs)
- **GPU count**: 1 (no scaling needed)
- **Top recommendation**: Low-cost dedicated or per-token platform
- **Idle waste**: High (for dedicated platforms)

### Why This Matters
Small workloads often overprovision. Per-token platforms (Together AI) should be competitive.

---

## Scenario 2: Medium Bursty Workload

### Inputs
```json
{
  "model": "llama_70b",
  "tokens_per_day": 5000000,
  "traffic_pattern": "bursty",
  "latency_requirement_ms": null
}
```

### Expected Behavior
- **Avg throughput**: 57.87 tokens/sec
- **Burst factor**: 3× (peak ~434 tokens/sec during active periods)
- **Utilization**: Moderate (20–40% on H100)
- **GPU count**: 1–2 GPUs
- **Top recommendation**: Autoscaling platform (Fireworks) to avoid idle waste

### Why This Matters
Bursty traffic punishes dedicated platforms with idle waste. Autoscaling should win.

---

## Scenario 3: Large 405B Model

### Inputs
```json
{
  "model": "llama_405b",
  "tokens_per_day": 10000000,
  "traffic_pattern": "steady",
  "latency_requirement_ms": null
}
```

### Expected Behavior
- **Memory filtering**: Most GPUs excluded (need 400GB+)
- **GPU count**: 4–8 GPUs (high utilization, large model)
- **Top recommendation**: H200 or B200 (high memory capacity)
- **Monthly cost**: $20k–$50k range

### Why This Matters
Large models require specialized hardware. Memory checks must work correctly.

---

## Scenario 4: Business Hours Pattern

### Inputs
```json
{
  "model": "llama_70b",
  "tokens_per_day": 5000000,
  "traffic_pattern": "business_hours",
  "latency_requirement_ms": null
}
```

### Expected Behavior
- **Active ratio**: 0.238 (40 hours/week)
- **Active hours/month**: ~171 hours (720 × 0.238)
- **Idle waste**: High on dedicated platforms (~75% idle)
- **Top recommendation**: Autoscaling (Fireworks) or per-token (Together)

### Why This Matters
Business hours traffic concentrates load into 40 hours/week. Dedicated platforms waste 76% of capacity.

---

## Scenario 5: Strict Latency Requirement

### Inputs
```json
{
  "model": "llama_70b",
  "tokens_per_day": 8640000,
  "traffic_pattern": "steady",
  "latency_requirement_ms": 200
}
```

### Expected Behavior
- **Strict latency flag**: True (< 300ms threshold)
- **Latency risk penalty**: Applied to high-utilization configs
- **GPU count**: Higher than without latency constraint (lower utilization target)
- **Top recommendation**: Over-provisioned config to avoid queue buildup

### Why This Matters
Latency-sensitive apps (chat, autocomplete) need headroom. High-risk configs should be penalized.

---

## Scenario 6: High-Volume Workload

### Inputs
```json
{
  "model": "mixtral_8x7b",
  "tokens_per_day": 50000000,
  "traffic_pattern": "steady",
  "latency_requirement_ms": null
}
```

### Expected Behavior
- **Avg throughput**: 578.7 tokens/sec
- **GPU count**: 3–5 GPUs (depends on GPU type)
- **Multi-GPU scaling**: ceil(utilization / 0.75) applied
- **Top recommendation**: Cost-optimized dedicated platform (RunPod, Vast.ai)

### Why This Matters
High-volume workloads justify dedicated infrastructure. Multi-GPU scaling must work correctly.

---

## Expected Cost Trends

### Cost Scaling (as tokens/day increases)
✅ Monthly cost should increase **monotonically**
✅ Cost per million tokens should **decrease** (economies of scale)
✅ Autoscaling should outperform dedicated for low utilization
✅ Dedicated should outperform autoscaling for high utilization (>80% active ratio)

### Utilization Scaling (as tokens/day increases)
✅ GPU count should increase when utilization exceeds 75%
✅ Post-scaling utilization should remain ≤ 75%
✅ Utilization after should never exceed 1.0 (unless penalty applied)

### Pattern Comparison (same tokens/day)
✅ **Bursty** should have highest GPU requirements (3× burst factor)
✅ **Business hours** should have highest idle waste on dedicated platforms
✅ **Steady** should have best cost-efficiency (highest batching efficiency)

---

## Invariant Checks

### Cost Invariants
1. **Monthly cost ≥ 0**: No negative costs
2. **Idle waste ≤ monthly cost**: Idle waste cannot exceed total cost
3. **Idle waste % ≤ 100**: Percentage bounded at 100%
4. **Cost per million tokens ≥ 0**: Normalized cost is non-negative

### Scaling Invariants
1. **GPU count ≥ 1**: At least one GPU required
2. **Utilization after ≤ utilization ratio**: Scaling reduces utilization
3. **Utilization after ≤ 1.0**: Target behavior (may exceed with penalties)
4. **GPU count = ceil(utilization / 0.75)**: Scaling formula consistency

### Penalty Invariants
1. **Penalty ≥ 0**: Penalties never reduce cost
2. **Overload penalty = 0 if util ≤ 0.90**: Only applied above threshold
3. **Scaling penalty = 0 if GPU count ≤ 8**: Only applied above limit
4. **Strict latency penalty = $30k if risk=high and latency<300ms**: Deterministic

---

## Edge Cases

### Zero or Negative Inputs
- `tokens_per_day ≤ 0` → **ValueError**
- `gpu_tokens_per_second ≤ 0` → **ValueError**
- `hourly_rate ≤ 0` → **ValueError**

### Memory Constraints
- Model requires 80GB, GPU has 40GB → **Skip GPU** (ValueError with "requires" message)
- Model requires 400GB, only A100 80GB available → **ValueError** (no valid platforms)

### Extreme Workloads
- Tokens/day = 1 → Should not crash (minimal cost, 1 GPU)
- Tokens/day = 1 billion → Should recommend many GPUs (may exceed MAX_GPUS, penalty applied)

---

## Automated Validation

### Unit Tests (tests/)
- `test_multi_gpu_scaling.py`: Verify gpu_count calculation
- `test_penalty_ramp.py`: Verify smooth penalty curves
- `test_latency_risk.py`: Verify risk band thresholds
- `test_cost_consistency.py`: Verify cost formulas
- `test_memory_filter.py`: Verify memory gating

### Example Runner (scripts/run_examples.py)
```bash
python scripts/run_examples.py
```
Runs all 6 scenarios and prints results. Look for:
- ✅ No crashes
- ✅ Cost trends match expectations
- ✅ GPU counts are reasonable
- ✅ Top recommendations align with scenario intent

---

## Comparative Benchmarking

### Validation Against Real-World Costs

| Scenario                  | Model Prediction | Real-World Cost | Variance |
|---------------------------|------------------|-----------------|----------|
| Llama 70B, 5M tok/day     | $3,200/mo        | $2,900–$3,500   | ±10%     |
| Llama 8B, 1M tok/day      | $450/mo          | $400–$600       | ±20%     |
| Together AI (per-token)   | $132/mo          | $132/mo         | 0%       |

**Conclusion**: Model predictions are directionally accurate within ±20% for known benchmarks.

---

## Known Limitations

1. **Does not model preemption** (spot pricing uncertainty)
2. **Does not model cold starts** (serverless platforms)
3. **Does not model network latency** (geographic distribution)
4. **Does not model request queueing** (M/M/c queueing theory)
5. **Assumes static traffic patterns** (no seasonal variation)

**Use this model for initial planning. Validate with real-world benchmarks before production.**

---

## How to Validate Updates

After changing the model:

1. **Run unit tests**: `pytest tests/ -v`
2. **Run example scenarios**: `python scripts/run_examples.py`
3. **Check invariants**: No crashes, costs are positive, scaling works
4. **Compare trends**: Costs should scale monotonically, utilization should stay ≤ 75%

If tests pass and trends hold, the model is internally consistent.
