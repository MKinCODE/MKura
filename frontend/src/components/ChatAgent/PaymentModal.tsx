import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CreditCard, Loader2, CheckCircle2, ShieldCheck, Lock, ArrowLeft, Globe } from 'lucide-react'
import { bookingApi } from '../../services/api'

// Simple mock transaction ID generator
const generateTxnId = () => 'ch_' + Math.random().toString(36).substring(2, 12).toUpperCase()

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
  const [isProcessing, setIsProcessing] = useState(false)
  const [loadingState, setLoadingState] = useState('Processing payment...')
  const [error, setError] = useState<string | null>(null)
  
  // Card Form State
  const [cardNumber, setCardNumber] = useState('4242 4242 4242 4242')
  const [expiry, setExpiry] = useState('12/28')
  const [cvc, setCvc] = useState('123')
  const [cardholder, setCardholder] = useState(bookingData?.patient_name || '')
  const [country, setCountry] = useState('India')
  const [txnId, setTxnId] = useState('')

  useEffect(() => {
    if (bookingData?.patient_name) {
      setCardholder(bookingData.patient_name)
    }
  }, [bookingData])

  if (!isOpen) return null

  // Card Formatters
  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '')
    if (value.length > 16) value = value.slice(0, 16)
    const formatted = value.match(/.{1,4}/g)?.join(' ') || value
    setCardNumber(formatted)
  }

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value.replace(/\D/g, '')
    if (value.length > 4) value = value.slice(0, 4)
    if (value.length > 2) {
      setExpiry(`${value.slice(0, 2)}/${value.slice(2)}`)
    } else {
      setExpiry(value)
    }
  }

  const handleCvcChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '')
    if (value.length <= 4) {
      setCvc(value)
    }
  }

  const handleClose = () => {
    localStorage.removeItem('mkura_session_id')
    localStorage.removeItem('mkura_messages')
    onClose()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!cardNumber || !expiry || !cvc || !cardholder) {
      setError('Please fill in all card details.')
      return
    }

    setIsProcessing(true)
    setError(null)
    setLoadingState('Authorizing card...')
    // Reference sessionId to prevent TS unused variable check
    const _session = sessionId
    if (!_session) {
      console.warn('Session ID missing')
    }

    try {
      // Step 1: Simulate bank authorization delay
      await new Promise(resolve => setTimeout(resolve, 1200))
      
      setLoadingState('Securing appointment...')
      
      // Step 2: Book slot
      const response = await bookingApi.createBooking({
        slot_id: bookingData.slot_id,
        patient_name: bookingData.patient_name,
        patient_email: bookingData.patient_email,
        patient_phone: bookingData.patient_phone,
        wants_waitlist: false,
      })

      const { booking_id } = response.data

      // Step 3: Confirm payment on backend
      await bookingApi.confirmPayment(booking_id)
      
      // Generate transaction details for success screen
      setTxnId(generateTxnId())
      
      // Additional slight delay for realistic processing feel
      await new Promise(resolve => setTimeout(resolve, 600))
      
      setSuccess(true)
      
      // Automatically trigger completion after displaying receipt
      setTimeout(() => {
        if (onPaymentComplete) onPaymentComplete()
        else onClose()
      }, 4000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Payment authorization failed. Please check details and try again.')
      setIsProcessing(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-0 sm:p-4 bg-black/50 chat-backdrop">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-[#0a0a0a]/20"
        onClick={handleClose}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative bg-white w-full max-w-2xl sm:max-w-3xl min-h-[500px] shadow-2xl border border-slate-200 overflow-hidden flex flex-col md:flex-row rounded-none sm:rounded-md"
        style={{ fontFamily: "'Inter', sans-serif" }}
      >
        <AnimatePresence mode="wait">
          {success ? (
            <motion.div
              key="success"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full p-8 flex flex-col items-center justify-center text-center bg-white"
            >
              <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-full flex items-center justify-center mb-4 border border-emerald-200">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-medium text-slate-900 mb-1">Payment Successful</h3>
              <p className="text-sm text-slate-500 mb-6">Your appointment deposit has been authorized.</p>

              {/* Sharp, realistic receipt block */}
              <div className="w-full max-w-md bg-slate-50 border border-slate-200 rounded-none p-5 text-left mb-8 space-y-3 text-xs text-slate-600">
                <div className="flex justify-between border-b border-slate-200 pb-2">
                  <span className="font-semibold text-slate-800">Merchant</span>
                  <span>MK Health Clinic</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold text-slate-800">Transaction ID</span>
                  <span className="font-mono text-slate-900">{txnId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold text-slate-800">Card Number</span>
                  <span>•••• •••• •••• {cardNumber.slice(-4) || '4242'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold text-slate-800">Billing Name</span>
                  <span>{cardholder}</span>
                </div>
                <div className="flex justify-between border-t border-slate-200 pt-2 font-medium">
                  <span className="text-slate-800">Amount Charged (Demo)</span>
                  <span className="text-slate-900 text-sm font-semibold">₹100.00</span>
                </div>
              </div>

              <button
                onClick={() => {
                  if (onPaymentComplete) onPaymentComplete()
                  else handleClose()
                }}
                className="px-6 py-2 bg-[#30313d] hover:bg-[#1a1b21] text-white text-sm font-medium rounded-md transition-colors shadow-sm"
              >
                Continue to Appointment
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="form"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full flex flex-col md:flex-row"
            >
              {/* Left Column: Invoice Summary (Stripe style) */}
              <div className="w-full md:w-5/12 bg-slate-50 p-6 md:p-8 border-b md:border-b-0 md:border-r border-slate-200 flex flex-col justify-between">
                <div>
                  <button 
                    onClick={handleClose}
                    className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition-colors mb-8"
                  >
                    <ArrowLeft className="w-3.5 h-3.5" />
                    Back to MK Health Clinic
                  </button>

                  <div className="space-y-1">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Consultation Deposit</span>
                    <h2 className="text-3xl font-semibold text-slate-900 tracking-tight">₹100.00</h2>
                  </div>

                  <div className="mt-8 space-y-4 text-xs">
                    <div className="flex items-start justify-between border-b border-slate-200/60 pb-3">
                      <div>
                        <p className="font-medium text-slate-800">Appointment Deposit</p>
                        <p className="text-slate-400 mt-0.5">100% Refundable upon cancellation</p>
                      </div>
                      <span className="font-medium text-slate-900">₹100.00</span>
                    </div>

                    <div className="space-y-2">
                      <p className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Patient Details</p>
                      <div className="bg-white border border-slate-200 p-3 space-y-1 text-slate-600">
                        <p className="font-medium text-slate-800">{bookingData?.patient_name || 'Patient'}</p>
                        <p className="truncate text-slate-500">{bookingData?.patient_email || 'No email'}</p>
                        <p className="text-slate-500">{bookingData?.patient_phone || 'No phone'}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-8 pt-4 border-t border-slate-200 flex items-center gap-2 text-slate-400">
                  <ShieldCheck className="w-4 h-4 text-slate-500" />
                  <span className="text-[10px] font-medium leading-none">Guaranteed Booking Coordination</span>
                </div>
              </div>

              {/* Right Column: Checkout Fields */}
              <form onSubmit={handleSubmit} className="w-full md:w-7/12 p-6 md:p-8 flex flex-col justify-between bg-white">
                <div className="space-y-5">
                  <h3 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">Pay with Card</h3>

                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-none flex items-start gap-2">
                      <span className="font-bold">Error:</span>
                      <span>{error}</span>
                    </div>
                  )}

                  {/* Standard Form Inputs with Sharp Edges */}
                  <div className="space-y-4 text-xs">
                    <div>
                      <label htmlFor="email" className="block text-slate-500 font-medium mb-1">Email</label>
                      <input
                        type="email"
                        id="email"
                        className="w-full px-3 py-2 border border-slate-200 rounded-none bg-slate-50 text-slate-400 cursor-not-allowed focus:outline-none"
                        value={bookingData?.patient_email || ''}
                        disabled
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="block text-slate-500 font-medium">Card Details</label>
                      
                      <div className="border border-slate-200 focus-within:ring-2 focus-within:ring-[#635BFF] focus-within:border-[#635BFF] transition-all">
                        {/* Card Number row */}
                        <div className="relative border-b border-slate-200">
                          <input
                            type="text"
                            placeholder="Card Number"
                            className="w-full px-3 py-2.5 pr-10 focus:outline-none placeholder-slate-300"
                            value={cardNumber}
                            onChange={handleCardNumberChange}
                            required
                          />
                          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center text-slate-400">
                            <CreditCard className="w-4 h-4" />
                          </div>
                        </div>

                        {/* Expiry and CVC Row */}
                        <div className="flex divide-x divide-slate-200">
                          <input
                            type="text"
                            placeholder="MM / YY"
                            className="w-1/2 px-3 py-2.5 focus:outline-none placeholder-slate-300"
                            value={expiry}
                            onChange={handleExpiryChange}
                            required
                          />
                          <input
                            type="password"
                            placeholder="CVC"
                            maxLength={4}
                            className="w-1/2 px-3 py-2.5 focus:outline-none placeholder-slate-300"
                            value={cvc}
                            onChange={handleCvcChange}
                            required
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <label htmlFor="cardholder" className="block text-slate-500 font-medium mb-1">Cardholder Name</label>
                      <input
                        type="text"
                        id="cardholder"
                        placeholder="Name on card"
                        className="w-full px-3 py-2.5 border border-slate-200 rounded-none focus:outline-none focus:ring-2 focus:ring-[#635BFF] focus:border-[#635BFF] placeholder-slate-300 text-slate-800"
                        value={cardholder}
                        onChange={(e) => setCardholder(e.target.value)}
                        required
                      />
                    </div>

                    <div>
                      <label htmlFor="country" className="block text-slate-500 font-medium mb-1">Country or Region</label>
                      <div className="relative border border-slate-200">
                        <select
                          id="country"
                          className="w-full px-3 py-2.5 pr-8 bg-white focus:outline-none focus:ring-2 focus:ring-[#635BFF] focus:border-[#635BFF] text-slate-700 appearance-none rounded-none"
                          value={country}
                          onChange={(e) => setCountry(e.target.value)}
                        >
                          <option value="India">India</option>
                          <option value="United States">United States</option>
                          <option value="United Kingdom">United Kingdom</option>
                          <option value="Canada">Canada</option>
                          <option value="Singapore">Singapore</option>
                        </select>
                        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                          <Globe className="w-3.5 h-3.5" />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Clean professional warning banner - NO rounded corners, sharp gray border */}
                  <div className="border border-slate-200 bg-slate-50 p-4 text-[11px] leading-relaxed text-slate-500 space-y-1">
                    <p className="font-semibold text-slate-700">🔒 Demo Mode Information</p>
                    <p>
                      This is a simulated billing interface. No actual charge is processed, and your card will not be billed. <strong>No real money is deducted.</strong> You can use standard mock credentials to continue.
                    </p>
                  </div>
                </div>

                <div className="mt-8 space-y-3">
                  <button
                    type="submit"
                    disabled={isProcessing}
                    className="w-full bg-[#30313d] hover:bg-[#1a1b21] disabled:bg-slate-300 text-white font-medium py-3 rounded-none transition-colors flex items-center justify-center gap-2 text-sm shadow-sm"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                        <span>{loadingState}</span>
                      </>
                    ) : (
                      <>
                        <Lock className="w-3.5 h-3.5" />
                        <span>Pay ₹100.00</span>
                      </>
                    )}
                  </button>

                  <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-400">
                    <Lock className="w-3 h-3 text-slate-400" />
                    <span>Secure connection via simulated gateway</span>
                  </div>
                </div>
              </form>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}