import { useState } from 'react'
import { ArrowLeft, Sparkles, SlidersHorizontal, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { WorkloadSelector } from '@/components/WorkloadSelector'
import { LLMForm } from '@/components/optimize/LLMForm'
import { NonLLMForm } from '@/components/optimize/NonLLMForm'
import { CopilotPanel } from '@/components/optimize/CopilotPanel'
import { ResultsTable } from '@/components/optimize/ResultsTable'
import { SkeletonCard } from '@/components/ui/skeleton'
import { planLLMWorkload, rankCatalogOffers } from '@/services/api'
import type { LLMFormValues, NonLLMFormValues } from '@/schemas/forms'
import type {
  LLMPlanningResponse,
  CatalogRankingResponse,
  CopilotApplyPayload,
} from '@/services/types'
import type { WorkloadTypeId } from '@/lib/constants'
import { WORKLOAD_TYPES } from '@/lib/constants'

type Step = 'select' | 'configure'
type ConfigMode = 'copilot' | 'guided'

export function OptimizePage() {
  const [step, setStep] = useState<Step>('select')
  const [mode, setMode] = useState<ConfigMode>('copilot')
  const [workload, setWorkload] = useState<WorkloadTypeId | null>(null)
  const [initialValues, setInitialValues] = useState<CopilotApplyPayload | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [llmResult, setLlmResult] = useState<LLMPlanningResponse | null>(null)
  const [catalogResult, setCatalogResult] = useState<CatalogRankingResponse | null>(null)

  function handleWorkloadSelect(id: WorkloadTypeId) {
    setWorkload(id)
    setMode('copilot')
    setStep('configure')
    setInitialValues(null)
    setLlmResult(null)
    setCatalogResult(null)
    setError(null)
  }

  function handleApply(payload: CopilotApplyPayload) {
    setInitialValues(payload)
    setMode('guided')
    setError(null)
  }

  function handleBack() {
    setStep('select')
    setWorkload(null)
    setInitialValues(null)
    setLlmResult(null)
    setCatalogResult(null)
    setError(null)
  }

  async function handleLLMSubmit(values: LLMFormValues) {
    setLoading(true)
    setError(null)
    try {
      const res = await planLLMWorkload({
        tokens_per_day: values.tokens_per_day,
        model_bucket: values.model_bucket,
        provider_ids: values.provider_ids,
        peak_to_avg: values.peak_to_avg,
        util_target: values.util_target,
        beta: values.beta,
        alpha: values.alpha,
        autoscale_inefficiency: values.autoscale_inefficiency,
        monthly_budget_max_usd: values.monthly_budget_max_usd,
        output_token_ratio: values.output_token_ratio,
        top_k: values.top_k,
      })
      setLlmResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Planning failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleNonLLMSubmit(values: NonLLMFormValues) {
    setLoading(true)
    setError(null)
    try {
      const res = await rankCatalogOffers({
        workload_type: values.workload_type,
        allowed_providers: values.provider_ids,
        unit_name: values.unit_name,
        monthly_usage: values.monthly_usage,
        monthly_budget_max_usd: values.monthly_budget_max_usd,
        top_k: values.top_k,
        confidence_weighted: values.confidence_weighted,
        comparator_mode: values.comparator_mode,
        throughput_aware: values.throughput_aware,
        peak_to_avg: values.peak_to_avg,
        util_target: values.util_target,
        strict_capacity_check: values.strict_capacity_check,
      })
      setCatalogResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ranking failed')
    } finally {
      setLoading(false)
    }
  }

  const isLLM = workload === 'llm'
  const hasResults = isLLM ? llmResult !== null : catalogResult !== null
  const workloadMeta = WORKLOAD_TYPES.find((w) => w.id === workload)

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 sm:px-6">
      {/* Back */}
      {step !== 'select' && (
        <button
          onClick={handleBack}
          className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 mb-5 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Change workload
        </button>
      )}

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6">
        {(['select', 'configure'] as Step[]).map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={cn(
                'w-5 h-5 rounded-full text-[10px] flex items-center justify-center font-bold',
                step === s
                  ? 'bg-indigo-600 text-white'
                  : step === 'configure' && s === 'select'
                  ? 'bg-indigo-950 border border-indigo-700 text-indigo-400'
                  : 'bg-zinc-800 text-zinc-500'
              )}
            >
              {i + 1}
            </div>
            <span
              className={cn(
                'text-xs',
                step === s ? 'font-medium text-zinc-200' : 'text-zinc-600'
              )}
            >
              {s === 'select' ? 'Category' : 'Configure'}
            </span>
            {i < 1 && <div className="w-6 subtle-divider" />}
          </div>
        ))}
      </div>

      {/* ── Step: Select ── */}
      {step === 'select' && (
        <WorkloadSelector selected={workload} onSelect={handleWorkloadSelect} />
      )}

      {/* ── Step: Configure ── */}
      {step === 'configure' && workload && (
        <div className="space-y-5">
          {/* Workload header */}
          <div>
            <h2 className="text-base font-semibold text-zinc-100">
              {workloadMeta?.label ?? workload.replace(/_/g, ' ')} optimization
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              {isLLM
                ? 'Capacity-aware ranking with GPU scaling, traffic modeling, and risk scoring'
                : 'Price catalog ranking with optional throughput and budget constraints'}
            </p>
          </div>

          {/* Mode tabs */}
          <div className="flex border-b border-white/[0.06] -mb-px">
            <button
              type="button"
              onClick={() => setMode('copilot')}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all duration-200',
                mode === 'copilot'
                  ? 'border-indigo-500 text-indigo-300'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:border-white/[0.10]'
              )}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Ask IA AI
            </button>
            <button
              type="button"
              onClick={() => setMode('guided')}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all duration-200',
                mode === 'guided'
                  ? 'border-indigo-500 text-indigo-300'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:border-white/[0.10]'
              )}
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              Guided Config
            </button>
          </div>

          {/* ── Copilot mode ── */}
          {mode === 'copilot' && (
            <CopilotPanel
              workloadType={workload}
              isLLM={isLLM}
              onApply={handleApply}
            />
          )}

          {/* ── Guided mode ── */}
          {mode === 'guided' && (
            <>
              {error && (
                <div className="rounded-md border border-red-800 bg-red-950/30 px-3 py-2.5 text-xs text-red-300 flex items-start justify-between gap-2">
                  <span>{error}</span>
                  <button
                    onClick={() => setError(null)}
                    className="flex-shrink-0 text-red-400 hover:text-red-200 transition-colors mt-0.5"
                    aria-label="Dismiss error"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}

              {isLLM ? (
                <LLMForm
                  key={`llm-${JSON.stringify(initialValues)}`}
                  onSubmit={handleLLMSubmit}
                  loading={loading}
                  initialValues={initialValues as Partial<LLMFormValues> | undefined}
                />
              ) : (
                <NonLLMForm
                  key={`non-llm-${JSON.stringify(initialValues)}`}
                  workloadType={workload}
                  onSubmit={handleNonLLMSubmit}
                  loading={loading}
                  initialValues={initialValues as Partial<NonLLMFormValues> | undefined}
                />
              )}
            </>
          )}

          {/* Loading skeleton */}
          {loading && (
            <div className="space-y-3 pt-2">
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </div>
          )}

          {/* ── Shared results panel ── */}
          {hasResults && !loading && (
            <div className="space-y-4 pt-4 border-t border-white/[0.06] animate-enter">
              <div>
                <h2 className="text-base font-semibold text-zinc-100">Ranked results</h2>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {isLLM
                    ? 'Capacity-optimized plans sorted by total cost score'
                    : 'Sorted by normalized unit price'}
                </p>
              </div>

              {isLLM ? (
                <ResultsTable
                  mode="llm"
                  plans={llmResult?.plans ?? []}
                  diagnostics={llmResult?.provider_diagnostics ?? []}
                  warnings={llmResult?.warnings ?? []}
                  excludedCount={llmResult?.excluded_count ?? 0}
                />
              ) : (
                <ResultsTable
                  mode="non-llm"
                  offers={catalogResult?.offers ?? []}
                  diagnostics={catalogResult?.provider_diagnostics ?? []}
                  warnings={catalogResult?.warnings ?? []}
                  excludedCount={catalogResult?.excluded_count ?? 0}
                />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
