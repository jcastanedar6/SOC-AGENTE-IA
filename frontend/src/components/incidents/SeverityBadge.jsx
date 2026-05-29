const MAP = {
  critical: "badge-critical",
  high:     "badge-high",
  medium:   "badge-medium",
  low:      "badge-low",
}

export function SeverityBadge({ severity }) {
  return (
    <span className={`soc-badge ${MAP[severity] ?? "badge-low"}`}>
      {severity?.toUpperCase()}
    </span>
  )
}
