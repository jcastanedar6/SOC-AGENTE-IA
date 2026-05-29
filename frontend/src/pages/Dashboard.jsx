import { useQuery } from "@tanstack/react-query"
import { api } from "../api/client"
import { StatCard } from "../components/dashboard/StatCard"
import { ServerCard } from "../components/servers/ServerCard"
import { SeverityBadge } from "../components/incidents/SeverityBadge"
import { formatDistanceToNow } from "../components/utils/time"
import { AgentPanel } from "../components/agent/AgentPanel"
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts"
import { AlertTriangle, Server, Activity, Shield } from "lucide-react"

function EventsChart({ stats }) {
  if (!stats?.by_severity) return null
  const data = Object.entries(stats.by_severity).map(([k, v]) => ({ name: k, value: v }))
  return (
    <ResponsiveContainer width="100%" height={120}>
      <AreaChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
        <XAxis dataKey="name" tick={{ fill: "#6e7681", fontSize: 10, fontFamily: "JetBrains Mono" }} />
        <YAxis tick={{ fill: "#6e7681", fontSize: 10, fontFamily: "JetBrains Mono" }} />
        <Tooltip
          contentStyle={{ background: "#161b22", border: "1px solid #21262d", borderRadius: 6, fontFamily: "JetBrains Mono", fontSize: 11 }}
          labelStyle={{ color: "#c9d1d9" }}
          itemStyle={{ color: "#00ff41" }}
        />
        <Area type="monotone" dataKey="value" stroke="#00ff41" fill="rgba(0,255,65,0.08)" strokeWidth={1.5} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export function Dashboard() {
  const { data: stats }     = useQuery({ queryKey: ["event-stats"],  queryFn: api.events.stats,     refetchInterval: 15_000 })
  const { data: incidents } = useQuery({ queryKey: ["incidents"],    queryFn: () => api.incidents.list({ limit: 5, status: "open" }), refetchInterval: 15_000 })
  const { data: servers }   = useQuery({ queryKey: ["servers"],      queryFn: api.servers.list,     refetchInterval: 15_000 })

  const online  = servers?.filter(s => s.status === "online").length ?? 0
  const offline = servers?.filter(s => s.status === "offline").length ?? 0
  const critical = incidents?.filter(i => i.severity === "critical").length ?? 0

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div>
        <h1 className="text-lg font-mono font-semibold text-soc-text tracking-wider">
          <span className="text-soc-green">&gt;</span> DASHBOARD
        </h1>
        <p className="text-xs font-mono text-soc-muted mt-0.5">Vista general del sistema SOC</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Eventos"  value={stats?.total ?? 0}    sub={`${stats?.unprocessed ?? 0} sin procesar`} color="blue"  icon={Activity} />
        <StatCard label="Incidentes"     value={incidents?.length ?? 0} sub={`${critical} críticos`}                   color="red"   icon={AlertTriangle} />
        <StatCard label="Servidores"     value={online}               sub={`${offline} offline`}                       color="green" icon={Server} />
        <StatCard label="Sin procesar"   value={stats?.unprocessed ?? 0} sub="eventos en cola"                         color="amber" icon={Shield} />
      </div>

      <AgentPanel />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="soc-card space-y-3">
          <h2 className="text-xs font-mono text-soc-muted uppercase tracking-widest">Eventos por severidad</h2>
          <EventsChart stats={stats} />
        </div>

        <div className="lg:col-span-2 soc-card space-y-3">
          <h2 className="text-xs font-mono text-soc-muted uppercase tracking-widest">Incidentes recientes</h2>
          {!incidents?.length ? (
            <p className="text-xs font-mono text-soc-text-dim py-4 text-center">Sin incidentes activos</p>
          ) : (
            <div className="space-y-2">
              {incidents.map(inc => (
                <div key={inc.id} className="flex items-start justify-between py-2 border-b border-soc-border last:border-0">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-mono text-soc-text truncate">{inc.title}</p>
                    <p className="text-xs font-mono text-soc-text-dim mt-0.5">
                      {inc.attack_type?.replace(/_/g, " ") ?? "—"} · {formatDistanceToNow(inc.created_at)}
                    </p>
                  </div>
                  <SeverityBadge severity={inc.severity} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div>
        <h2 className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-3">Servidores monitoreados</h2>
        {!servers?.length ? (
          <p className="text-xs font-mono text-soc-text-dim py-4 text-center">No hay servidores registrados</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {servers.map(s => <ServerCard key={s.id} server={s} />)}
          </div>
        )}
      </div>
    </div>
  )
}
