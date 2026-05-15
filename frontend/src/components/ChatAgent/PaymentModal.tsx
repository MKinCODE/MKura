import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CreditCard, Loader2, CheckCircle, ShieldCheck } from 'lucide-react'
import { bookingApi } from '../../services/api'

function PaymentForm({
  bookingData,
  onSuccess,
}: {
  bookingData: any
  sessionId: string
  onSuccess: () => void
}) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [loadingState, setLoadingState] = useState('Processing transaction...')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setIsProcessing(true)
    setError(null)
    setLoadingState('Processing transaction...')

    try {
      // Simulated payment delay
      await new Promise(resolve => setTimeout(resolve, 1500))

      setLoadingState('Securing appointment...')
      
      const response = await bookingApi.createBooking({
        slot_id: bookingData.slot_id,
        patient_name: bookingData.patient_name,
        patient_email: bookingData.patient_email,
        patient_phone: bookingData.patient_phone,
        wants_waitlist: false,
      })

      const { booking_id } = response.data

      await bookingApi.confirmPayment(booking_id)
      
      // Additional slight delay for realistic feel
      await new Promise(resolve => setTimeout(resolve, 500))
      
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

      <div className="bg-surface-100 border border-surface-300 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-text-500" />
            <span className="text-text-700 font-medium">•••• •••• •••• 4242</span>
          </div>
          <span className="text-text-400 text-sm">12/28</span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-2 text-red-600 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={isProcessing}
        className="w-full bg-primary-800 hover:bg-primary-700 disabled:bg-surface-400 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            {loadingState}
          </>
        ) : (
          <>
            <ShieldCheck className="w-4 h-4" />
            Pay ₹100 (Demo – Refundable)
          </>
        )}
      </button>

      <p className="text-xs text-text-400 text-center">
        This is a secure, simulated demo payment environment.
      </p>
    </form>
  )
}

export function PaymentModal({
  isOpen,
  onClose,
  bookingData,
  sessionId,
  onPaymentComplete,
}: {
  isOpen: boolean
  onClose: () => void
  bookingData: any
  sessionId: string
  onPaymentComplete?: () => void
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
        <AnimatePresence mode="wait">
        {success ? (
          <motion.div 
            key="success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-8 text-center"
          >
            <div className="w-16 h-16 bg-primary-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-primary-800" />
            </div>
            <h3 className="text-xl font-bold text-text-900 mb-2">Payment Successful!</h3>
            <p className="text-text-500 mb-6">
              Your appointment has been secured.
            </p>
            <button
              onClick={() => {
                if (onPaymentComplete) onPaymentComplete()
                else onClose()
              }}
              className="bg-primary-800 hover:bg-primary-700 text-white font-semibold px-6 py-2.5 rounded-xl transition-colors"
            >
              Continue
            </button>
          </motion.div>
        ) : (
          <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
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
                <span className="text-2xl font-bold text-amber-600">₹100</span>
              </div>

              <div className="mb-6 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                <p className="text-emerald-700 text-xs font-medium">🧪 Test Mode – No real money is charged</p>
              </div>

              <PaymentForm
                bookingData={bookingData}
                sessionId={sessionId}
                onSuccess={() => {
                  setSuccess(true)
                  // Automatically trigger continue after a brief delay
                  setTimeout(() => {
                    if (onPaymentComplete) onPaymentComplete()
                    else onClose()
                  }, 2000)
                }}
              />
            </div>
          </motion.div>
        )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}