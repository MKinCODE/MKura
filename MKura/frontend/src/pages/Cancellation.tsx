import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Calendar, Clock, User, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { bookingApi } from '../services/api'

interface BookingDetails {
  booking_id: number
  patient_name: string
  date: string
  time: string
  doctor_name: string
  valid: boolean
}

export default function Cancellation() {
  const { bookingId, token } = useParams()
  const navigate = useNavigate()
  const [booking, setBooking] = useState<BookingDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    const validateToken = async () => {
      try {
        const response = await bookingApi.validateCancellation(
          Number(bookingId),
          token || ''
        )
        setBooking(response.data)
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Invalid cancellation link')
      } finally {
        setLoading(false)
      }
    }

    validateToken()
  }, [bookingId, token])

  const handleCancel = async () => {
    if (!booking) return

    setCancelling(true)
    setError(null)

    try {
      await bookingApi.cancelBooking(booking.booking_id, token || '')
      setSuccess(true)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to cancel booking')
    } finally {
      setCancelling(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-700 animate-spin mx-auto mb-4" />
          <p className="text-text-500">Loading booking details...</p>
        </div>
      </div>
    )
  }

  if (error && !booking) {
    return (
      <div className="min-h-screen bg-surface-100 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-surface-300 rounded-2xl p-8 max-w-md w-full text-center shadow-sm"
        >
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-2xl font-display font-bold text-text-900 mb-2">Invalid Link</h2>
          <p className="text-text-500 mb-6">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="bg-primary-800 hover:bg-primary-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors"
          >
            Go to Homepage
          </button>
        </motion.div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="min-h-screen bg-surface-100 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white border border-surface-300 rounded-2xl p-8 max-w-md w-full text-center shadow-sm"
        >
          <div className="w-16 h-16 bg-primary-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-primary-800" />
          </div>
          <h2 className="text-2xl font-display font-bold text-text-900 mb-2">Booking Cancelled</h2>
          <p className="text-text-500 mb-6">
            Your appointment has been cancelled successfully. A confirmation email has been sent to you.
          </p>
          <button
            onClick={() => navigate('/')}
            className="bg-primary-800 hover:bg-primary-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors"
          >
            Back to Home
          </button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white border border-surface-300 rounded-2xl p-8 max-w-md w-full shadow-sm"
      >
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-2xl font-display font-bold text-text-900 mb-2">Cancel Appointment?</h2>
          <p className="text-text-500">Are you sure you want to cancel your appointment?</p>
        </div>

        {booking && (
          <div className="bg-surface-100 border border-surface-300 rounded-xl p-6 mb-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <User className="w-5 h-5 text-text-400" />
                <span className="text-text-900">{booking.patient_name}</span>
              </div>
              <div className="flex items-center gap-3">
                <Calendar className="w-5 h-5 text-text-400" />
                <span className="text-text-900">{booking.date}</span>
              </div>
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-text-400" />
                <span className="text-text-900">{booking.time}</span>
              </div>
              <div className="flex items-center gap-3">
                <User className="w-5 h-5 text-text-400" />
                <span className="text-text-900">{booking.doctor_name}</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2 mb-4 text-red-600 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={() => navigate('/')}
            className="flex-1 border-2 border-surface-400 hover:border-primary-600 text-text-900 px-6 py-3 rounded-xl font-semibold transition-colors"
          >
            Keep Appointment
          </button>
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="flex-1 bg-red-600 hover:bg-red-500 disabled:bg-surface-400 text-white px-6 py-3 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2"
          >
            {cancelling ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Cancelling...
              </>
            ) : (
              'Confirm Cancel'
            )}
          </button>
        </div>
      </motion.div>
    </div>
  )
}