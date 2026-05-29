const BASE = import.meta.env.VITE_API_URL ?? "/api/v1"

function getToken() {
  try { return localStorage.getItem("soc-agent-token") } catch { return null }
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers }
  const token = getToken()
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, { headers, ...options })
  if (res.status === 401 && !path.startsWith("/auth/")) {
    localStorage.removeItem("soc-agent-token")
    localStorage.removeItem("soc-agent-user")
    window.location.href = "/login"
    throw new Error("Sesión expirada")
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `${res.status} ${res.statusText}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  auth: {
    login:   (body) => request("/auth/login", { method: "POST", body: JSON.stringify(body) }),
    verify:  (body) => request("/auth/verify", { method: "POST", body: JSON.stringify(body) }),
    confirm: (body) => request("/auth/confirm", { method: "POST", body: JSON.stringify(body) }),
  },
  events: {
    list:   (params = {}) => request(`/events?${new URLSearchParams(params)}`),
    stats:  () => request("/events/stats"),
    create: (body) => request("/events", { method: "POST", body: JSON.stringify(body) }),
    get:    (id) => request(`/events/${id}`),
    delete: (id) => request(`/events/${id}`, { method: "DELETE" }),
  },
  incidents: {
    list:   (params = {}) => request(`/incidents?${new URLSearchParams(params)}`),
    get:    (id) => request(`/incidents/${id}`),
    update: (id, body) => request(`/incidents/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id) => request(`/incidents/${id}`, { method: "DELETE" }),
  },
  servers: {
    list:   () => request("/servers"),
    create: (body) => request("/servers", { method: "POST", body: JSON.stringify(body) }),
    update: (id, b) => request(`/servers/${id}`, { method: "PATCH", body: JSON.stringify(b) }),
  },
  agent: {
    run:      () => request("/agent/run", { method: "POST" }),
    status:   () => request("/agent/status"),
    llmHealth:() => request("/agent/llm/health"),
  },
}
