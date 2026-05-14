import { useState } from 'react'
import { motion } from 'framer-motion'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { X, CreditCard, Loader2, CheckCircle } from 'lucide-react'
import { bookingApi } from '../../services/api'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_KEY || 'pk_test_placeholder')

function PaymentForm({
  bookingData,
  onSuccess,
}: {
  bookingData: any
  sessionId: string
  onSuccess: () => void
}) {
  const stripe = useStripe()
  const elements = useElements()
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!stripe || !elements) return

    setIsProcessing(true)
    setError(null)

    try {
      const response = await bookingApi.createBooking({
        slot_id: 1,
        patient_name: bookingData.patient_name,
        patient_email: bookingData.patient_email,
        patient_phone: bookingData.patient_phone,
        wants_waitlist: false,
      })

      const { booking_id } = response.data

      await bookingApi.confirmPayment(booking_id)
      onSuccess()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Payment failed. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Demo payment banner */}
      <div className="bg-emerald-50 border border-emerald-300 rounded-xl px-4 py-3 flex items-center gap-2">
        <span className="text-lg">🧪</span>
        <p className="text-emerald-800 text-sm font-medium">
          Demo/Test Payment – No real charges are made.
        </p>
      </div>

      <div className="bg-surface-100 border border-surface-300 rounded-xl p-4">
        <CardElement
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#1A1A1A',
                '::placeholder': { color: '#9E9E9E' },
              },
              invalid: { color: '#ef4444' },
            },
          }}
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2 text-red-600 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={!stripe || isProcessing}
        className="w-full bg-primary-800 hover:bg-primary-700 disabled:bg-surface-400 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <CreditCard className="w-4 h-4" />
            Pay ₹1 (Demo – Refundable)
          </>
        )}
      </button>

      <p className="text-xs text-text-400 text-center">
        This is a test payment. Use card number 4242 4242 4242 4242
      </p>
    </form>
  )
}

export function PaymentModal({
  isOpen,
  onClose,
  bookingData,
  sessionId,
}: {
  isOpen: boolean
  onClose: () => void
  bookingData: any
  sessionId: string
}) {
  const [success, setSuccess] = useState(false)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/40 chat-backdrop"
        onClick={onClose}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-surface-300"
      >
        {success ? (
          <div className="p-8 text-center">
            <div className="w-16 h-16 bg-primary-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-primary-800" />
            </div>
            <h3 className="text-xl font-bold text-text-900 mb-2">Payment Successful!</h3>
            <p className="text-text-500 mb-6">
              Your appointment has been confirmed. Check your email for details.
            </p>
            <button
              onClick={onClose}
              className="bg-primary-800 hover:bg-primary-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors"
            >
              Done
            </button>
          </div>
        ) : (
          <>
            <div className="p-5 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%)' }}>
              <div className="flex items-center gap-3">
                <CreditCard className="w-5 h-5 text-white" />
                <h3 className="font-semibold text-white">Confirm Booking</h3>
              </div>
              <button onClick={onClose} className="text-white/70 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <div className="bg-surface-100 border border-surface-300 rounded-xl p-4 mb-6">
                <h4 className="text-sm text-text-500 mb-2">Booking Details</h4>
                <div className="space-y-1">
                  <p className="text-text-900 font-medium">{bookingData.patient_name}</p>
                  <p className="text-text-500 text-sm">{bookingData.patient_email}</p>
                  <p className="text-text-500 text-sm">{bookingData.patient_phone}</p>
                </div>
              </div>

              <div className="flex items-center justify-between mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl">
                <span className="text-text-700">Demo Deposit</span>
                <span className="text-2xl font-bold text-amber-600">₹1</span>
              </div>

              <div className="mb-6 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                <p className="text-emerald-700 text-xs font-medium">🧪 Test Mode – No real money is charged</p>
              </div>

              <Elements stripe={stripePromise}>
                <PaymentForm
                  bookingData={bookingData}
                  sessionId={sessionId}
                  onSuccess={() => setSuccess(true)}
                />
              </Elements>
            </div>
          </>
        )}
      </motion.div>
    </div>
  )
}