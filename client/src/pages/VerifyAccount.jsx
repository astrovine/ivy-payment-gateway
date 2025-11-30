import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../lib/apiClient'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'

export default function VerifyAccount() {
  const navigate = useNavigate()
  const location = useLocation()
  const { token, user, setUser } = useAuth()

  const [formData, setFormData] = useState({
    business_type: '',
    business_name: '',
    industry: '',
    staff_size: '',
    business_email: '',
    business_website: '',
    business_description: '',
    location: '',
    phone_number: '',
    support_email: '',
    support_phone: '',
    bank_account_name: '',
    bank_account_number: '',
    bank_name: '',
    bank_code: '',
    tax_id: ''
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const message = location.state?.message

  useEffect(() => {
    if (user?.is_verified) {
      navigate('/onboarding/merchant')
    }
  }, [user, navigate])

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = { ...formData, staff_size: parseInt(formData.staff_size, 10) }

      const verifiedData = await api.verifyUser(token, data)

      const refreshedUser = await api.getCurrentUser()

      setUser(refreshedUser)
      localStorage.setItem('user', JSON.stringify(refreshedUser))

      navigate('/onboarding/merchant', {
        state: { message: 'Account verified! Now, let\'s create your merchant account.' }
      })
    } catch (err) {
      setError(err.message || 'Verification failed. Please check your details.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg border border-neutral-200">
            <div className="px-6 py-8 sm:px-10">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-neutral-900">Verify Your Business</h1>
                <p className="mt-2 text-sm text-neutral-600">
                  Provide your business details to get started.
                </p>
              </div>

              {message && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm font-medium text-green-800">{message}</p>
                </div>
              )}

              {error && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm font-medium text-red-800">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="mt-8 space-y-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="business_name" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Business Name
                    </label>
                    <input
                      type="text"
                      name="business_name"
                      id="business_name"
                      required
                      value={formData.business_name}
                      onChange={handleChange}
                      className="input"
                      placeholder="Your Company Inc."
                    />
                  </div>
                  <div>
                    <label htmlFor="business_type" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Business Type
                    </label>
                    <select
                      name="business_type"
                      id="business_type"
                      required
                      value={formData.business_type}
                      onChange={handleChange}
                      className="input"
                    >
                      <option value="">Select type...</option>
                      <option value="Starter">Starter (Unregistered)</option>
                      <option value="Registered">Registered Business</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="industry" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Industry
                    </label>
                    <input
                      type="text"
                      name="industry"
                      id="industry"
                      required
                      value={formData.industry}
                      onChange={handleChange}
                      className="input"
                      placeholder="e.g., E-commerce, SaaS"
                    />
                  </div>
                  <div>
                    <label htmlFor="staff_size" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Staff Size
                    </label>
                    <input
                      type="number"
                      name="staff_size"
                      id="staff_size"
                      required
                      value={formData.staff_size}
                      onChange={handleChange}
                      className="input"
                      placeholder="e.g., 10"
                    />
                  </div>
                  <div>
                    <label htmlFor="location" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Location
                    </label>
                    <input
                      type="text"
                      name="location"
                      id="location"
                      required
                      value={formData.location}
                      onChange={handleChange}
                      className="input"
                      placeholder="City, Country"
                    />
                  </div>
                  <div>
                    <label htmlFor="phone_number" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      name="phone_number"
                      id="phone_number"
                      required
                      value={formData.phone_number}
                      onChange={handleChange}
                      className="input"
                      placeholder="+123456789"
                    />
                  </div>
                  <div>
                    <label htmlFor="business_email" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Business Email
                    </label>
                    <input
                      type="email"
                      name="business_email"
                      id="business_email"
                      value={formData.business_email}
                      onChange={handleChange}
                      className="input"
                      placeholder="contact@company.com"
                    />
                  </div>
                  <div>
                    <label htmlFor="business_website" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Website
                    </label>
                    <input
                      type="url"
                      name="business_website"
                      id="business_website"
                      value={formData.business_website}
                      onChange={handleChange}
                      className="input"
                      placeholder="https://company.com"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="business_description" className="block text-sm font-semibold text-neutral-700 mb-2">
                    Business Description
                  </label>
                  <textarea
                    name="business_description"
                    id="business_description"
                    rows={3}
                    value={formData.business_description}
                    onChange={handleChange}
                    className="input"
                    placeholder="What does your business do?"
                  />
                </div>

                <div className="border-t border-neutral-200 pt-6">
                  <h3 className="text-lg font-semibold text-neutral-900">Support & Bank Details</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="support_email" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Support Email
                    </label>
                    <input
                      type="email"
                      name="support_email"
                      id="support_email"
                      value={formData.support_email}
                      onChange={handleChange}
                      className="input"
                      placeholder="support@company.com"
                    />
                  </div>
                  <div>
                    <label htmlFor="support_phone" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Support Phone
                    </label>
                    <input
                      type="tel"
                      name="support_phone"
                      id="support_phone"
                      value={formData.support_phone}
                      onChange={handleChange}
                      className="input"
                      placeholder="+123456789"
                    />
                  </div>
                  <div>
                    <label htmlFor="bank_account_name" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Bank Account Name
                    </label>
                    <input
                      type="text"
                      name="bank_account_name"
                      id="bank_account_name"
                      required
                      value={formData.bank_account_name}
                      onChange={handleChange}
                      className="input"
                      placeholder="Your Company Inc."
                    />
                  </div>
                  <div>
                    <label htmlFor="bank_account_number" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Bank Account Number
                    </label>
                    <input
                      type="text"
                      name="bank_account_number"
                      id="bank_account_number"
                      required
                      value={formData.bank_account_number}
                      onChange={handleChange}
                      className="input"
                      placeholder="1234567890"
                    />
                  </div>
                  <div>
                    <label htmlFor="bank_name" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Bank Name
                    </label>
                    <input
                      type="text"
                      name="bank_name"
                      id="bank_name"
                      value={formData.bank_name}
                      onChange={handleChange}
                      className="input"
                      placeholder="e.g., Chase, Bank of America"
                    />
                  </div>
                  <div>
                    <label htmlFor="bank_code" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Bank Code / Routing Number
                    </label>
                    <input
                      type="text"
                      name="bank_code"
                      id="bank_code"
                      value={formData.bank_code}
                      onChange={handleChange}
                      className="input"
                      placeholder="e.g., 021000021"
                    />
                  </div>
                  <div>
                    <label htmlFor="tax_id" className="block text-sm font-semibold text-neutral-700 mb-2">
                      Tax ID
                    </label>
                    <input
                      type="text"
                      name="tax_id"
                      id="tax_id"
                      value={formData.tax_id}
                      onChange={handleChange}
                      className="input"
                      placeholder="Your business tax ID"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Submitting...
                      </>
                    ) : (
                      'Save and Continue'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}