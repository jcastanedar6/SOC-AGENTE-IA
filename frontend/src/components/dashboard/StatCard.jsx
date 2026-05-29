export function StatCard({ label, value, sub, color = "green", icon: Icon }) {
  const colors = {
    green: "text-soc-green border-soc-green/20 bg-soc-green/5",
    red:   "text-soc-red   border-soc-red/20   bg-soc-red/5",
    amber: "text-soc-amber border-soc-amber/20 bg-soc-amber/5",
    blue:  "text-soc-blue  border-soc-blue/20  bg-soc-blue/5",
  }

  return (
    <div className={`soc-card border ${colors[color]} flex flex-col gap-1`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-soc-muted uppercase tracking-widest">{label}</span>
        {Icon && <Icon size={14} className="text-current opacity-60" />}
      </div>
      <span className="text-3xl font-mono font-semibold text-current">{value ?? "—"}</span>
      {sub && <span className="text-xs font-mono text-soc-muted">{sub}</span>}
    </div>
  )
}
