import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react'
import { doctorApi } from '../services/api'

export default function DoctorLogin() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await doctorApi.login(email, password)
      localStorage.setItem('doctor_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      navigate('/doctor/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 overflow-hidden">
            <img src="/logo.png" alt="MK Health" className="w-full h-full object-contain" />
          </div>
          <h1 className="text-3xl font-display font-bold text-text-900 mb-2">Doctor Portal</h1>
          <p className="text-text-500">Sign in to access your dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white border border-surface-300 rounded-2xl p-8 shadow-sm">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-6 flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <span className="text-red-600 text-sm">{error}</span>
            </div>
          )}

          <div className="space-y-5">
            <div>
              <label className="block text-text-700 text-sm font-medium mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-surface-100 border border-surface-400 rounded-xl px-4 py-3 text-text-900 placeholder-text-400 focus:outline-none focus:border-primary-700 transition-colors"
                placeholder="dr.mehta@mkhealth.com"
              />
            </div>

            <div>
              <label className="block text-text-700 text-sm font-medium mb-2">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full bg-surface-100 border border-surface-400 rounded-xl px-4 py-3 text-text-900 placeholder-text-400 focus:outline-none focus:border-primary-700 transition-colors pr-12"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-text-400 hover:text-text-900"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-800 hover:bg-primary-700 disabled:bg-surface-400 text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </div>
        </form>

        <div className="mt-6 text-center">
          <a href="/" className="text-text-500 hover:text-primary-800 text-sm transition-colors">
            Back to Home
          </a>
        </div>

        <div className="mt-6 bg-white border border-surface-300 rounded-xl p-4 shadow-sm">
          <p className="text-text-500 text-sm text-center mb-2">Demo Credentials</p>
          <p className="text-text-700 text-sm text-center">
            Email: <span className="text-text-900 font-medium">dr.mehta@mkhealth.com</span>
          </p>
          <p className="text-text-700 text-sm text-center">
            Password: <span className="text-text-900 font-medium">doctor123</span>
          </p>
        </div>
      </motion.div>
    </div>
  )
}