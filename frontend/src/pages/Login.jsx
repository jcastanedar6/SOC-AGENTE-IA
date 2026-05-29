import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

const BASE = import.meta.env.VITE_API_URL ?? "/api/v1"

export default function Login() {
  const [step, setStep] = useState(1)
  const [username, setUsername] = useState("")
  const [answer, setAnswer] = useState("")
  const [phone, setPhone] = useState("")
  const [sessionId, setSessionId] = useState("")
  const [code, setCode] = useState("")
  const [question, setQuestion] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleUsername(e) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Usuario incorrecto")
      }
      const data = await res.json()
      setQuestion(data.question)
      setStep(2)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify(e) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer, phone }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Verificación fallida")
      }
      const data = await res.json()
      setSessionId(data.session_id)
      setStep(3)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleConfirm(e) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const res = await fetch(`${BASE}/auth/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, code }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Código inválido")
      }
      const data = await res.json()
      login(data.token, data.user)
      navigate("/", { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-soc-bg px-4">
      <div className="w-full max-w-sm">
        <div className="bg-gray-800 rounded-2xl shadow-xl p-8 border border-gray-700">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Agente SOC
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Acceso al sistema de monitoreo
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-900/40 border border-red-700 text-red-300 text-sm text-center">
              {error}
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleUsername} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Usuario
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Ingrese su usuario"
                  required
                  autoFocus
                  className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !username}
                className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium transition-colors"
              >
                {loading ? "Verificando..." : "Continuar"}
              </button>
            </form>
          ) : step === 2 ? (
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="p-3 rounded-lg bg-blue-900/30 border border-blue-700/50 text-blue-200 text-sm text-center">
                {question}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Respuesta
                </label>
                <input
                  type="text"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Ingrese la respuesta"
                  required
                  autoFocus
                  className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Teléfono registrado
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="Ej: 50255551234"
                  required
                  className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !answer || !phone}
                className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium transition-colors"
              >
                {loading ? "Verificando..." : "Enviar código"}
              </button>
              <button
                type="button"
                onClick={() => { setStep(1); setError("") }}
                className="w-full text-sm text-gray-400 hover:text-gray-300 transition-colors"
              >
                ← Volver
              </button>
            </form>
          ) : (
            <form onSubmit={handleConfirm} className="space-y-4">
              <div className="p-3 rounded-lg bg-green-900/30 border border-green-700/50 text-green-200 text-sm text-center">
                Código enviado por Telegram
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Código de verificación
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="Código de 6 dígitos"
                  required
                  autoFocus
                  inputMode="numeric"
                  className="w-full px-3 py-2 rounded-lg bg-gray-700 border border-gray-600 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-center text-2xl tracking-widest"
                />
              </div>
              <button
                type="submit"
                disabled={loading || code.length !== 6}
                className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium transition-colors"
              >
                {loading ? "Verificando..." : "Ingresar"}
              </button>
              <button
                type="button"
                onClick={() => { setStep(2); setError(""); setCode("") }}
                className="w-full text-sm text-gray-400 hover:text-gray-300 transition-colors"
              >
                ← Volver
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
