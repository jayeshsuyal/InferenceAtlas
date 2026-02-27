import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { ScalingPlanResponse } from '@/services/types'

// ─── Badge helpers ────────────────────────────────────────────────────────────

const RISK_CONFIG: Record<
  ScalingPlanResponse['risk_band'],
  { label: string; color: string; bg: string; border: string }
> = {
  low:     { label: 'Low risk',    color: '#4ade80', bg: 'rgba(74,222,128,0.10)',  border: 'rgba(74,222,128,0.28)'  },
  medium:  { label: 'Medium risk', color: '#fbbf24', bg: 'rgba(251,191,36,0.10)',  border: 'rgba(251,191,36,0.28)'  },
  high:    { label: 'High risk',   color: '#f87171', bg: 'rgba(248,113,113,0.10)', border: 'rgba(248,113,113,0.28)' },
  unknown: { label: 'Risk ?',      color: 'var(--text-disabled)', bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.10)' },
}

const CAPACITY_CONFIG: Record<
  ScalingPlanResponse['capacity_check'],
  { label: string; color: string; bg: string; border: string }
> = {
  ok:           { label: 'Capacity OK',   color: '#4ade80', bg: 'rgba(74,222,128,0.10)',  border: 'rgba(74,222,128,0.28)'  },
  insufficient: { label: 'Insufficient',  color: '#f87171', bg: 'rgba(248,113,113,0.10)', border: 'rgba(248,113,113,0.28)' },
  unknown:      { label: 'Capacity ?',    color: 'var(--text-disabled)', bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.10)' },
}

function Badge({ color, bg, border, label }: { color: string; bg: string; border: string; label: string }) {
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border tracking-wide"
      style={{ color, background: bg, borderColor: border }}
    >
      {label}
    </span>
  )
}

// ─── Stat cell ────────────────────────────────────────────────────────────────

function StatCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border p-2" style={{ borderColor: 'var(--border-subtle)' }}>
      <div className="micro-label mb-0.5">{label}</div>
      <div
        className="text-xs font-medium capitalize truncate"
        style={{ color: 'var(--text-secondary)' }}
      >
        {value}
      </div>
    </div>
  )
}

// ─── Main card ────────────────────────────────────────────────────────────────

interface ScalingSummaryCardProps {
  data: ScalingPlanResponse
}

export function ScalingSummaryCard({ data }: ScalingSummaryCardProps) {
  const [open, setOpen] = useState(false)

  const riskCfg     = RISK_CONFIG[data.risk_band]
  const capacityCfg = CAPACITY_CONFIG[data.capacity_check]

  const utilizationStr =
    data.projected_utilization !== null
      ? `${(data.projected_utilization * 100).toFixed(0)}%${
          data.utilization_target !== null
            ? ` / ${(data.utilization_target * 100).toFixed(0)}% target`
            : ''
        }`
      : null

  return (
    <div
      className="rounded-lg border p-4 space-y-3"
      style={{ borderColor: 'var(--border-default)', background: 'var(--bg-elevated)' }}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="eyebrow mb-0.5">Scaling Planner</div>
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            Deployment Recommendation
          </h3>
        </div>
        <div className="flex items-center gap-1.5 flex-wrap justify-end shrink-0">
          <Badge {...riskCfg} />
          <Badge {...capacityCfg} />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <StatCell
          label="Deployment"
          value={data.deployment_mode.replace(/_/g, ' ')}
        />
        <StatCell
          label="Est. GPUs"
          value={data.estimated_gpu_count > 0 ? String(data.estimated_gpu_count) : 'n/a'}
        />
        {data.suggested_gpu_type ? (
          <StatCell label="GPU Type" value={data.suggested_gpu_type} />
        ) : (
          <StatCell label="GPU Type" value="—" />
        )}
        {utilizationStr ? (
          <StatCell label="Utilization" value={utilizationStr} />
        ) : (
          <StatCell label="Utilization" value="—" />
        )}
      </div>

      {/* Rationale */}
      <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>
        {data.rationale}
      </p>

      {/* Assumptions — collapsible */}
      {data.assumptions.length > 0 && (
        <div>
          <button
            type="button"
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
            className="flex items-center gap-1 text-[11px] transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--brand)]"
            style={{ color: open ? 'var(--text-secondary)' : 'var(--text-disabled)' }}
          >
            {open
              ? <ChevronUp className="h-3 w-3" />
              : <ChevronDown className="h-3 w-3" />
            }
            {open ? 'Hide' : 'Show'} assumptions ({data.assumptions.length})
          </button>

          {open && (
            <ul className="mt-1.5 space-y-0.5" role="list">
              {data.assumptions.map((a, i) => (
                <li key={i} className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>
                  · {a}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
