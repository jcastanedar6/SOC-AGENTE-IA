import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../../api/client"
import { Play, Cpu, Wifi, WifiOff } from "lucide-react"

export function Header() {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  const { data: agentStatus } = useQuery({
    queryKey: ["agent-status"],
    queryFn: api.agent.status,
    refetchInterval: 10_000,
  })

  const { data: llmHealth } = useQuery({
    queryKey: ["llm-health"],
    queryFn: api.agent.llmHealth,
    refetchInterval: 30_000,
  })

  const { mutate: runAgent, isPending } = (() => {
    const [pending, setPending] = useState(false)
    const mutate = async () => {
      if (pending) return
      setPending(true)
      try { await api.agent.run() } finally { setPending(false) }
    }
    return { mutate, isPending: pending }
  })()

  return (
    <header className="h-12 bg-soc-surface border-b border-soc-border flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <span className="text-soc-text-dim text-xs font-mono">
          {now.toISOString().replace("T", " ").slice(0, 19)} UTC
        </span>
        {agentStatus && (
          <div className="flex items-center gap-1.5">
            <Cpu size={12} className="text-soc-muted" />
            <span className="text-xs font-mono text-soc-muted">
              {agentStatus.events_processed} eventos / {agentStatus.incidents_created} incidentes
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          {llmHealth?.llm_online ? (
            <Wifi size={12} className="text-soc-green" />
          ) : (
            <WifiOff size={12} className="text-soc-red" />
          )}
          <span className={`text-xs font-mono ${llmHealth?.llm_online ? "text-soc-green" : "text-soc-red"}`}>
            {llmHealth?.llm_online ? "LLM online" : "LLM offline"}
          </span>
        </div>

        <button
          onClick={runAgent}
          disabled={isPending || agentStatus?.is_running}
          className="soc-btn-primary flex items-center gap-1.5"
        >
          <Play size={11} />
          {isPending || agentStatus?.is_running ? "Analizando..." : "Analizar"}
        </button>
      </div>
    </header>
  )
}
