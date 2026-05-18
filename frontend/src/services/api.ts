import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('doctor_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const chatApi = {
  sendMessage: (message: string, sessionId?: string) =>
    api.post('/chat/message', { message, session_id: sessionId }),

  getEarliestSlot: () => api.get('/chat/slots/earliest'),

  getDoctors: () => api.get('/chat/doctors'),
}

export const bookingApi = {
  createBooking: (data: {
    slot_id: number
    patient_name: string
    patient_email: string
    patient_phone: string
    wants_waitlist: boolean
  }) => api.post('/bookings/create', null, { params: data }),

  confirmPayment: (bookingId: number) =>
    api.post(`/bookings/${bookingId}/confirm-payment`),

  validateCancellation: (bookingId: number, token: string) =>
    api.get(`/bookings/${bookingId}/cancel/${token}`),

  cancelBooking: (bookingId: number, token: string) =>
    api.post(`/bookings/${bookingId}/cancel/${token}`),
}

export const slotsApi = {
  getAvailable: (doctorId?: number, date?: string) =>
    api.get('/slots/available', { params: { doctor_id: doctorId, target_date: date } }),

  getEarliest: (doctorId?: number) => api.get('/slots/earliest', { params: { doctor_id: doctorId } }),

  blockSlot: (slotId: number, reason?: string) =>
    api.post('/slots/block', { slot_id: slotId, reason }),
}

export const doctorApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  getMe: () => api.get('/auth/me'),

  getBookings: () => api.get('/bookings/doctor/all'),

  getSlots: () => api.get('/bookings/doctor/slots'),

  blockSlot: (slotId: number, reason?: string) =>
    api.post('/slots/block', { slot_id: slotId, reason }),

  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),
}

export default api