import {
  Brain, Mic, Volume2, Layers, Eye, ImageIcon,
  Film, Shield,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { WORKLOAD_TYPES, type WorkloadTypeId } from '@/lib/constants'

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  Brain, Mic, Volume2, Layers, Eye, ImageIcon, Film, Shield,
}

// Base style: translucent dark + colored border/text
const COLOR_MAP: Record<string, string> = {
  indigo: 'border-indigo-800/50 bg-indigo-950/25 text-indigo-400 hover:border-indigo-600/70 hover:bg-indigo-950/45',
  emerald: 'border-emerald-800/50 bg-emerald-950/25 text-emerald-400 hover:border-emerald-600/70 hover:bg-emerald-950/45',
  sky: 'border-sky-800/50 bg-sky-950/25 text-sky-400 hover:border-sky-600/70 hover:bg-sky-950/45',
  violet: 'border-violet-800/50 bg-violet-950/25 text-violet-400 hover:border-violet-600/70 hover:bg-violet-950/45',
  amber: 'border-amber-800/50 bg-amber-950/25 text-amber-400 hover:border-amber-600/70 hover:bg-amber-950/45',
  rose: 'border-rose-800/50 bg-rose-950/25 text-rose-400 hover:border-rose-600/70 hover:bg-rose-950/45',
  orange: 'border-orange-800/50 bg-orange-950/25 text-orange-400 hover:border-orange-600/70 hover:bg-orange-950/45',
  teal: 'border-teal-800/50 bg-teal-950/25 text-teal-400 hover:border-teal-600/70 hover:bg-teal-950/45',
}

// Selected: brighter border + glow ring
const SELECTED_MAP: Record<string, string> = {
  indigo: 'border-indigo-500/60 bg-indigo-950/50 text-indigo-300 ring-1 ring-indigo-500/30 shadow-[0_0_18px_rgba(99,102,241,0.18)]',
  emerald: 'border-emerald-500/60 bg-emerald-950/50 text-emerald-300 ring-1 ring-emerald-500/30 shadow-[0_0_18px_rgba(16,185,129,0.18)]',
  sky: 'border-sky-500/60 bg-sky-950/50 text-sky-300 ring-1 ring-sky-500/30 shadow-[0_0_18px_rgba(14,165,233,0.18)]',
  violet: 'border-violet-500/60 bg-violet-950/50 text-violet-300 ring-1 ring-violet-500/30 shadow-[0_0_18px_rgba(139,92,246,0.18)]',
  amber: 'border-amber-500/60 bg-amber-950/50 text-amber-300 ring-1 ring-amber-500/30 shadow-[0_0_18px_rgba(245,158,11,0.18)]',
  rose: 'border-rose-500/60 bg-rose-950/50 text-rose-300 ring-1 ring-rose-500/30 shadow-[0_0_18px_rgba(244,63,94,0.18)]',
  orange: 'border-orange-500/60 bg-orange-950/50 text-orange-300 ring-1 ring-orange-500/30 shadow-[0_0_18px_rgba(249,115,22,0.18)]',
  teal: 'border-teal-500/60 bg-teal-950/50 text-teal-300 ring-1 ring-teal-500/30 shadow-[0_0_18px_rgba(20,184,166,0.18)]',
}

interface WorkloadSelectorProps {
  selected: WorkloadTypeId | null
  onSelect: (id: WorkloadTypeId) => void
}

export function WorkloadSelector({ selected, onSelect }: WorkloadSelectorProps) {
  return (
    <div className="space-y-4 animate-enter">
      <div>
        <h2 className="text-base font-semibold text-zinc-100">Select workload category</h2>
        <p className="text-xs text-zinc-500 mt-0.5">
          Choose the type of AI workload you want to cost-optimize
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
        {WORKLOAD_TYPES.map((w, i) => {
          const Icon = ICON_MAP[w.icon]
          const isSelected = selected === w.id
          return (
            <button
              key={w.id}
              onClick={() => onSelect(w.id)}
              style={{ animationDelay: `${i * 30}ms` }}
              className={cn(
                'group flex flex-col gap-2.5 rounded-lg border p-3.5 text-left cursor-pointer',
                'transition-all duration-200 ease-out',
                'hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:scale-[0.98]',
                'animate-enter',
                isSelected ? SELECTED_MAP[w.color] : COLOR_MAP[w.color]
              )}
            >
              {Icon && (
                <Icon
                  className={cn(
                    'h-5 w-5 transition-transform duration-200',
                    isSelected
                      ? 'scale-110'
                      : 'group-hover:scale-110 group-hover:rotate-[-4deg]'
                  )}
                />
              )}
              <div>
                <div className="text-xs font-semibold text-zinc-100 leading-tight">{w.label}</div>
                <div className="text-[10px] text-zinc-400 mt-0.5 leading-tight">{w.description}</div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
