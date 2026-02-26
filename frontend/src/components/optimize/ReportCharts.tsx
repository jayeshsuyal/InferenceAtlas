import { useState, useMemo } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { BarChart2, ChevronDown, ChevronUp } from 'lucide-react'
import { formatUSD } from '@/lib/utils'
import type { ChartUnit, ReportChart } from '@/services/types'

// ─── Constants ────────────────────────────────────────────────────────────────

const SERIES_COLORS = ['#6366f1', '#14b8a6', '#f59e0b', '#ef4444', '#a855f7', '#22c55e']

const TOOLTIP_STYLE: React.CSSProperties = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-default)',
  borderRadius: '8px',
  color: 'var(--text-primary)',
  fontSize: 11,
}

const TICK_STYLE: React.SVGProps<SVGTextElement> = {
  fill: 'var(--text-tertiary)',
  fontSize: 11,
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatChartValue(value: number, unit: ChartUnit): string {
  switch (unit) {
    case 'usd':
      return formatUSD(value)
    case '%':
      return `${value.toFixed(1)}%`
    case 'count':
      return String(Math.round(value))
    case 'risk_score':
      return value.toFixed(3)
  }
}

type SortKey = 'rank' | 'cost' | 'risk'

function normalizeUnit(unit: string | null | undefined): ChartUnit {
  if (unit === 'usd' || unit === '%' || unit === 'count' || unit === 'risk_score') return unit
  return 'count'
}

function seriesLabel(series: ReportChart['series'][number]): string {
  return series.label ?? series.name ?? series.id
}

function seriesPoints(series: ReportChart['series'][number]) {
  return series.points ?? series.data ?? []
}

function pointX(point: Record<string, unknown>, fallback: number): string | number {
  const candidate =
    point.x ??
    point.rank ??
    point.step ??
    point.confidence ??
    point.provider_name ??
    point.provider ??
    point.sku_name ??
    point.step_index
  if (typeof candidate === 'string' || typeof candidate === 'number') return candidate
  return fallback
}

function pointY(point: Record<string, unknown>): number {
  const candidate = point.y ?? point.value
  const n = Number(candidate)
  return Number.isFinite(n) ? n : 0
}

/** Pivot multi-series chart data into recharts row format `{ _x, series_id, ... }`. */
function pivotData(
  chart: ReportChart,
  hidden: Set<string>,
  sortKey: SortKey,
): Record<string, string | number>[] {
  const active = chart.series.filter((s) => !hidden.has(s.id))
  if (active.length === 0) return []

  // Collect all x values in original order from all series
  const xOrder: Array<string | number> = []
  const seen = new Set<string>()
  for (const s of chart.series) {
    const pts = seriesPoints(s) as Record<string, unknown>[]
    for (let idx = 0; idx < pts.length; idx++) {
      const pt = pts[idx]
      const x = pointX(pt, idx)
      const key = String(x)
      if (!seen.has(key)) {
        xOrder.push(x)
        seen.add(key)
      }
    }
  }

  const rows: Record<string, string | number>[] = xOrder.map((x) => {
    const row: Record<string, string | number> = { _x: String(x) }
    for (const s of active) {
      const pts = seriesPoints(s) as Record<string, unknown>[]
      const pt = pts.find((p, idx) => pointX(p, idx) === x)
      row[s.id] = pt ? pointY(pt) : 0
    }
    return row
  })

  if (sortKey === 'cost' && active[0]) {
    const id = active[0].id
    rows.sort((a, b) => Number(a[id]) - Number(b[id]))
  } else if (sortKey === 'risk') {
    const riskSeries = active.find((s) => s.id.includes('risk') || s.id.includes('total'))
    if (riskSeries) {
      const id = riskSeries.id
      rows.sort((a, b) => Number(a[id]) - Number(b[id]))
    }
  }
  // 'rank' → keep original backend order

  return rows
}

// ─── ChartCard ────────────────────────────────────────────────────────────────

interface ChartCardProps {
  chart: ReportChart
  hidden: Set<string>
  onToggle: (seriesId: string) => void
}

function ChartCard({ chart, hidden, onToggle }: ChartCardProps) {
  const [sortKey, setSortKey] = useState<SortKey>(chart.sort_key ?? 'rank')
  const data = useMemo(() => pivotData(chart, hidden, sortKey), [chart, hidden, sortKey])

  const active = chart.series.filter((s) => !hidden.has(s.id))
  const primaryUnit = normalizeUnit(chart.series[0]?.unit)
  const isStepLine = chart.type === 'step_line'
  const hasSortControls =
    chart.id === 'cost_comparison' || chart.id === 'risk_comparison' || chart.sort_key !== undefined

  function renderInnerChart() {
    if (data.length === 0) {
      return (
        <div className="h-48 flex items-center justify-center">
          <span className="text-[11px]" style={{ color: 'var(--text-disabled)' }}>
            No data to display
          </span>
        </div>
      )
    }

    const xAxisAngled = data.length > 5
    const xAxis = (
      <XAxis
        dataKey="_x"
        tick={TICK_STYLE}
        tickLine={false}
        axisLine={{ stroke: 'rgba(255,255,255,0.08)' }}
        interval={0}
        angle={xAxisAngled ? -20 : 0}
        textAnchor={xAxisAngled ? 'end' : 'middle'}
        height={xAxisAngled ? 42 : 22}
      />
    )
    const yAxis = (
      <YAxis
        tick={TICK_STYLE}
        tickLine={false}
        axisLine={false}
        tickFormatter={(v: number) => formatChartValue(v, primaryUnit)}
        width={58}
      />
    )
    const tooltip = (
      <Tooltip
        contentStyle={TOOLTIP_STYLE}
        labelStyle={{ color: 'var(--text-secondary)', marginBottom: 4 }}
        formatter={(value: number, name: string) => {
          const s = chart.series.find((s) => s.id === name)
          return [formatChartValue(value, normalizeUnit(s?.unit)), s ? seriesLabel(s) : name]
        }}
      />
    )
    const grid = <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />

    if (chart.type === 'bar' || chart.type === 'stacked_bar') {
      const stacked = chart.type === 'stacked_bar'
      return (
        <ResponsiveContainer width="100%" height={224}>
          <BarChart data={data} margin={{ top: 4, right: 8, left: 4, bottom: 4 }}>
            {grid}
            {xAxis}
            {yAxis}
            {tooltip}
            {active.map((s, i) => (
              <Bar
                key={s.id}
                dataKey={s.id}
                name={s.id}
                stackId={stacked ? 'stack' : undefined}
                fill={s.color ?? SERIES_COLORS[i % SERIES_COLORS.length]}
                radius={stacked ? undefined : [3, 3, 0, 0]}
                maxBarSize={48}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )
    }

    // line / step_line
    return (
      <ResponsiveContainer width="100%" height={224}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 4, bottom: 4 }}>
          {grid}
          {xAxis}
          {yAxis}
          {tooltip}
          {active.map((s, i) => (
            <Line
              key={s.id}
              dataKey={s.id}
              name={s.id}
              type={isStepLine ? 'stepAfter' : 'monotone'}
              stroke={s.color ?? SERIES_COLORS[i % SERIES_COLORS.length]}
              strokeWidth={2}
              dot={isStepLine ? false : { r: 3 }}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return (
    <div
      className="rounded-lg border p-4 space-y-3"
      style={{ borderColor: 'var(--border-default)', background: 'var(--bg-elevated)' }}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
            {chart.title}
          </h3>
          {(chart.description || Boolean(chart.meta?.note)) && (
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
              {chart.description ?? String(chart.meta?.note)}
            </p>
          )}
        </div>

        {hasSortControls && (
          <div
            className="flex items-center gap-1 shrink-0"
            role="group"
            aria-label="Sort chart by"
          >
            {(['rank', 'cost', 'risk'] as SortKey[]).map((key) => (
              <button
                key={key}
                type="button"
                aria-pressed={sortKey === key}
                onClick={() => setSortKey(key)}
                className="rounded px-1.5 py-0.5 text-[10px] border transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--brand)]"
                style={
                  sortKey === key
                    ? {
                        borderColor: 'var(--brand-border)',
                        background: 'rgba(124,92,252,0.10)',
                        color: 'var(--brand-hover)',
                      }
                    : {
                        borderColor: 'rgba(255,255,255,0.07)',
                        background: 'transparent',
                        color: 'var(--text-disabled)',
                      }
                }
              >
                {key}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Chart */}
      {renderInnerChart()}

      {/* Step badges for step_line (e.g. fallback_trace) */}
      {isStepLine && data.length > 0 && (
        <div className="flex flex-wrap gap-1 pt-1">
          {data.map((row, i) => (
            <span
              key={i}
              className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] border"
              style={{
                borderColor: 'rgba(255,255,255,0.08)',
                color: 'var(--text-tertiary)',
                background: 'var(--bg-base)',
              }}
            >
              {i + 1}. {row['_x']}
            </span>
          ))}
        </div>
      )}

      {/* Series legend toggles (multi-series only) */}
      {chart.series.length > 1 && (
        <div
          className="flex flex-wrap gap-1.5 pt-2 border-t"
          style={{ borderColor: 'var(--border-subtle)' }}
        >
          {chart.series.map((s, i) => {
            const isHidden = hidden.has(s.id)
            const color = s.color ?? SERIES_COLORS[i % SERIES_COLORS.length]
            return (
              <button
                key={s.id}
                type="button"
                aria-pressed={!isHidden}
                onClick={() => onToggle(s.id)}
                className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10px] border transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--brand)]"
                style={{
                  borderColor: isHidden ? 'rgba(255,255,255,0.07)' : `${color}55`,
                  background: isHidden ? 'transparent' : `${color}18`,
                  color: isHidden ? 'var(--text-disabled)' : 'var(--text-secondary)',
                  opacity: isHidden ? 0.6 : 1,
                }}
              >
                <span
                  className="w-2 h-2 rounded-sm shrink-0"
                  style={{ background: isHidden ? 'rgba(255,255,255,0.12)' : color }}
                />
                {seriesLabel(s)}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyCharts() {
  return (
    <div
      className="rounded-lg border p-6 text-center space-y-2"
      style={{ borderColor: 'var(--border-default)', background: 'var(--bg-elevated)' }}
    >
      <BarChart2 className="h-6 w-6 mx-auto" style={{ color: 'var(--text-disabled)' }} />
      <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
        No chart data available for this report.
      </p>
    </div>
  )
}

// ─── Public component ─────────────────────────────────────────────────────────

interface ReportChartsProps {
  charts: ReportChart[]
}

export function ReportCharts({ charts }: ReportChartsProps) {
  const [hiddenSeries, setHiddenSeries] = useState<Record<string, Set<string>>>({})
  const [expanded, setExpanded] = useState(false)

  if (charts.length === 0) {
    return <EmptyCharts />
  }

  const visible = expanded ? charts : charts.slice(0, 2)
  const overflow = charts.length - 2

  function toggleSeries(chartId: string, seriesId: string) {
    setHiddenSeries((prev) => {
      const cur = new Set(prev[chartId] ?? [])
      if (cur.has(seriesId)) {
        cur.delete(seriesId)
      } else {
        cur.add(seriesId)
      }
      return { ...prev, [chartId]: cur }
    })
  }

  return (
    <div className="space-y-3">
      {visible.map((chart) => (
        <ChartCard
          key={chart.id}
          chart={chart}
          hidden={hiddenSeries[chart.id] ?? new Set<string>()}
          onToggle={(id) => toggleSeries(chart.id, id)}
        />
      ))}

      {overflow > 0 && (
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="w-full flex items-center justify-center gap-1.5 rounded-lg border py-2 text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand)]"
          style={{
            borderColor: 'rgba(255,255,255,0.07)',
            color: 'var(--text-tertiary)',
            background: 'transparent',
          }}
        >
          {expanded ? (
            <>
              <ChevronUp className="h-3.5 w-3.5" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="h-3.5 w-3.5" />
              {overflow} more insight{overflow !== 1 ? 's' : ''}
            </>
          )}
        </button>
      )}
    </div>
  )
}
