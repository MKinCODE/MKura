import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Calendar, Clock, Users, LogOut, Loader2, AlertCircle, CheckCircle, Blocks } from 'lucide-react'
import { doctorApi } from '../services/api'

interface SlotData {
  id: number
  date: string
  start_time: string
  end_time: string
  status: string
  patient_name: string | null
  patient_email: string | null
}

export default function DoctorDashboard() {
  const navigate = useNavigate()
  const [slots, setSlots] = useState<SlotData[]>([])
  const [loading, setLoading] = useState(true)
  const [blocking, setBlocking] = useState<number | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('doctor_token')
    if (!token) {
      navigate('/doctor/login')
      return
    }
    fetchSlots()
  }, [navigate])

  const fetchSlots = async () => {
    try {
      const response = await doctorApi.getSlots()
      setSlots(response.data)
    } catch (err: any) {
      if (err.response?.status === 401) {
        localStorage.removeItem('doctor_token')
        localStorage.removeItem('refresh_token')
        navigate('/doctor/login')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleBlockSlot = async (slotId: number) => {
    setBlocking(slotId)
    setMessage(null)
    try {
      const response = await doctorApi.blockSlot(slotId)
      setMessage({ type: 'success', text: response.data.message })
      await fetchSlots()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to block slot' })
    } finally {
      setBlocking(null)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('doctor_token')
    localStorage.removeItem('refresh_token')
    navigate('/')
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' })
  }

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':')
    const hour = parseInt(hours)
    const ampm = hour >= 12 ? 'PM' : 'AM'
    const hour12 = hour % 12 || 12
    return `${hour12}:${minutes} ${ampm}`
  }

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'available': return 'bg-emerald-50 border-emerald-200 text-emerald-700'
      case 'booked': return 'bg-blue-50 border-blue-200 text-blue-700'
      case 'blocked': return 'bg-red-50 border-red-200 text-red-700'
      default: return 'bg-surface-100 border-surface-300 text-text-500'
    }
  }

  const getCardStyle = (status: string) => {
    switch (status) {
      case 'available': return 'border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50'
      case 'booked': return 'border-blue-200 bg-blue-50/50 hover:bg-blue-50 cursor-pointer'
      case 'blocked': return 'border-red-200 bg-red-50/50'
      default: return 'border-surface-300 bg-surface-50'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'available': return <CheckCircle className="w-4 h-4" />
      case 'booked': return <Users className="w-4 h-4" />
      case 'blocked': return <Blocks className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  const groupedSlots = slots.reduce((acc, slot) => {
    if (!acc[slot.date]) acc[slot.date] = []
    acc[slot.date].push(slot)
    return acc
  }, {} as Record<string, SlotData[]>)

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-700 animate-spin mx-auto mb-4" />
          <p className="text-text-500">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface-100">
      <nav className="bg-white border-b border-surface-300 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="MK Health" className="w-10 h-10 rounded-lg object-contain" />
            <div>
              <h1 className="font-display font-bold text-text-900 text-lg leading-none">Doctor Dashboard</h1>
              <p className="text-xs text-text-500">MK Health Clinic</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-text-500 text-sm">Dr. Vikram Mehta</span>
            <button onClick={handleLogout} className="flex items-center gap-2 text-text-500 hover:text-red-600 transition-colors text-sm">
              <LogOut className="w-4 h-4" /> Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`mb-6 flex items-center gap-3 px-4 py-3 rounded-xl border ${
              message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
            {message.text}
          </motion.div>
        )}

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white border border-surface-300 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <p className="text-text-500 text-sm">Available Slots</p>
                <p className="text-2xl font-bold text-text-900">{slots.filter((s) => s.status === 'available').length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white border border-surface-300 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-text-500 text-sm">Booked Slots</p>
                <p className="text-2xl font-bold text-text-900">{slots.filter((s) => s.status === 'booked').length}</p>
              </div>
            </div>
          </div>
          <div className="bg-white border border-surface-300 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <Blocks className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-text-500 text-sm">Blocked Slots</p>
                <p className="text-2xl font-bold text-text-900">{slots.filter((s) => s.status === 'blocked').length}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white border border-surface-300 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-6 border-b border-surface-300">
            <h2 className="text-xl font-display font-bold text-text-900">Schedule — Next 7 Days</h2>
            <p className="text-text-500 text-sm mt-1">Click on a booked slot to block it for emergency</p>
          </div>

          <div className="divide-y divide-surface-300">
            {Object.entries(groupedSlots).map(([date, daySlots]) => (
              <div key={date} className="p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Calendar className="w-5 h-5 text-primary-700" />
                  <h3 className="text-lg font-semibold text-text-900">{formatDate(date)}</h3>
                </div>

                <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {daySlots.map((slot) => (
                    <div
                      key={slot.id}
                      className={`border rounded-xl p-4 transition-colors ${getCardStyle(slot.status)}`}
                      onClick={() => slot.status === 'booked' && handleBlockSlot(slot.id)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-medium border ${getStatusStyle(slot.status)}`}>
                          {getStatusIcon(slot.status)}
                          {slot.status}
                        </span>
                        {blocking === slot.id && <Loader2 className="w-4 h-4 text-primary-700 animate-spin" />}
                      </div>

                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-4 h-4 text-text-400" />
                        <span className="text-text-900 font-medium">{formatTime(slot.start_time)} - {formatTime(slot.end_time)}</span>
                      </div>

                      {slot.patient_name && (
                        <div className="mt-2 pt-2 border-t border-surface-300">
                          <p className="text-text-700 text-sm">{slot.patient_name}</p>
                          <p className="text-text-400 text-xs">{slot.patient_email}</p>
                        </div>
                      )}

                      {slot.status === 'booked' && <p className="text-xs text-text-400 mt-2">Click to block (emergency)</p>}
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {slots.length === 0 && (
              <div className="p-12 text-center">
                <Calendar className="w-12 h-12 text-surface-500 mx-auto mb-4" />
                <p className="text-text-500">No slots available for the next 7 days</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}