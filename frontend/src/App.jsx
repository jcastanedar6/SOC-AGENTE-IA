import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AuthProvider } from "./context/AuthContext"
import ProtectedRoute from "./components/auth/ProtectedRoute"
import { Sidebar } from "./components/layout/Sidebar"
import { Header } from "./components/layout/Header"
import { Dashboard } from "./pages/Dashboard"
import { Incidents } from "./pages/Incidents"
import { Servers } from "./pages/Servers"
import { Events } from "./pages/Events"
import Login from "./pages/Login"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 5_000 },
  },
})

function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-soc-bg">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/"          element={<Dashboard />} />
            <Route path="/incidents" element={<Incidents />} />
            <Route path="/servers"   element={<Servers />}   />
            <Route path="/events"    element={<Events />}    />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/*" element={<ProtectedRoute><AppLayout /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
