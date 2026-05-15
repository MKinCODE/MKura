import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, MessageCircle, Send, Bot, User, Loader2 } from 'lucide-react'
import { chatApi, bookingApi } from '../../services/api'
import { PaymentModal } from './PaymentModal'

interface Message {
  role: 'assistant' | 'user'
  content: string
}

export default function ChatPopup() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Welcome to MK Health Clinic! I'm MKura, your scheduling assistant. I'm here to help you book an appointment. What's your name?",
    },
  ])
  const [input, setInput] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [showPayment, setShowPayment] = useState(false)
  const [bookingData, setBookingData] = useState<any>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Prevent body scroll when chat is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const response = await chatApi.sendMessage(userMessage, sessionId || undefined)
      const { response: botResponse, session_id, action, data } = response.data

      if (!sessionId) setSessionId(session_id)
      setMessages((prev) => [...prev, { role: 'assistant', content: botResponse }])

      if (action === 'redirect_payment' && data) {
        setBookingData(data)
        setShowPayment(true)
      }

      if (action === 'complete' && data) {
        const slotResponse = await chatApi.getEarliestSlot()
        const slot = slotResponse.data

        await bookingApi.createBooking({
          slot_id: slot.id,
          patient_name: data.patient_name,
          patient_email: data.patient_email,
          patient_phone: data.patient_phone,
          wants_waitlist: data.wants_waitlist,
        })
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* ─── Floating Chat Button (72px, prominent) ─── */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            onClick={() => setIsOpen(true)}
            className="fixed bottom-6 right-6 z-50 w-[72px] h-[72px] rounded-full shadow-2xl flex items-center justify-center transition-all duration-300 hover:scale-110 group"
            style={{ background: 'linear-gradient(135deg, #2D6A4F 0%, #40916C 100%)' }}
          >
            <MessageCircle className="w-8 h-8 text-white group-hover:rotate-12 transition-transform" />
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-amber-400 rounded-full animate-pulse border-2 border-white" />
            {/* Ripple ring */}
            <span className="absolute inset-0 rounded-full border-2 border-primary-600 animate-ping opacity-30" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* ─── Chat Modal (Centered, Portrait, Blurred Background) ─── */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop with blur */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="fixed inset-0 z-[90] bg-black/40 chat-backdrop"
              onClick={() => setIsOpen(false)}
            />

            {/* Chat panel — centered, portrait (height > width) */}
            <motion.div
              initial={{ opacity: 0, scale: 0.85, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.85, y: 30 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed inset-0 z-[95] flex items-center justify-center p-4 pointer-events-none"
            >
              <div
                className="pointer-events-auto w-full flex flex-col bg-white rounded-2xl shadow-2xl border border-surface-300 overflow-hidden"
                style={{ maxWidth: '420px', height: '85vh', maxHeight: '85vh' }}
              >
                {/* Header */}
                <div className="flex-shrink-0 p-4 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%)' }}>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-white text-[15px]">MKura</h3>
                      <p className="text-xs text-white/70">MK Health Clinic</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-white/15 transition-colors"
                  >
                    <X className="w-5 h-5 text-white/80" />
                  </button>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface-100">
                  {messages.map((msg, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`flex items-end gap-2 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-primary-800' : 'bg-surface-400'}`}>
                          {msg.role === 'user' ? <User className="w-3.5 h-3.5 text-white" /> : <Bot className="w-3.5 h-3.5 text-white" />}
                        </div>
                        <div className={`px-4 py-2.5 rounded-2xl ${msg.role === 'user' ? 'bg-primary-800 text-white rounded-br-sm' : 'bg-white text-text-900 border border-surface-300 rounded-bl-sm shadow-sm'}`}>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                  {isLoading && (
                    <div className="flex items-center gap-2 text-text-500">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Typing...</span>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="flex-shrink-0 p-4 bg-white border-t border-surface-300">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Type your message..."
                      className="flex-1 bg-surface-100 border border-surface-400 rounded-xl px-4 py-3 text-sm text-text-900 placeholder-text-400 focus:outline-none focus:border-primary-600 transition-colors"
                    />
                    <button
                      onClick={handleSend}
                      disabled={!input.trim() || isLoading}
                      className="w-12 h-12 rounded-xl flex items-center justify-center transition-colors disabled:bg-surface-300 disabled:cursor-not-allowed"
                      style={input.trim() && !isLoading ? { background: 'linear-gradient(135deg, #2D6A4F 0%, #40916C 100%)' } : {}}
                    >
                      <Send className={`w-4 h-4 ${input.trim() && !isLoading ? 'text-white' : 'text-text-400'}`} />
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {showPayment && bookingData && (
        <PaymentModal
          isOpen={showPayment}
          onClose={() => setShowPayment(false)}
          bookingData={bookingData}
          sessionId={sessionId || ''}
        />
      )}
    </>
  )
}