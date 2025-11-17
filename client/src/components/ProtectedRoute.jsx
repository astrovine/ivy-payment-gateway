import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const FullPageSpinner = () => (
  <div className="flex items-center justify-center h-screen bg-neutral-50">
    <div className="w-12 h-12 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin" />
  </div>
)

export default function ProtectedRoute({ children }) {
  const { token, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <FullPageSpinner />
  }

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}