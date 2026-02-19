import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { RankedCatalogOffer, RankedPlan } from '@/services/types'
import { formatUSD } from '@/lib/utils'

interface InsightsChartsProps {
  mode: 'llm' | 'non-llm'
  plans: RankedPlan[]
  offers: RankedCatalogOffer[]
}

const PROVIDER_COLORS = ['#6366f1', '#14b8a6', '#f59e0b', '#ef4444', '#a855f7', '#22c55e']

function ProviderCostChart({ mode, plans, offers }: InsightsChartsProps) {
  const source = mode === 'llm'
    ? plans.map((plan) => ({
        provider: plan.provider_name,
        monthly_cost: Number(plan.monthly_cost_usd.toFixed(2)),
      }))
    : offers
        .filter((offer) => offer.monthly_estimate_usd !== null)
        .map((offer) => ({
          provider: offer.provider,
          monthly_cost: Number((offer.monthly_estimate_usd ?? 0).toFixed(2)),
        }))

  const byProvider = new Map<string, number>()
  for (const row of source) {
    const current = byProvider.get(row.provider)
    if (current === undefined || row.monthly_cost < current) {
      byProvider.set(row.provider, row.monthly_cost)
    }
  }
  const data = Array.from(byProvider.entries())
    .map(([provider, monthly_cost]) => ({ provider, monthly_cost }))
    .sort((a, b) => a.monthly_cost - b.monthly_cost)
    .slice(0, 8)

  if (data.length === 0) {
    return null
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="text-sm font-semibold text-zinc-100">Provider Cost Comparison</h3>
      <p className="text-[11px] text-zinc-500 mt-0.5">
        Lowest monthly estimate per provider (top 8).
      </p>
      <div className="h-64 mt-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="provider" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
            <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
            <Tooltip
              formatter={(value: number) => formatUSD(value)}
              contentStyle={{ background: '#18181b', border: '1px solid #3f3f46' }}
              labelStyle={{ color: '#e4e4e7' }}
            />
            <Bar dataKey="monthly_cost" radius={[4, 4, 0, 0]}>
              {data.map((_, i) => (
                <Cell key={i} fill={PROVIDER_COLORS[i % PROVIDER_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function RiskCostScatter({ plans }: { plans: RankedPlan[] }) {
  if (plans.length === 0) {
    return null
  }
  const data = plans.map((plan) => ({
    provider: plan.provider_name,
    monthly_cost: Number(plan.monthly_cost_usd.toFixed(2)),
    risk: Number(plan.risk.total_risk.toFixed(4)),
  }))

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="text-sm font-semibold text-zinc-100">Risk vs Cost Frontier</h3>
      <p className="text-[11px] text-zinc-500 mt-0.5">
        Lower-left is ideal: lower risk and lower monthly cost.
      </p>
      <div className="h-64 mt-3">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis
              type="number"
              dataKey="monthly_cost"
              name="Monthly Cost"
              tick={{ fill: '#a1a1aa', fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="risk"
              name="Risk"
              domain={[0, 1]}
              tick={{ fill: '#a1a1aa', fontSize: 11 }}
            />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              formatter={(value: number, key) => (
                key === 'monthly_cost' ? formatUSD(value) : value.toFixed(3)
              )}
              contentStyle={{ background: '#18181b', border: '1px solid #3f3f46' }}
              labelStyle={{ color: '#e4e4e7' }}
            />
            <Legend />
            <Scatter name="Plans" data={data} fill="#6366f1" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function PriceChangeChart({ offers }: { offers: RankedCatalogOffer[] }) {
  const data = offers
    .filter((offer) => typeof offer.price_change_pct === 'number')
    .map((offer) => ({
      provider: offer.provider,
      change_pct: Number((offer.price_change_pct ?? 0).toFixed(2)),
    }))
    .slice(0, 10)

  if (data.length === 0) {
    return null
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="text-sm font-semibold text-zinc-100">Price Change Since Last Sync</h3>
      <p className="text-[11px] text-zinc-500 mt-0.5">
        Negative means cheaper, positive means more expensive.
      </p>
      <div className="h-64 mt-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
            <XAxis dataKey="provider" tick={{ fill: '#a1a1aa', fontSize: 11 }} />
            <YAxis tick={{ fill: '#a1a1aa', fontSize: 11 }} />
            <Tooltip
              formatter={(value: number) => `${value.toFixed(2)}%`}
              contentStyle={{ background: '#18181b', border: '1px solid #3f3f46' }}
              labelStyle={{ color: '#e4e4e7' }}
            />
            <Bar dataKey="change_pct" radius={[4, 4, 0, 0]}>
              {data.map((row, i) => (
                <Cell key={i} fill={row.change_pct <= 0 ? '#22c55e' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function InsightsCharts(props: InsightsChartsProps) {
  return (
    <div className="space-y-3">
      <ProviderCostChart {...props} />
      {props.mode === 'llm' ? <RiskCostScatter plans={props.plans} /> : null}
      {props.mode === 'non-llm' ? <PriceChangeChart offers={props.offers} /> : null}
    </div>
  )
}
