import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function OnboardingGuard({ children }) {
  const navigate = useNavigate()

  useEffect(() => {
    const userData = localStorage.getItem('user')

    if (!userData || userData === 'undefined') {
      
      navigate('/login')
      return
    }

    try {
      const user = JSON.parse(userData)

      if (user.is_superadmin) {
        return
      }

      const snoozeRaw = localStorage.getItem('onboarding_snooze_until')
      if (snoozeRaw) {
        const until = Number(snoozeRaw)
        if (!Number.isNaN(until) && Date.now() < until) {
          
          return
        } else {
          
          localStorage.removeItem('onboarding_snooze_until')
        }
      }

      if (user.onboarding_stage === 'account_created') {
        
        navigate('/onboarding/verify')
      } else if (user.onboarding_stage === 'verified') {
        
        navigate('/onboarding/merchant')
      }

    } catch {
      navigate('/login')
    }
  }, [navigate])

  return children
}
