import { useEffect, useState } from 'react'
import { ArrowLeft, SlidersHorizontal, Sparkles, X } from 'lucide-react'
import { useLocation, useSearchParams } from 'react-router-dom'
import { useAIContext } from '@/context/AIContext'
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
  CostAuditAlternative,
} from '@/services/types'
import type { WorkloadTypeId } from '@/lib/constants'
import { WORKLOAD_TYPES } from '@/lib/constants'
import { Badge } from '@/components/ui/badge'

type Step = 'select' | 'configure'
type ConfigMode = 'copilot' | 'guided'

function canonicalWorkloadFromQuery(raw: string | null): WorkloadTypeId | null {
  if (!raw) return null
  const token = raw.trim().toLowerCase()
  if (token === 'llm') return 'llm'
  if (token === 'speech_to_text' || token === 'asr' || token === 'stt') return 'speech_to_text'
  return null
}

function formatUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

function providerNameFromId(provider: string): string {
  const token = provider.replace(/[_-]/g, ' ').trim()
  return token
    .split(/\s+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

interface AuditNavState {
  auditRecommendedOptions?: CostAuditAlternative[]
  auditModelName?: string
}

export function OptimizePage() {
  const [searchParams] = useSearchParams()
  const location = useLocation()
  const locationState = (location.state ?? {}) as AuditNavState
  const [step, setStep] = useState<Step>('select')
  const [mode, setMode] = useState<ConfigMode>('copilot')
  const [workload, setWorkload] = useState<WorkloadTypeId | null>(null)
  const [initialValues, setInitialValues] = useState<CopilotApplyPayload | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [llmResult, setLlmResult] = useState<LLMPlanningResponse | null>(null)
  const [catalogResult, setCatalogResult] = useState<CatalogRankingResponse | null>(null)
  const [auditRecommendedOptions, setAuditRecommendedOptions] = useState<CostAuditAlternative[]>([])
  const [auditModelName, setAuditModelName] = useState<string | null>(null)
  const { setAIContext } = useAIContext()

  useEffect(() => {
    if (step !== 'select' || workload !== null) return
    const queryFromAudit = searchParams.get('from') === 'audit' || searchParams.get('source') === 'audit'
    const queryWorkload = canonicalWorkloadFromQuery(searchParams.get('workload'))
    if (!queryFromAudit && queryWorkload === null) return

    const qTokens = Number(searchParams.get('tokens_per_day') ?? '')
    const qBudget = Number(searchParams.get('monthly_budget') ?? '')
    const resolvedWorkload: WorkloadTypeId = queryWorkload ?? 'llm'

    if (resolvedWorkload === 'llm') {
      const seeded: Partial<LLMFormValues> = {}
      if (Number.isFinite(qTokens) && qTokens > 0) seeded.tokens_per_day = qTokens
      if (Number.isFinite(qBudget) && qBudget > 0) seeded.monthly_budget_max_usd = qBudget
      setInitialValues(Object.keys(seeded).length > 0 ? (seeded as CopilotApplyPayload) : null)
    } else {
      const seeded: Partial<NonLLMFormValues> = { workload_type: 'speech_to_text' }
      if (Number.isFinite(qBudget) && qBudget > 0) seeded.monthly_budget_max_usd = qBudget
      setInitialValues(seeded as CopilotApplyPayload)
    }
    setWorkload(resolvedWorkload)
    setMode('guided')
    setStep('configure')
    setAuditRecommendedOptions(locationState.auditRecommendedOptions ?? [])
    setAuditModelName(locationState.auditModelName ?? null)
    setAIContext({ workload_type: resolvedWorkload, providers: [] })
  }, [locationState.auditModelName, locationState.auditRecommendedOptions, searchParams, setAIContext, step, workload])

  function handleWorkloadSelect(id: WorkloadTypeId) {
    setWorkload(id)
    setMode('copilot')
    setStep('configure')
    setInitialValues(null)
    setLlmResult(null)
    setCatalogResult(null)
    setError(null)
    setAIContext({ workload_type: id, providers: [] })
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
    setAIContext({ workload_type: null, providers: [] })
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
      setAIContext({
        workload_type: workload,
        providers: [...new Set(res.plans.map((p) => p.provider_id))],
      })
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
      setAIContext({
        workload_type: workload,
        providers: [...new Set(res.offers.map((o) => o.provider))],
      })
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
    <div className="max-w-5xl mx-auto px-5 py-8 sm:px-8">
      {/* ── Page header (select step only) ── */}
      {step === 'select' && (
        <div className="mb-8 page-section hero-panel p-5 sm:p-6">
          <div className="headline-kicker mb-2">Cost Intelligence</div>
          <h1 className="text-2xl font-bold tracking-tight mb-2">
            <span className="text-gradient">Optimize</span>{' '}
            <span style={{ color: 'var(--text-primary)' }}>Workload</span>
          </h1>
          <p className="text-sm max-w-2xl" style={{ color: 'var(--text-secondary)' }}>
            Pick a workload category and we'll rank the most cost-effective inference options
            across every major AI provider.
          </p>
        </div>
      )}

      {/* Back */}
      {step !== 'select' && (
        <button
          onClick={handleBack}
          className="flex items-center gap-1.5 text-xs mb-6 transition-colors hover:text-zinc-200"
          style={{ color: 'var(--text-tertiary)' }}
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Change workload
        </button>
      )}

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6 px-1">
        {(['select', 'configure'] as Step[]).map((s, i) => {
          const isActive = step === s
          const isDone = step === 'configure' && s === 'select'
          return (
            <div key={s} className="flex items-center gap-2">
              <div
                className="w-5 h-5 rounded-full text-[10px] flex items-center justify-center font-bold transition-all duration-200"
                style={
                  isActive
                    ? { background: 'var(--brand-gradient)', color: '#fff', boxShadow: 'var(--shadow-glow-sm)' }
                    : isDone
                    ? { background: 'rgba(124,92,252,0.15)', border: '1px solid rgba(124,92,252,0.35)', color: 'var(--brand-hover)' }
                    : { background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-default)', color: 'var(--text-disabled)' }
                }
              >
                {i + 1}
              </div>
              <span
                className="text-xs transition-colors"
                style={{ color: isActive ? 'var(--text-primary)' : 'var(--text-disabled)', fontWeight: isActive ? 600 : 400 }}
              >
                {s === 'select' ? 'Category' : 'Configure'}
              </span>
              {i < 1 && <div className="w-8 subtle-divider" />}
            </div>
          )
        })}
      </div>

      {/* ── Step: Select ── */}
      {step === 'select' && (
        <WorkloadSelector selected={workload} onSelect={handleWorkloadSelect} />
      )}

      {/* ── Step: Configure ── */}
      {step === 'configure' && workload && (
        <div className="space-y-5 animate-enter">
          {/* Workload header */}
          <div className="hero-panel p-4 sm:p-5">
            <div className="headline-kicker mb-1">{workloadMeta?.label ?? workload.replace(/_/g, ' ')}</div>
            <h2 className="text-lg font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
              Cost Optimization
            </h2>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
              {isLLM
                ? 'Capacity-aware ranking with GPU scaling, traffic modeling, and risk scoring'
                : 'Price catalog ranking with optional throughput and budget constraints'}
            </p>
          </div>

          {/* Mode tabs */}
          <div className="flex border-b border-white/[0.06] -mb-px">
            {[
              { id: 'copilot' as ConfigMode, icon: <Sparkles className="h-3.5 w-3.5" />, label: 'Ask IA AI' },
              { id: 'guided' as ConfigMode, icon: <SlidersHorizontal className="h-3.5 w-3.5" />, label: 'Guided Config' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setMode(tab.id)}
                className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-all duration-200"
                style={
                  mode === tab.id
                    ? { borderColor: 'var(--brand)', color: 'var(--brand-hover)' }
                    : { borderColor: 'transparent', color: 'var(--text-tertiary)' }
                }
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
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
              {auditRecommendedOptions.length > 0 && (
                <div className="rounded-xl border p-4 space-y-3" style={{ borderColor: 'var(--brand-border)', background: 'rgba(34,211,238,0.06)' }}>
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div>
                      <div className="eyebrow mb-0.5">From Cost Audit</div>
                      <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {auditModelName ? `Top alternatives for ${auditModelName}` : 'Top alternatives from your audit run'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setAuditRecommendedOptions([])}
                      className="text-[11px] transition-colors hover:opacity-100"
                      style={{ color: 'var(--text-disabled)' }}
                    >
                      hide
                    </button>
                  </div>
                  <div className="space-y-2">
                    {auditRecommendedOptions.slice(0, 3).map((opt, idx) => (
                      <div
                        key={`${opt.provider}-${opt.gpu_type ?? 'none'}-${opt.deployment_mode}-${idx}`}
                        className="rounded-lg border px-3 py-2 flex items-start justify-between gap-3"
                        style={{ borderColor: 'var(--border-default)', background: 'var(--bg-elevated)' }}
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>
                              {providerNameFromId(opt.provider)}
                            </span>
                            <Badge variant="default">{opt.deployment_mode}</Badge>
                            {opt.gpu_type ? <Badge variant="violet">{opt.gpu_type}</Badge> : null}
                          </div>
                          <p className="text-[11px] mt-1" style={{ color: 'var(--text-tertiary)' }}>
                            {opt.rationale}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="micro-label mb-0.5">Monthly</div>
                          <div className="text-xs font-semibold" style={{ color: 'var(--text-secondary)' }}>
                            {formatUsd(opt.estimated_monthly_cost_usd)}
                          </div>
                          <div className="text-[11px]" style={{ color: 'var(--success)' }}>
                            Save {formatUsd(Math.max(0, opt.savings_vs_current_usd))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {error && (
                <div
                  className="rounded-lg px-3 py-2.5 text-xs flex items-start justify-between gap-2 border"
                  style={{ borderColor: 'var(--danger-border)', background: 'var(--danger-bg)', color: 'var(--danger-text)' }}
                >
                  <span>{error}</span>
                  <button
                    onClick={() => setError(null)}
                    className="flex-shrink-0 transition-colors hover:text-white mt-0.5"
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
            <div className="space-y-4 pt-5 border-t border-white/[0.06] animate-enter">
              <div>
                <div className="eyebrow mb-1">Results</div>
                <h2 className="text-base font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>
                  Ranked Configurations
                </h2>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
                  {isLLM
                    ? 'Capacity-optimized plans sorted by total cost score'
                    : 'Sorted by normalized unit price'}
                </p>
              </div>
              <p className="text-[11px]" style={{ color: 'var(--text-disabled)' }}>
                Demo flow shows one ranking table, one cost chart, and explainability diagnostics.
              </p>

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
