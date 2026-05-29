import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "../api/client"
import { SeverityBadge } from "../components/incidents/SeverityBadge"
import { formatDistanceToNow } from "../components/utils/time"
import { Plus, X } from "lucide-react"

const EVENT_TYPES = ["auth_failed","service_down","port_scan","anomaly","sql_injection","xss","path_traversal","command_injection"]
const SEVERITIES  = ["low","medium","high","critical"]

function InjectEventModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ event_type: EVENT_TYPES[0], source_ip: "", target_server: "", severity: "low" })
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try { await api.events.create(form); onAdd() } finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-soc-card border border-soc-border rounded-lg w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-soc-border">
          <span className="text-sm font-mono text-soc-text">Inyectar evento simulado</span>
          <button onClick={onClose} className="soc-btn-ghost p-1"><X size={14} /></button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          <div>
            <label className="text-xs font-mono text-soc-muted uppercase tracking-widest block mb-1">Tipo</label>
            <select
              value={form.event_type}
              onChange={e => setForm(p => ({ ...p, event_type: e.target.value }))}
              className="w-full bg-soc-surface border border-soc-border rounded px-3 py-2 text-xs font-mono text-soc-text focus:outline-none focus:border-soc-green/50 transition-all"
            >
              {EVENT_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-mono text-soc-muted uppercase tracking-widest block mb-1">Severidad</label>
            <select
              value={form.severity}
              onChange={e => setForm(p => ({ ...p, severity: e.target.value }))}
              className="w-full bg-soc-surface border border-soc-border rounded px-3 py-2 text-xs font-mono text-soc-text focus:outline-none focus:border-soc-green/50 transition-all"
            >
              {SEVERITIES.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
          {["source_ip", "target_server"].map(field => (
            <div key={field}>
              <label className="text-xs font-mono text-soc-muted uppercase tracking-widest block mb-1">{field.replace("_", " ")}</label>
              <input
                value={form[field]}
                onChange={e => setForm(p => ({ ...p, [field]: e.target.value }))}
                placeholder={field === "source_ip" ? "192.168.1.100" : "srv-web-01"}
                className="w-full bg-soc-surface border border-soc-border rounded px-3 py-2 text-xs font-mono text-soc-text focus:outline-none focus:border-soc-green/50 transition-all"
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="soc-btn-ghost flex-1">Cancelar</button>
            <button type="submit" disabled={saving} className="soc-btn-primary flex-1">
              {saving ? "Inyectando..." : "Inyectar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export function Events() {
  const [showInject, setShowInject] = useState(false)
  const [severity, setSeverity] = useState("")
  const qc = useQueryClient()

  const { data: events, isLoading } = useQuery({
    queryKey: ["events", severity],
    queryFn: () => api.events.list(severity ? { severity, limit: 200 } : { limit: 200 }),
    refetchInterval: 8_000,
  })

  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-mono font-semibold text-soc-text">
            <span className="text-soc-amber">&gt;</span> EVENTOS
          </h1>
          <p className="text-xs font-mono text-soc-muted mt-0.5">{events?.length ?? 0} evento(s)</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1">
            {["", ...SEVERITIES].map(s => (
              <button key={s} onClick={() => setSeverity(s)} className={`soc-btn ${severity === s ? "soc-btn-primary" : "soc-btn-ghost"}`}>
                {s || "todos"}
              </button>
            ))}
          </div>
          <button onClick={() => setShowInject(true)} className="soc-btn-primary flex items-center gap-1.5">
            <Plus size={12} /> Simular
          </button>
        </div>
      </div>

      <div className="soc-card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-soc-border">
              {["#", "Tipo", "Severidad", "IP Origen", "Servidor", "Estado", "Detectado"].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-mono text-soc-muted uppercase tracking-widest">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-xs font-mono text-soc-muted">Cargando...</td></tr>
            ) : !events?.length ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-xs font-mono text-soc-muted">Sin eventos</td></tr>
            ) : events.map(ev => (
              <tr key={ev.id} className="border-b border-soc-border hover:bg-white/5 transition-colors">
                <td className="px-4 py-2.5 text-xs font-mono text-soc-text-dim">#{ev.id}</td>
                <td className="px-4 py-2.5 text-xs font-mono text-soc-amber">{ev.event_type}</td>
                <td className="px-4 py-2.5"><SeverityBadge severity={ev.severity} /></td>
                <td className="px-4 py-2.5 text-xs font-mono text-soc-text">{ev.source_ip ?? "—"}</td>
                <td className="px-4 py-2.5 text-xs font-mono text-soc-text">{ev.target_server ?? "—"}</td>
                <td className="px-4 py-2.5 text-xs font-mono">
                  <span className={ev.processed ? "text-soc-green" : "text-soc-muted"}>
                    {ev.processed ? "procesado" : "pendiente"}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-xs font-mono text-soc-text-dim">{formatDistanceToNow(ev.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showInject && (
        <InjectEventModal
          onClose={() => setShowInject(false)}
          onAdd={() => { qc.invalidateQueries({ queryKey: ["events"] }); setShowInject(false) }}
        />
      )}
    </div>
  )
}
