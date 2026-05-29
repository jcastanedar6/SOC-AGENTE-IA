import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "../api/client"
import { IncidentRow } from "../components/incidents/IncidentRow"
import { SeverityBadge } from "../components/incidents/SeverityBadge"
import { formatDistanceToNow } from "../components/utils/time"
import { X, Shield, CheckCircle, Clock } from "lucide-react"

function IncidentDetail({ incident, onClose, onUpdate }) {
  const [saving, setSaving] = useState(false)

  const resolve = async () => {
    setSaving(true)
    try { await api.incidents.update(incident.id, { status: "resolved" }); onUpdate() }
    finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-soc-card border border-soc-border rounded-lg w-full max-w-2xl max-h-[85vh] overflow-y-auto">
        <div className="sticky top-0 bg-soc-card border-b border-soc-border px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield size={16} className="text-soc-red" />
            <span className="text-sm font-mono text-soc-text font-medium">Incidente #{incident.id}</span>
            <SeverityBadge severity={incident.severity} />
          </div>
          <button onClick={onClose} className="soc-btn-ghost p-1"><X size={14} /></button>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-1">Título</p>
            <p className="text-sm font-mono text-soc-text">{incident.title}</p>
          </div>

          {incident.description && (
            <div>
              <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-1">Descripción</p>
              <p className="text-xs font-mono text-soc-text leading-relaxed">{incident.description}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-1">Tipo de ataque</p>
              <p className="text-xs font-mono text-soc-amber">{incident.attack_type?.replace(/_/g, " ") ?? "—"}</p>
            </div>
            <div>
              <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-1">Estado</p>
              <p className={`text-xs font-mono ${incident.status === "resolved" ? "text-soc-green" : incident.status === "investigating" ? "text-soc-amber" : "text-soc-red"}`}>
                {incident.status}
              </p>
            </div>
          </div>

          {incident.source_ips?.length > 0 && (
            <div>
              <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-2">IPs origen</p>
              <div className="flex flex-wrap gap-2">
                {incident.source_ips.map(ip => (
                  <span key={ip} className="text-xs font-mono bg-soc-red/10 text-soc-red border border-soc-red/20 px-2 py-1 rounded">
                    {ip}
                  </span>
                ))}
              </div>
            </div>
          )}

          {incident.recommendation && (
            <div>
              <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-2">Recomendación</p>
              <div className="bg-soc-green/5 border border-soc-green/20 rounded p-3">
                <p className="text-xs font-mono text-soc-text leading-relaxed">{incident.recommendation}</p>
              </div>
            </div>
          )}

          {incident.llm_analysis && (
            <div>
              <p className="text-xs font-mono text-soc-muted uppercase tracking-widest mb-2">Análisis LLM</p>
              <div className="bg-soc-blue/5 border border-soc-blue/20 rounded p-3">
                <p className="text-xs font-mono text-soc-text leading-relaxed">{incident.llm_analysis}</p>
              </div>
            </div>
          )}

          <div className="flex items-center gap-2 text-xs font-mono text-soc-text-dim">
            <Clock size={12} />
            <span>Detectado {formatDistanceToNow(incident.created_at)}</span>
          </div>

          {incident.status !== "resolved" && (
            <div className="flex gap-2 pt-2 border-t border-soc-border">
              <button
                onClick={() => api.incidents.update(incident.id, { status: "investigating" }).then(onUpdate)}
                className="soc-btn-ghost flex items-center gap-1.5"
              >
                <Clock size={12} /> Investigando
              </button>
              <button onClick={resolve} disabled={saving} className="soc-btn-primary flex items-center gap-1.5">
                <CheckCircle size={12} /> {saving ? "Guardando..." : "Resolver"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function Incidents() {
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState("open")
  const qc = useQueryClient()

  const { data: incidents, isLoading } = useQuery({
    queryKey: ["incidents", filter],
    queryFn: () => api.incidents.list(filter ? { status: filter } : {}),
    refetchInterval: 15_000,
  })

  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-mono font-semibold text-soc-text">
            <span className="text-soc-red">&gt;</span> INCIDENTES
          </h1>
          <p className="text-xs font-mono text-soc-muted mt-0.5">{incidents?.length ?? 0} resultado(s)</p>
        </div>
        <div className="flex gap-2">
          {["open", "investigating", "resolved", ""].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`soc-btn ${filter === s ? "soc-btn-primary" : "soc-btn-ghost"}`}
            >
              {s || "todos"}
            </button>
          ))}
        </div>
      </div>

      <div className="soc-card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-soc-border">
              {["#", "Título", "Severidad", "Estado", "Tipo", "Detectado"].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-mono text-soc-muted uppercase tracking-widest">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-xs font-mono text-soc-muted">Cargando...</td></tr>
            ) : !incidents?.length ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-xs font-mono text-soc-muted">Sin incidentes</td></tr>
            ) : (
              incidents.map(inc => (
                <IncidentRow key={inc.id} incident={inc} onSelect={setSelected} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {selected && (
        <IncidentDetail
          incident={selected}
          onClose={() => setSelected(null)}
          onUpdate={() => { qc.invalidateQueries({ queryKey: ["incidents"] }); setSelected(null) }}
        />
      )}
    </div>
  )
}
