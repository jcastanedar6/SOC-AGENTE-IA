import { SeverityBadge } from "./SeverityBadge"
import { formatDistanceToNow } from "../utils/time"

const STATUS_COLOR = {
  open:         "text-soc-red",
  investigating:"text-soc-amber",
  resolved:     "text-soc-green",
}

export function IncidentRow({ incident, onSelect }) {
  return (
    <tr
      onClick={() => onSelect(incident)}
      className="border-b border-soc-border hover:bg-white/5 cursor-pointer transition-colors"
    >
      <td className="px-4 py-3 text-xs font-mono text-soc-text-dim">#{incident.id}</td>
      <td className="px-4 py-3 text-xs font-mono text-soc-text max-w-xs truncate">{incident.title}</td>
      <td className="px-4 py-3"><SeverityBadge severity={incident.severity} /></td>
      <td className="px-4 py-3">
        <span className={`text-xs font-mono ${STATUS_COLOR[incident.status] ?? "text-soc-muted"}`}>
          {incident.status}
        </span>
      </td>
      <td className="px-4 py-3 text-xs font-mono text-soc-muted">
        {incident.attack_type?.replace(/_/g, " ") ?? "—"}
      </td>
      <td className="px-4 py-3 text-xs font-mono text-soc-text-dim">
        {formatDistanceToNow(incident.created_at)}
      </td>
    </tr>
  )
}
