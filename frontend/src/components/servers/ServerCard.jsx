import { Server } from "lucide-react"

function Bar({ value, color }) {
  const colors = { green: "bg-soc-green", amber: "bg-soc-amber", red: "bg-soc-red" }
  const c = value > 85 ? "red" : value > 65 ? "amber" : "green"
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-soc-border rounded-full overflow-hidden">
        <div className={`h-full ${colors[c]} transition-all`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
      <span className="text-xs font-mono text-soc-muted w-10 text-right">{value.toFixed(0)}%</span>
    </div>
  )
}

const STATUS = {
  online:  { dot: "status-online",  label: "ONLINE",  pulse: true  },
  offline: { dot: "status-offline", label: "OFFLINE", pulse: false },
  warning: { dot: "status-warning", label: "WARNING", pulse: true  },
}

export function ServerCard({ server }) {
  const st = STATUS[server.status] ?? STATUS.online

  return (
    <div className="soc-card space-y-3 hover:border-soc-green/20 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Server size={14} className="text-soc-muted flex-shrink-0" />
          <div>
            <p className="text-sm font-mono text-soc-text font-medium">{server.hostname}</p>
            <p className="text-xs font-mono text-soc-text-dim">{server.ip_address}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`status-dot ${st.dot} ${st.pulse ? "animate-pulse" : ""}`} />
          <span className={`text-xs font-mono ${server.status === "offline" ? "text-soc-red" : server.status === "warning" ? "text-soc-amber" : "text-soc-green"}`}>
            {st.label}
          </span>
        </div>
      </div>

      {server.role && (
        <span className="text-xs font-mono text-soc-muted bg-soc-border/50 px-2 py-0.5 rounded">
          {server.role}
        </span>
      )}

      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-xs font-mono text-soc-muted mb-1">
          <span>CPU</span><span>MEM</span><span>DISK</span>
        </div>
        <Bar value={server.cpu_usage}    />
        <Bar value={server.memory_usage} />
        <Bar value={server.disk_usage}   />
      </div>
    </div>
  )
}
