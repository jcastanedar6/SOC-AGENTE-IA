import { NavLink } from "react-router-dom"
import { LayoutDashboard, AlertTriangle, Server, Activity, Zap } from "lucide-react"

const links = [
  { to: "/",         icon: LayoutDashboard, label: "Dashboard" },
  { to: "/incidents",icon: AlertTriangle,   label: "Incidentes" },
  { to: "/servers",  icon: Server,          label: "Servidores" },
  { to: "/events",   icon: Activity,        label: "Eventos" },
]

export function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 bg-soc-surface border-r border-soc-border flex flex-col">
      <div className="px-4 py-5 border-b border-soc-border">
        <div className="flex items-center gap-2">
          <Zap size={18} className="text-soc-green" />
          <span className="text-soc-green font-mono font-semibold text-sm tracking-widest uppercase">
            SOC Agent
          </span>
        </div>
        <p className="text-soc-text-dim text-xs mt-1">v1.0.0 — Anomaly Detection</p>
      </div>

      <nav className="flex-1 py-4 px-2 space-y-0.5">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded text-xs font-mono transition-all duration-150 ${
                isActive
                  ? "bg-soc-green/10 text-soc-green border border-soc-green/20"
                  : "text-soc-muted hover:text-soc-text hover:bg-white/5 border border-transparent"
              }`
            }
          >
            <Icon size={14} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-3 border-t border-soc-border">
        <div className="flex items-center gap-2">
          <span className="status-dot status-online animate-pulse" />
          <span className="text-soc-text-dim text-xs">Sistema activo</span>
        </div>
      </div>
    </aside>
  )
}
