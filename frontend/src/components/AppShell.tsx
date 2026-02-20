import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { Button } from './ui/button'

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#09090b] bg-grid-pattern">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex lg:w-64 xl:w-72 flex-col h-full flex-shrink-0">
        <Sidebar className="h-full" />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden animate-fade-in">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 bottom-0 w-72 z-10 animate-enter">
            <Sidebar className="h-full" />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-white/[0.06] bg-zinc-950/90 backdrop-blur-sm">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
          <div className="flex items-center gap-2">
            <div className="relative w-5 h-5 flex-shrink-0">
              <div className="absolute inset-0 rounded bg-indigo-600 shadow-glow-sm" />
              <div className="absolute inset-0 rounded flex items-center justify-center">
                <span className="text-white text-[9px] font-bold">IA</span>
              </div>
            </div>
            <span className="text-sm font-bold text-zinc-100 tracking-tight">InferenceAtlas</span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
