import { useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { api } from "../api/client"
import { ServerCard } from "../components/servers/ServerCard"
import { Plus, X } from "lucide-react"

function AddServerModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ hostname: "", ip_address: "", role: "", os: "" })
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try { await api.servers.create(form); onAdd() } finally { setSaving(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-soc-card border border-soc-border rounded-lg w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-soc-border">
          <span className="text-sm font-mono text-soc-text">Agregar servidor</span>
          <button onClick={onClose} className="soc-btn-ghost p-1"><X size={14} /></button>
        </div>
        <form onSubmit={submit} className="p-6 space-y-4">
          {[
            { field: "hostname",   label: "Hostname",    required: true  },
            { field: "ip_address", label: "IP Address",  required: true  },
            { field: "role",       label: "Rol",         required: false },
            { field: "os",         label: "OS",          required: false },
          ].map(({ field, label, required }) => (
            <div key={field}>
              <label className="text-xs font-mono text-soc-muted uppercase tracking-widest block mb-1">
                {label}
              </label>
              <input
                required={required}
                value={form[field]}
                onChange={e => setForm(p => ({ ...p, [field]: e.target.value }))}
                className="w-full bg-soc-surface border border-soc-border rounded px-3 py-2 text-xs font-mono text-soc-text focus:outline-none focus:border-soc-green/50 focus:shadow-glow-green transition-all"
                placeholder={field}
              />
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="soc-btn-ghost flex-1">Cancelar</button>
            <button type="submit" disabled={saving} className="soc-btn-primary flex-1">
              {saving ? "Guardando..." : "Agregar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export function Servers() {
  const [showAdd, setShowAdd] = useState(false)
  const qc = useQueryClient()
  const { data: servers, isLoading } = useQuery({
    queryKey: ["servers"],
    queryFn: api.servers.list,
    refetchInterval: 10_000,
  })

  const online  = servers?.filter(s => s.status === "online").length ?? 0
  const offline = servers?.filter(s => s.status === "offline").length ?? 0

  return (
    <div className="p-6 space-y-4 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-mono font-semibold text-soc-text">
            <span className="text-soc-green">&gt;</span> SERVIDORES
          </h1>
          <p className="text-xs font-mono text-soc-muted mt-0.5">
            <span className="text-soc-green">{online} online</span>
            {offline > 0 && <span className="text-soc-red ml-2">{offline} offline</span>}
          </p>
        </div>
        <button onClick={() => setShowAdd(true)} className="soc-btn-primary flex items-center gap-1.5">
          <Plus size={12} /> Agregar
        </button>
      </div>

      {isLoading ? (
        <p className="text-xs font-mono text-soc-muted text-center py-8">Cargando...</p>
      ) : !servers?.length ? (
        <div className="soc-card text-center py-12">
          <p className="text-xs font-mono text-soc-muted">Sin servidores registrados</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {servers.map(s => <ServerCard key={s.id} server={s} />)}
        </div>
      )}

      {showAdd && (
        <AddServerModal
          onClose={() => setShowAdd(false)}
          onAdd={() => { qc.invalidateQueries({ queryKey: ["servers"] }); setShowAdd(false) }}
        />
      )}
    </div>
  )
}
