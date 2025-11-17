import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/apiClient'
import Navbar from '../components/Navbar'
import { Upload, FileText, AlertCircle, CheckCircle, Clock, ArrowLeft, User, Briefcase, Check } from 'lucide-react'

const REQUIRED_DOC_TYPES = [
  'business_registration',
  'identity_proof',
  'address_proof'
];

export default function KYC() {
  const navigate = useNavigate()
  const [kycStatus, setKycStatus] = useState(null)
  const [documents, setDocuments] = useState([])

  const [identityData, setIdentityData] = useState(null)
  const [businessData, setBusinessData] = useState(null)

  const [currentTab, setCurrentTab] = useState('identity')

  const [loading, setLoading] = useState(true)
  const [formLoading, setFormLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [identityForm, setIdentityForm] = useState({
    first_name: '', last_name: '', date_of_birth: '', id_number: '', id_type: 'passport',
    address_line1: '', city: '', state_province: '', postal_code: '', country: 'NG'
  })

  const [businessForm, setBusinessForm] = useState({
    legal_business_name: '', business_registration_number: '', tax_id: '',
    incorporation_date: '', incorporation_country: 'NG', business_address_line1: '',
    business_city: '', business_state_province: '', business_postal_code: ''
  })

  const [uploadForm, setUploadForm] = useState({
    document_type: REQUIRED_DOC_TYPES[0],
    file: null,
    file_name: '',
    description: ''
  })

  const fetchKYCData = async () => {
    try {
      setError('')
      const statusData = await api.getKYCStatus()
      setKycStatus(statusData)

      const kycDocs = await api.getKYCDocuments().catch(() => [])
      setDocuments(kycDocs)

      const idData = await api.getKYCIdentity().catch(() => null)
      if (idData) {
        setIdentityData(idData)

        setIdentityForm({
          ...idData,
          date_of_birth: idData.date_of_birth ? idData.date_of_birth.split('T')[0] : ''
        })
      }

      const bizData = await api.getKYCBusiness().catch(() => null)
      if (bizData) {
        setBusinessData(bizData)
        setBusinessForm({
          ...bizData,
          incorporation_date: bizData.incorporation_date ? bizData.incorporation_date.split('T')[0] : ''
        })
      }

    } catch (err) {
      setError(err.message || 'Failed to load KYC data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchKYCData()
  }, [])


  const uploadedDocTypes = useMemo(() =>
    documents.map(doc => doc.document_type),
  [documents])

  const missingDocTypes = useMemo(() =>
    REQUIRED_DOC_TYPES.filter(type => !uploadedDocTypes.includes(type)),
  [uploadedDocTypes])

  const isReadyForReview = useMemo(() =>
    !!identityData && !!businessData && missingDocTypes.length === 0,
  [identityData, businessData, missingDocTypes])

  useEffect(() => {
    if (missingDocTypes.length > 0) {
      setUploadForm(prev => ({ ...prev, document_type: missingDocTypes[0] }))
    }
  }, [missingDocTypes])


  const handleIdentityChange = (e) => {
    setIdentityForm({ ...identityForm, [e.target.name]: e.target.value })
  }

  const handleBusinessChange = (e) => {
    setBusinessForm({ ...businessForm, [e.target.name]: e.target.value })
  }

  const handleIdentitySubmit = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    setError('')
    setSuccess('')
    try {
      const dataToSubmit = {
        ...identityForm,
        date_of_birth: `${identityForm.date_of_birth}T00:00:00Z`
      }
      const data = await api.submitKYCIdentity(dataToSubmit)
      setIdentityData(data)
      setSuccess('Identity information saved successfully!')
      setCurrentTab('business')
    } catch (err) {
      setError(err.message || 'Failed to save identity data. Please check all fields.')
    } finally {
      setFormLoading(false)
    }
  }

  const handleBusinessSubmit = async (e) => {
    e.preventDefault()
    setFormLoading(true)
    setError('')
    setSuccess('')
    try {
      // --- THIS IS THE FIX ---
      // Convert the "YYYY-MM-DD" string to a full ISO string
      const dataToSubmit = {
        ...businessForm,
        incorporation_date: `${businessForm.incorporation_date}T00:00:00Z`
      }
      // -----------------------

      const data = await api.submitKYCBusiness(dataToSubmit)
      setBusinessData(data)
      setSuccess('Business information saved successfully!')
      setCurrentTab('documents')
    } catch (err) {
      setError(err.message || 'Failed to save business data. Please check all fields.')
    } finally {
      setFormLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setUploadForm({
        ...uploadForm,
        file,
        file_name: file.name
      })
    }
  }

  const handleUploadDocument = async (e) => {
    e.preventDefault()
    if (!uploadForm.file) {
      setError('Please select a file')
      return
    }
    setUploading(true)
    setError('')
    setSuccess('')
    try {
      const formData = new FormData()
      formData.append('file', uploadForm.file)
      formData.append('document_type', uploadForm.document_type)
      formData.append('file_name', uploadForm.file_name)
      if (uploadForm.description) {
        formData.append('description', uploadForm.description)
      }

      const response = await fetch('http://localhost:8000/api/v1/kyc/documents', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
        body: formData
      })
      if (!response.ok) throw new Error((await response.json()).detail || 'Upload failed')

      setSuccess('Document uploaded successfully!')
      setUploadForm({ document_type: missingDocTypes[0] || '', file: null, file_name: '', description: '' })
      if(document.getElementById('file-input')) document.getElementById('file-input').value = ''

      await fetchKYCData()
    } catch (err) {
      setError(err.message || 'Failed to upload document')
    } finally {
      setUploading(false)
    }
  }

  const handleSubmitForReview = async () => {
    setLoading(true)
    setError('')
    setSuccess('')
    try {
      await api.submitKYCForReview()
      setSuccess('KYC submitted for review successfully! You will be notified upon completion.')
      await fetchKYCData()
    } catch (err) {
      setError(err.message || 'Failed to submit KYC for review')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const badges = {
      not_started: { color: 'bg-neutral-100 text-neutral-700', icon: AlertCircle, text: 'Not Started' },
      pending: { color: 'bg-yellow-100 text-yellow-700', icon: Clock, text: 'Pending Review' },
      verified: { color: 'bg-green-100 text-green-700', icon: CheckCircle, text: 'Verified' },
      failed: { color: 'bg-red-100 text-red-700', icon: AlertCircle, text: 'Failed' }
    }
    const badge = badges[status] || badges.not_started
    const Icon = badge.icon
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${badge.color}`}>
        <Icon className="w-4 h-4" />
        {badge.text}
      </span>
    )
  }

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-neutral-200 border-t-neutral-900 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-neutral-600">Loading KYC information...</p>
          </div>
        </div>
      </>
    )
  }

  const TabButton = ({ tabName, label, icon: Icon }) => (
    <button
      onClick={() => setCurrentTab(tabName)}
      className={`flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-3 sm:px-6 sm:py-4 text-sm font-semibold rounded-t-lg border-b-2 transition-all ${
        currentTab === tabName
          ? 'border-neutral-900 text-neutral-900'
          : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
      }`}
    >
      <Icon className="w-5 h-5" />
      <span>{label}</span>
    </button>
  )

  const RequirementItem = ({ label, met }) => (
    <li className="flex items-center justify-between text-sm">
      <span className={met ? "text-neutral-600" : "text-neutral-800 font-medium"}>{label}</span>
      {met ? (
        <CheckCircle className="w-5 h-5 text-green-600" />
      ) : (
        <AlertCircle className="w-5 h-5 text-amber-600" />
      )}
    </li>
  )

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-neutral-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <button
            onClick={() => navigate('/dashboard')}
            className="mb-6 flex items-center gap-2 text-neutral-600 hover:text-neutral-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Dashboard</span>
          </button>

          <div className="mb-8">
            <h1 className="text-3xl font-bold text-neutral-900">KYC Verification</h1>
            <p className="text-neutral-600 mt-2">Complete your identity and business verification to unlock payouts.</p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <p className="text-green-700 text-sm">{success}</p>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            <div className="lg:col-span-2 space-y-6">

              <div className="flex flex-col sm:flex-row border-b border-neutral-200">
                <TabButton tabName="identity" label="Identity" icon={User} />
                <TabButton tabName="business" label="Business" icon={Briefcase} />
                <TabButton tabName="documents" label="Documents" icon={FileText} />
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6 sm:p-8">

                {currentTab === 'identity' && (
                  <form onSubmit={handleIdentitySubmit} className="space-y-6">
                    <h2 className="text-xl font-semibold text-neutral-900 mb-4">Personal Identity</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <Input label="First Name" name="first_name" value={identityForm.first_name} onChange={handleIdentityChange} required />
                      <Input label="Last Name" name="last_name" value={identityForm.last_name} onChange={handleIdentityChange} required />
                      <Input label="Date of Birth" name="date_of_birth" type="date" value={identityForm.date_of_birth} onChange={handleIdentityChange} required />
                      <Input label="ID Number" name="id_number" value={identityForm.id_number} onChange={handleIdentityChange} required />
                      <Input label="ID Type" name="id_type" value={identityForm.id_type} onChange={handleIdentityChange} required />
                      <Input label="Country" name="country" value={identityForm.country} onChange={handleIdentityChange} required />
                    </div>
                    <div className="border-t border-neutral-200 pt-6">
                      <h3 className="text-lg font-semibold text-neutral-900 mb-4">Home Address</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        <Input label="Address Line 1" name="address_line1" value={identityForm.address_line1} onChange={handleIdentityChange} required />
                        <Input label="City" name="city" value={identityForm.city} onChange={handleIdentityChange} required />
                        <Input label="State / Province" name="state_province" value={identityForm.state_province} onChange={handleIdentityChange} required />
                        <Input label="Postal Code" name="postal_code" value={identityForm.postal_code} onChange={handleIdentityChange} required />
                      </div>
                    </div>
                    <button type="submit" className="btn-primary w-full py-3" disabled={formLoading}>
                      {formLoading ? 'Saving...' : 'Save & Continue'}
                    </button>
                  </form>
                )}

                {currentTab === 'business' && (
                  <form onSubmit={handleBusinessSubmit} className="space-y-6">
                    <h2 className="text-xl font-semibold text-neutral-900 mb-4">Business Information</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      <Input label="Legal Business Name" name="legal_business_name" value={businessForm.legal_business_name} onChange={handleBusinessChange} required />
                      <Input label="Business Registration Number" name="business_registration_number" value={businessForm.business_registration_number} onChange={handleBusinessChange} required />
                      <Input label="Tax ID" name="tax_id" value={businessForm.tax_id} onChange={handleBusinessChange} required />
                      <Input label="Incorporation Date" name="incorporation_date" type="date" value={businessForm.incorporation_date} onChange={handleBusinessChange} required />
                      <Input label="Incorporation Country" name="incorporation_country" value={businessForm.incorporation_country} onChange={handleBusinessChange} required />
                    </div>
                    <div className="border-t border-neutral-200 pt-6">
                      <h3 className="text-lg font-semibold text-neutral-900 mb-4">Business Address</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        <Input label="Address Line 1" name="business_address_line1" value={businessForm.business_address_line1} onChange={handleBusinessChange} required />
                        <Input label="City" name="business_city" value={businessForm.business_city} onChange={handleBusinessChange} required />
                        <Input label="State / Province" name="business_state_province" value={businessForm.business_state_province} onChange={handleBusinessChange} required />
                        <Input label="Postal Code" name="business_postal_code" value={businessForm.business_postal_code} onChange={handleBusinessChange} required />
                      </div>
                    </div>
                    <button type="submit" className="btn-primary w-full py-3" disabled={formLoading}>
                      {formLoading ? 'Saving...' : 'Save & Continue'}
                    </button>
                  </form>
                )}

                {currentTab === 'documents' && (
                  <div>
                    <h2 className="text-xl font-semibold text-neutral-900 mb-4">Upload Required Documents</h2>
                    {missingDocTypes.length > 0 ? (
                      <form onSubmit={handleUploadDocument} className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-2">
                            Document Type
                          </label>
                          <select
                            value={uploadForm.document_type}
                            onChange={(e) => setUploadForm({ ...uploadForm, document_type: e.target.value })}
                            className="input"
                          >
                            {missingDocTypes.map(docType => (
                              <option key={docType} value={docType}>
                                {docType.replace(/_/g, ' ')}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-neutral-700 mb-2">File</label>
                          <input id="file-input" type="file" onChange={handleFileChange} accept=".pdf,.jpg,.jpeg,.png" className="input" />
                        </div>
                        <button type="submit" disabled={uploading || !uploadForm.file} className="w-full btn-primary py-2.5 flex items-center justify-center gap-2">
                          {uploading ? 'Uploading...' : <><Upload className="w-4 h-4" /> Upload Document</>}
                        </button>
                      </form>
                    ) : (
                      <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
                        <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                        <p className="font-semibold text-green-800">All required documents have been uploaded!</p>
                      </div>
                    )}

                    <div className="border-t border-neutral-200 mt-8 pt-6">
                      <h3 className="text-lg font-semibold text-neutral-900 mb-4">Uploaded Files</h3>
                      <div className="space-y-3">
                        {documents.length > 0 ? documents.map((doc) => (
                          <div key={doc.id} className="flex items-center gap-3 p-3 border border-neutral-200 rounded-lg">
                            <FileText className="w-5 h-5 text-neutral-600 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-neutral-900 truncate">{doc.file_name || doc.description}</p>
                              <p className="text-xs text-neutral-600 capitalize">{doc.document_type?.replace(/_/g, ' ')}</p>
                            </div>
                            {doc.status === 'approved' ? (
                              <CheckCircle className="w-5 h-5 text-green-600" />
                            ) : (
                              <Clock className="w-5 h-5 text-yellow-600" />
                            )}
                          </div>
                        )) : (
                          <p className="text-sm text-neutral-500 text-center py-4">No documents uploaded yet.</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-neutral-900">Status</h2>
                  {kycStatus && getStatusBadge(kycStatus.kyc_status)}
                </div>
                {kycStatus?.kyc_status === 'failed' && kycStatus.rejection_reason && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm font-medium text-red-900 mb-1">Rejection Reason</p>
                    <p className="text-sm text-red-700">{kycStatus.rejection_reason}</p>
                  </div>
                )}
                {kycStatus?.kyc_status === 'pending' && (
                  <p className="text-sm text-neutral-600">Your application is under review. This typically takes 24-48 hours.</p>
                )}
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
                <h2 className="text-xl font-semibold text-neutral-900 mb-4">Requirements</h2>
                <ul className="space-y-3">
                  <RequirementItem label="Identity Information" met={!!identityData} />
                  <RequirementItem label="Business Information" met={!!businessData} />
                  {REQUIRED_DOC_TYPES.map(type => (
                    <RequirementItem
                      key={type}
                      label={`${type.replace(/_/g, ' ')}`}
                      met={uploadedDocTypes.includes(type)}
                    />
                  ))}
                </ul>
              </div>

              {kycStatus?.kyc_status === 'not_started' && (
                <div className="bg-white rounded-xl shadow-sm border border-neutral-200 p-6">
                  <h2 className="text-xl font-semibold text-neutral-900 mb-4">Submit for Review</h2>
                  {isReadyForReview ? (
                    <>
                      <p className="text-sm text-neutral-600 mb-4">All requirements are met. You can now submit your application for review.</p>
                      <button
                        onClick={handleSubmitForReview}
                        className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                        disabled={loading}
                      >
                        {loading ? 'Submitting...' : 'Submit Application for Review'}
                      </button>
                    </>
                  ) : (
                    <p className="text-sm text-neutral-600">Please complete all requirements in the list above to submit your application.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

const Input = ({ label, name, type = 'text', value, onChange, required = false, placeholder = '' }) => (
  <div>
    <label htmlFor={name} className="block text-sm font-semibold text-neutral-700 mb-2">
      {label} {required && <span className="text-red-500">*</span>}
    </label>
    <input
      type={type}
      name={name}
      id={name}
      required={required}
      value={value || ''}
      onChange={onChange}
      className="input"
      placeholder={placeholder}
    />
  </div>
)