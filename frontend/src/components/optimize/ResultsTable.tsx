import { lazy, Suspense, useState } from 'react'
import { ChevronDown, ChevronUp, Info, Trophy } from 'lucide-react'
import { cn, formatUSD, formatPercent, riskLevel, confidenceLabel, billingModeLabel, capacityLabel } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import type { RankedPlan, RankedCatalogOffer, ProviderDiagnostic } from '@/services/types'
import { ASSUMPTION_LABELS } from '@/lib/constants'
const InsightsCharts = lazy(() =>
  import('@/components/optimize/InsightsCharts').then((module) => ({
    default: module.InsightsCharts,
  }))
)

// ─── Confidence badge ─────────────────────────────────────────────────────────

function ConfidenceBadge({ confidence }: { confidence: string }) {
  const variant = confidence as 'high' | 'official' | 'medium' | 'estimated' | 'low' | 'vendor_list'
  return <Badge variant={variant}>{confidenceLabel(confidence)}</Badge>
}

function RiskBadge({ totalRisk }: { totalRisk: number }) {
  const level = riskLevel(totalRisk)
  const variant = `risk_${level}` as 'risk_low' | 'risk_medium' | 'risk_high'
  const labels = { low: 'Low risk', medium: 'Med risk', high: 'High risk' }
  return <Badge variant={variant}>{labels[level]}</Badge>
}

function CapacityBadge({ check }: { check: string }) {
  const variant = check as 'ok' | 'insufficient' | 'unknown'
  return <Badge variant={variant}>{capacityLabel(check)}</Badge>
}

// ─── LLM result card ──────────────────────────────────────────────────────────

function LLMResultCard({ plan, isFirst, index }: { plan: RankedPlan; isFirst: boolean; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      style={{ animationDelay: `${index * 50}ms` }}
      className={cn(
        'rounded-lg border transition-all duration-200 animate-enter',
        'hover:-translate-y-px hover:shadow-md',
        isFirst
          ? 'border-indigo-500/30 bg-indigo-950/20 shadow-[0_0_18px_rgba(99,102,241,0.12)] ring-1 ring-indigo-500/20'
          : 'border-white/[0.07] bg-zinc-900/60 hover:border-white/[0.11]'
      )}
    >
      <div className="p-4">
        {/* Rank + header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5">
            <div
              className={cn(
                'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
                isFirst
                  ? 'bg-indigo-600 text-white shadow-glow-sm'
                  : 'bg-zinc-800/80 text-zinc-400 border border-white/[0.06]'
              )}
            >
              {isFirst ? <Trophy className="w-3.5 h-3.5" /> : plan.rank}
            </div>
            <div>
              <div className="text-sm font-semibold text-zinc-100">{plan.provider_name}</div>
              <div className="text-[11px] text-zinc-500 font-mono mt-0.5">{plan.offering_id}</div>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <div className={cn(
              'text-lg font-bold font-numeric',
              isFirst ? 'text-indigo-200' : 'text-zinc-100'
            )}>
              {formatUSD(plan.monthly_cost_usd, 0)}
            </div>
            <div className="text-[10px] text-zinc-500">/ month</div>
          </div>
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <Badge variant="default">{billingModeLabel(plan.billing_mode)}</Badge>
          <ConfidenceBadge confidence={plan.confidence} />
          <RiskBadge totalRisk={plan.risk.total_risk} />
          {plan.utilization_at_peak !== null && (
            <Badge variant="default">
              {formatPercent(plan.utilization_at_peak)} util
            </Badge>
          )}
        </div>

        {/* Why */}
        <p className="text-xs text-zinc-400 leading-relaxed">{plan.why}</p>

        {/* Expand assumptions */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 mt-3 text-[11px] text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <Info className="h-3 w-3" />
          Assumptions
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-3 border-t border-white/[0.05] pt-3 animate-enter-fast">
          <div className="grid grid-cols-3 gap-x-4 gap-y-1.5">
            {Object.entries(plan.assumptions).map(([key, val]) => (
              <div key={key}>
                <div className="text-[10px] text-zinc-500">{ASSUMPTION_LABELS[key] ?? key}</div>
                <div className="text-xs font-mono text-zinc-300">{val}</div>
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t border-white/[0.05] grid grid-cols-2 gap-x-4">
            <div>
              <div className="text-[10px] text-zinc-500">Overload risk</div>
              <div className="text-xs font-mono text-zinc-300">
                {formatPercent(plan.risk.risk_overload)}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-zinc-500">Complexity risk</div>
              <div className="text-xs font-mono text-zinc-300">
                {formatPercent(plan.risk.risk_complexity)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Non-LLM result row ───────────────────────────────────────────────────────

function NonLLMResultRow({ offer, isFirst, index }: { offer: RankedCatalogOffer; isFirst: boolean; index: number }) {
  return (
    <div
      style={{ animationDelay: `${index * 40}ms` }}
      className={cn(
        'flex items-center gap-4 px-4 py-3 rounded-lg border transition-all duration-200 animate-enter',
        'hover:-translate-y-px hover:shadow-md',
        isFirst
          ? 'border-indigo-500/30 bg-indigo-950/20 shadow-[0_0_14px_rgba(99,102,241,0.10)] ring-1 ring-indigo-500/20'
          : 'border-white/[0.07] bg-zinc-900/60 hover:border-white/[0.11]'
      )}
    >
      {/* Rank */}
      <div
        className={cn(
          'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
          isFirst
            ? 'bg-indigo-600 text-white shadow-glow-sm'
            : 'bg-zinc-800/80 text-zinc-400 border border-white/[0.06]'
        )}
      >
        {isFirst ? <Trophy className="w-3.5 h-3.5" /> : offer.rank}
      </div>

      {/* Provider + SKU */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-zinc-100">{offer.provider}</div>
        <div className="text-[11px] text-zinc-500 font-mono truncate">{offer.sku_name}</div>
      </div>

      {/* Unit price */}
      <div className="text-right hidden sm:block">
        <div className="text-xs text-zinc-300 font-numeric">{formatUSD(offer.unit_price_usd, 4)}</div>
        <div className="text-[10px] text-zinc-500">/{offer.unit_name}</div>
      </div>

      {/* Monthly estimate */}
      <div className="text-right">
        <div className={cn(
          'text-sm font-bold font-numeric',
          isFirst ? 'text-indigo-200' : 'text-zinc-100'
        )}>
          {offer.monthly_estimate_usd !== null ? formatUSD(offer.monthly_estimate_usd) : '—'}
        </div>
        <div className="text-[10px] text-zinc-500">/ month</div>
      </div>

      {/* Badges */}
      <div className="flex flex-col gap-1 items-end">
        <ConfidenceBadge confidence={offer.confidence} />
        <CapacityBadge check={offer.capacity_check} />
      </div>

      {/* Replicas */}
      {offer.required_replicas !== null && (
        <div className="text-[11px] text-zinc-500 hidden md:block">
          {offer.required_replicas}× replica{offer.required_replicas !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}

// ─── Provider diagnostics ─────────────────────────────────────────────────────

function DiagnosticsPanel({ diagnostics }: { diagnostics: ProviderDiagnostic[] }) {
  const [open, setOpen] = useState(false)
  const excluded = diagnostics.filter((d) => d.status !== 'included')

  if (excluded.length === 0) return null

  return (
    <div className="border border-white/[0.06] rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.03] transition-colors"
      >
        <span>
          {excluded.length} provider{excluded.length !== 1 ? 's' : ''} excluded or not selected
        </span>
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>
      {open && (
        <div className="border-t border-white/[0.05] divide-y divide-white/[0.04] animate-enter-fast">
          {diagnostics.map((d) => (
            <div key={d.provider} className="flex items-center gap-3 px-4 py-2">
              <Badge
                variant={
                  d.status === 'included' ? 'emerald' :
                  d.status === 'not_selected' ? 'default' : 'amber'
                }
              >
                {d.status}
              </Badge>
              <span className="text-xs font-medium text-zinc-300 w-24">{d.provider}</span>
              <span className="text-[11px] text-zinc-500 flex-1">{d.reason}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Main export ──────────────────────────────────────────────────────────────

interface ResultsTableProps {
  mode: 'llm' | 'non-llm'
  plans?: RankedPlan[]
  offers?: RankedCatalogOffer[]
  diagnostics?: ProviderDiagnostic[]
  warnings?: string[]
  excludedCount?: number
}

export function ResultsTable({
  mode,
  plans = [],
  offers = [],
  diagnostics = [],
  warnings = [],
  excludedCount = 0,
}: ResultsTableProps) {
  if (mode === 'llm' && plans.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="text-zinc-500 text-sm mb-1">No feasible configurations found</div>
        <div className="text-zinc-600 text-xs leading-relaxed max-w-xs">
          Try adding more providers, selecting a smaller model size, or reducing your daily token volume.
        </div>
      </div>
    )
  }

  if (mode === 'non-llm' && offers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="text-zinc-500 text-sm mb-1">No offers found for this workload</div>
        <div className="text-zinc-600 text-xs leading-relaxed max-w-xs">
          Try removing provider filters, switching to &ldquo;All units&rdquo; (browse mode), or setting budget to 0.
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Warnings */}
      {warnings.map((w, i) => (
        <div key={i} className="flex gap-2 items-start rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2">
          <span className="text-amber-400 text-xs">⚠</span>
          <span className="text-xs text-amber-300">{w}</span>
        </div>
      ))}

      {/* Summary */}
      <div className="flex items-center gap-2 text-[11px] text-zinc-500">
        <span>
          {mode === 'llm' ? plans.length : offers.length} result{(mode === 'llm' ? plans.length : offers.length) !== 1 ? 's' : ''}
        </span>
        {excludedCount > 0 && (
          <span>· {excludedCount} excluded</span>
        )}
      </div>

      {/* Insights */}
      <Suspense
        fallback={
          <div className="rounded-lg border border-white/[0.06] bg-zinc-900/50 p-4 text-xs text-zinc-500">
            Loading insights…
          </div>
        }
      >
        <InsightsCharts mode={mode} plans={plans} offers={offers} />
      </Suspense>

      {/* Results */}
      {mode === 'llm'
        ? plans.map((plan, i) => (
            <LLMResultCard key={plan.offering_id} plan={plan} isFirst={i === 0} index={i} />
          ))
        : offers.map((offer, i) => (
            <NonLLMResultRow key={offer.sku_name} offer={offer} isFirst={i === 0} index={i} />
          ))}

      {/* Provider diagnostics */}
      {diagnostics.length > 0 && <DiagnosticsPanel diagnostics={diagnostics} />}
    </div>
  )
}
