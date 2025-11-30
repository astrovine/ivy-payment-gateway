import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Layout({ children }) {
  const { token, logout } = useAuth()
  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-800 flex">
      <aside className="w-64 border-r border-neutral-200 bg-white p-4 hidden md:flex flex-col">
        <h2 className="text-lg font-semibold mb-6">Gateway</h2>
        <nav className="space-y-2 text-sm">
          <Link className="block px-2 py-1 rounded hover:bg-neutral-100" to="/onboarding">Onboarding</Link>
          <Link className="block px-2 py-1 rounded hover:bg-neutral-100" to="/dashboard">Dashboard</Link>
          <Link className="block px-2 py-1 rounded hover:bg-neutral-100" to="/merchant">Merchant</Link>
          <Link className="block px-2 py-1 rounded hover:bg-neutral-100" to="/charges">Charges</Link>
        </nav>
        <div className="mt-auto pt-4 border-t border-neutral-200">
          {token ? (
            <button onClick={logout} className="text-xs text-red-600 hover:underline">Logout</button>
          ) : (
            <Link to="/login" className="text-xs text-blue-600 hover:underline">Login</Link>
          )}
        </div>
      </aside>
      <main className="flex-1 p-6 max-w-5xl mx-auto w-full">{children}</main>
    </div>
  )
}

