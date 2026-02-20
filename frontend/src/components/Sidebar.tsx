import { NavLink } from 'react-router-dom'
import { BarChart3, BookOpen, Receipt, Github, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { AIAssistantPanel } from './AIAssistantPanel'
import { Separator } from './ui/separator'

const NAV_ITEMS = [
  { to: '/', label: 'Optimize Workload', icon: BarChart3, end: true },
  { to: '/catalog', label: 'Browse Catalog', icon: BookOpen },
  { to: '/invoice', label: 'Invoice Analyzer', icon: Receipt },
]

interface SidebarProps {
  className?: string
}

export function Sidebar({ className }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex flex-col h-full border-r',
        'bg-zinc-950/90 border-white/[0.06]',
        className
      )}
    >
      {/* Logo */}
      <div className="px-4 py-4 border-b border-white/[0.05]">
        <div className="flex items-center gap-2.5">
          <div className="relative w-7 h-7 flex-shrink-0">
            <div className="absolute inset-0 rounded-lg bg-indigo-600 shadow-glow-sm" />
            <div className="absolute inset-0 rounded-lg flex items-center justify-center">
              <span className="text-white text-[10px] font-bold tracking-tight">IA</span>
            </div>
          </div>
          <div>
            <div className="text-sm font-bold text-zinc-100 leading-none tracking-tight">
              InferenceAtlas
            </div>
            <div className="text-[10px] text-zinc-500 mt-0.5 font-mono">v0.1 · pre-release</div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-2 py-3 space-y-0.5">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 border',
                isActive
                  ? 'bg-indigo-600/12 text-indigo-300 border-indigo-500/25 shadow-glow-sm'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04] border-transparent'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  className={cn(
                    'h-4 w-4 flex-shrink-0 transition-colors',
                    isActive ? 'text-indigo-400' : 'text-zinc-500 group-hover:text-zinc-300'
                  )}
                />
                <span>{label}</span>
                {isActive && (
                  <span className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400 shadow-[0_0_6px_rgba(129,140,248,0.8)]" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <Separator className="bg-white/[0.05] h-px" />

      {/* AI Panel — takes remaining space */}
      <div className="flex-1 min-h-0 flex flex-col">
        <AIAssistantPanel />
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/[0.05] space-y-2">
        <a
          href="https://github.com/jayeshsuyal/inference-atlas"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors group"
        >
          <Github className="h-3.5 w-3.5 flex-shrink-0" />
          <span>Star on GitHub</span>
          <ChevronRight className="h-3 w-3 ml-auto opacity-40 group-hover:opacity-70 transition-opacity" />
        </a>
        <details className="group/details">
          <summary className="flex items-center gap-2 text-[11px] text-zinc-500 hover:text-zinc-300 cursor-pointer list-none transition-colors select-none">
            <span>ℹ︎ About & Roadmap</span>
            <ChevronRight className="h-3 w-3 ml-auto group-open/details:rotate-90 transition-transform duration-200" />
          </summary>
          <div className="mt-2 space-y-2 pl-1 animate-enter-fast">
            <p className="text-[10px] text-zinc-500 leading-relaxed">
              Early build — expect rough edges and breaking changes before v1.
            </p>
            <div className="text-[10px] text-zinc-500 space-y-0.5">
              <div className="text-zinc-400 font-medium mb-1">v1 Roadmap</div>
              {[
                'Fine-tuning cost estimation',
                'GPU cluster planning',
                'Real-time price sync API',
                'Shareable result links',
                'REST API + widget',
              ].map((item) => (
                <div key={item} className="flex items-start gap-1.5">
                  <span className="text-zinc-600 mt-0.5">▸</span>
                  <span>{item}</span>
                </div>
              ))}
            </div>
            <a
              href="mailto:jksuyal@gmail.com"
              className="block text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Ideas for v1? → jksuyal@gmail.com
            </a>
          </div>
        </details>
      </div>
    </aside>
  )
}
