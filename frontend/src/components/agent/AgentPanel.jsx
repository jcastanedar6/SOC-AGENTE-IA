import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../../api/client"
import { Play, Activity, AlertTriangle, CheckCircle, Clock, Zap, RefreshCw } from "lucide-react"

function StatusDot({ status }) {
  const colors = {
    running: "bg-green-400 animate-pulse",
    idle: "bg-green-500",
    error: "bg-red-500",
    unknown: "bg-gray-500",
  }
  return <span className={`inline-block w-1.5 h-1.5 rounded-full ${colors[status] || colors.unknown} mr-1.5`} />
}

function StatItem({ label, value, icon: Icon }) {
  return (
    <div className="flex items-center gap-2 text-[11px] font-mono">
      <Icon size={12} className="text-soc-muted flex-shrink-0" />
      <span className="text-soc-muted">{label}:</span>
      <span className="text-soc-text font-medium">{value}</span>
    </div>
  )
}

export function AgentPanel() {
  const queryClient = useQueryClient()

  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["agent-status"],
    queryFn: api.agent.status,
    refetchInterval: 10_000,
  })

  const { data: llmHealth, isLoading: healthLoading } = useQuery({
    queryKey: ["llm-health"],
    queryFn: api.agent.llmHealth,
    refetchInterval: 30_000,
  })

  const runMutation = useMutation({
    mutationFn: api.agent.run,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["agent-status"] })
      queryClient.invalidateQueries({ queryKey: ["event-stats"] })
      queryClient.invalidateQueries({ queryKey: ["incidents"] })
    },
  })

  const isRunning = status?.is_running ?? false
  const llmOnline = llmHealth?.llm_online ?? false
  const agentStatus = isRunning ? "running" : status?.errors?.length ? "error" : "idle"

  return (
    <div className="soc-card space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-mono text-soc-muted uppercase tracking-widest flex items-center gap-2">
          <Zap size={13} className="text-soc-green" />
          Agente SOC
        </h2>
        <div className="flex items-center gap-3">
          <span className="flex items-center text-[11px] font-mono">
            <StatusDot status={llmOnline ? "idle" : "error"} />
            <span className={llmOnline ? "text-soc-text-dim" : "text-red-400"}>
              LLM {llmOnline ? "conectado" : "caído"}
            </span>
          </span>
          <span className="flex items-center text-[11px] font-mono">
            <StatusDot status={agentStatus} />
            <span className="text-soc-text-dim">
              {isRunning ? "Procesando..." : status?.errors?.length ? "Error" : "Inactivo"}
            </span>
          </span>
        </div>
      </div>

      {statusLoading ? (
        <div className="text-[11px] font-mono text-soc-text-dim py-2 text-center">Cargando estado...</div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <StatItem label="Procesados"   value={status?.events_processed ?? 0}    icon={Activity} />
          <StatItem label="Incidentes"   value={status?.incidents_created ?? 0}   icon={AlertTriangle} />
          <StatItem label="Notificaciones" value={status?.notifications_sent ?? 0} icon={CheckCircle} />
          <StatItem label="Último ciclo" value={
            status?.last_run
              ? new Date(status.last_run).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" })
              : "—"
          } icon={Clock} />
        </div>
      )}

      {/* Reacent errors */}
      {status?.errors?.length > 0 && (
        <div className="bg-red-900/20 border border-red-800/30 rounded px-2 py-1.5 space-y-0.5">
          <p className="text-[10px] font-mono text-red-400 uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle size={10} /> Errores recientes
          </p>
          {status.errors.slice(-2).map((err, i) => (
            <p key={i} className="text-[10px] font-mono text-red-300 truncate">{err}</p>
          ))}
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          onClick={() => runMutation.mutate()}
          disabled={isRunning || runMutation.isPending}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] font-mono font-medium transition-all duration-150
            bg-soc-green/10 text-soc-green border border-soc-green/20
            hover:bg-soc-green/20 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {runMutation.isPending ? (
            <RefreshCw size={12} className="animate-spin" />
          ) : (
            <Play size={12} />
          )}
          {runMutation.isPending ? "Ejecutando..." : "Run Cycle"}
        </button>

        <button
          onClick={() => queryClient.invalidateQueries({ queryKey: ["agent-status"] })}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] font-mono
            text-soc-muted border border-soc-border hover:text-soc-text hover:border-soc-muted transition-all duration-150"
        >
          <RefreshCw size={12} />
          Recargar
        </button>
      </div>

      {runMutation.data && (
        <div className="bg-soc-green/10 border border-soc-green/20 rounded px-2 py-1.5 text-[10px] font-mono text-soc-green space-y-0.5">
          <p>Ciclo completado: {runMutation.data.events_analyzed} eventos, {runMutation.data.anomalies_found} anomalías, {runMutation.data.incidents_created} incidentes</p>
        </div>
      )}

      {runMutation.isError && (
        <div className="bg-red-900/20 border border-red-800/30 rounded px-2 py-1.5 text-[10px] font-mono text-red-400">
          Error: {runMutation.error?.message || "Error al ejecutar el ciclo"}
        </div>
      )}
    </div>
  )
}
