import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MapPin, Phone, Mail, Clock, Award, Shield, ChevronDown, Star, ArrowRight, MessageCircle, ChevronLeft, ChevronRight } from 'lucide-react'

const testimonials = [
  { name: 'Priya Sharma', location: 'Jaipur', text: 'Dr. Mehta is very thorough. The AI booking was so convenient!', rating: 5 },
  { name: 'Rajesh Agarwal', location: 'Ajmer', text: 'Excellent diagnosis. Booked my appointment through the chat in under 2 minutes.', rating: 5 },
  { name: 'Sunita Jain', location: 'Udaipur', text: 'The waitlist feature got me an earlier slot when someone cancelled. Amazing!', rating: 5 },
  { name: 'Mohan Lal', location: 'Jodhpur', text: 'Quick appointment booking and minimal waiting time. Great experience!', rating: 5 },
  { name: 'Kavita Rathore', location: 'Kota', text: 'Dr. Mehta treated my diabetes effectively. Follow-up reminders are very helpful.', rating: 5 },
]

const faqs = [
  { question: 'How do I book an appointment?', answer: 'Click the chat button at the bottom-right. MKura, our AI assistant, will guide you through booking in under 2 minutes — just share your name, contact details, and preferred time.' },
  { question: 'What payment methods are accepted?', answer: 'A refundable ₹100 deposit confirms your booking. (Currently in demo mode, no real charges are made.)' },
  { question: 'How do I cancel my appointment?', answer: "You'll receive a confirmation email with a cancellation link. Click it and confirm — your ₹100 deposit is refunded automatically." },
  { question: 'What is the waitlist?', answer: "If your preferred slot is full, join the waitlist. When a cancellation occurs, you'll get a 15-minute window to claim the freed slot." },
  { question: 'What are the clinic hours?', answer: 'Monday to Saturday, 9:00 AM – 6:00 PM. Closed on Sundays and public holidays.' },
  { question: 'Is my data secure?', answer: 'Absolutely. All data is transmitted over encrypted connections. We never share your information with third parties.' },
]

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <div className="border border-surface-400 rounded-xl overflow-hidden hover:border-primary-600/40 transition-colors">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between px-6 py-5 text-left">
        <span className="font-semibold text-text-900 text-[15px] pr-4">{question}</span>
        <ChevronDown className={`w-5 h-5 text-text-500 flex-shrink-0 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3 }} className="overflow-hidden">
            <div className="px-6 pb-5 text-text-500 leading-relaxed text-[15px]">{answer}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function TestimonialCarousel() {
  const [activeIndex, setActiveIndex] = useState(0)
  const [isHovered, setIsHovered] = useState(false)

  useEffect(() => {
    if (isHovered) return
    const timer = setInterval(() => {
      setActiveIndex((current) => (current + 1) % testimonials.length)
    }, 4000)
    return () => clearInterval(timer)
  }, [isHovered])

  const nextSlide = () => setActiveIndex((current) => (current + 1) % testimonials.length)
  const prevSlide = () => setActiveIndex((current) => (current - 1 + testimonials.length) % testimonials.length)

  return (
    <div 
      className="relative w-full max-w-5xl mx-auto h-[400px] flex items-center justify-center overflow-hidden"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="absolute inset-0 flex items-center justify-center perspective-[1000px]">
        <AnimatePresence initial={false} mode="popLayout">
          {testimonials.map((t, index) => {
            // Determine position relative to active index
            let offset = index - activeIndex
            // Handle wrap-around
            if (offset > Math.floor(testimonials.length / 2)) offset -= testimonials.length
            if (offset < -Math.floor(testimonials.length / 2)) offset += testimonials.length

            // Only render cards that are nearby
            if (Math.abs(offset) > 2) return null

            const isCenter = offset === 0
            const isLeft = offset < 0

            return (
              <motion.div
                key={index}
                layout
                initial={{ opacity: 0, scale: 0.8, x: isLeft ? -100 : 100 }}
                animate={{
                  opacity: isCenter ? 1 : 0.6,
                  scale: isCenter ? 1 : 0.85,
                  x: offset * 250, // spread them out
                  z: isCenter ? 0 : -100,
                  rotateY: offset * -15, // slight rotation towards center
                  filter: isCenter ? 'blur(0px)' : 'blur(4px)',
                  zIndex: testimonials.length - Math.abs(offset)
                }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                onClick={() => setActiveIndex(index)}
                className={`absolute w-full max-w-md bg-white border border-surface-300 rounded-3xl p-8 shadow-xl ${!isCenter ? 'cursor-pointer pointer-events-auto hover:opacity-80' : ''}`}
              >
                <div className="flex gap-1 mb-6">
                  {[...Array(t.rating)].map((_, i) => <Star key={i} className="w-5 h-5 text-amber-400 fill-amber-400" />)}
                </div>
                <p className="text-text-700 mb-8 leading-relaxed text-lg">"{t.text}"</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-primary-200 rounded-full flex items-center justify-center">
                    <span className="text-primary-900 font-bold text-lg">{t.name[0]}</span>
                  </div>
                  <div>
                    <div className="text-text-900 font-semibold">{t.name}</div>
                    <div className="text-text-400 text-sm">{t.location}</div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>

      {/* Navigation Buttons */}
      <div className="absolute z-50 flex gap-4 bottom-0">
        <button 
          onClick={prevSlide}
          className="w-10 h-10 rounded-full bg-white/80 backdrop-blur border border-surface-300 shadow-md flex items-center justify-center text-text-700 hover:text-primary-800 hover:bg-white transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <button 
          onClick={nextSlide}
          className="w-10 h-10 rounded-full bg-white/80 backdrop-blur border border-surface-300 shadow-md flex items-center justify-center text-text-700 hover:text-primary-800 hover:bg-white transition-colors"
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}

// Fade in up animation wrapper
const FadeInUp = ({ children, delay = 0, className = "" }: { children: React.ReactNode, delay?: number, className?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 40 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-100px" }}
    transition={{ duration: 0.6, delay, ease: "easeOut" }}
    className={className}
  >
    {children}
  </motion.div>
)

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-surface-300">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="MK Health Clinic" className="w-10 h-10 rounded-lg object-contain" />
            <div>
              <h1 className="font-display font-bold text-text-900 text-lg leading-none">MK Health</h1>
              <p className="text-xs text-text-500">Clinic</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#about" className="text-text-700 hover:text-primary-800 transition-colors text-sm font-medium">About</a>
            <a href="#testimonials" className="text-text-700 hover:text-primary-800 transition-colors text-sm font-medium">Reviews</a>
            <a href="#faq" className="text-text-700 hover:text-primary-800 transition-colors text-sm font-medium">FAQ</a>
            <a href="#location" className="text-text-700 hover:text-primary-800 transition-colors text-sm font-medium">Location</a>
          </div>
          <a href="#book" className="bg-primary-800 hover:bg-primary-700 text-white px-5 py-2.5 rounded-lg font-semibold text-sm transition-colors">Book Now</a>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-28 pb-16 lg:pt-32 lg:pb-24 bg-gradient-to-b from-primary-200/30 to-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <FadeInUp>
              <div className="inline-flex items-center gap-2 bg-primary-200/60 border border-primary-400/40 rounded-full px-4 py-1.5 mb-6">
                <span className="w-2 h-2 bg-primary-700 rounded-full animate-pulse" />
                <span className="text-primary-900 text-sm font-medium">Accepting New Patients</span>
              </div>
              <h1 className="font-display text-4xl sm:text-5xl lg:text-[56px] font-bold text-text-900 leading-[1.1] mb-6">
                MK Health<br />Clinic in <span className="text-primary-800">Jaipur</span>
              </h1>
              <p className="text-lg text-text-500 mb-8 leading-relaxed max-w-lg">
                Experience personalized healthcare with AI-powered appointment booking. Chat with MKura, our assistant, to find the earliest available slot in seconds.
              </p>
              <div className="flex flex-wrap gap-4 mb-10">
                <a href="#book" className="bg-primary-800 hover:bg-primary-700 text-white px-7 py-3.5 rounded-xl font-semibold text-base transition-all hover:shadow-lg hover:shadow-primary-800/20 flex items-center gap-2">
                  Book Appointment <ArrowRight className="w-5 h-5" />
                </a>
                <a href="tel:+919876543210" className="border-2 border-surface-400 hover:border-primary-600 text-text-900 px-7 py-3.5 rounded-xl font-semibold text-base transition-colors flex items-center gap-2">
                  <Phone className="w-5 h-5" /> Call Now
                </a>
              </div>
              <div className="flex flex-wrap gap-10">
                {[{ value: '15+', label: 'Years Experience' }, { value: '10,000+', label: 'Patients Treated' }, { value: '98%', label: 'Satisfaction' }].map((s) => (
                  <div key={s.label}><div className="text-2xl font-bold text-text-900">{s.value}</div><div className="text-text-500 text-sm">{s.label}</div></div>
                ))}
              </div>
            </FadeInUp>
            
            <motion.div initial={{ opacity: 0, scale: 0.9, x: 20 }} animate={{ opacity: 1, scale: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.2 }} className="relative">
              <div className="relative z-10">
                <img src="https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=600&h=700&fit=crop" alt="MK Health Clinic" className="w-full rounded-2xl shadow-xl object-cover" />
                <motion.div 
                  initial={{ opacity: 0, y: 20 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  transition={{ delay: 0.8, type: "spring" }}
                  className="absolute -bottom-5 -left-5 bg-white border border-surface-300 rounded-xl p-4 shadow-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-primary-200 rounded-full flex items-center justify-center"><MessageCircle className="w-6 h-6 text-primary-800" /></div>
                    <div><div className="text-text-900 font-semibold text-sm">AI-Powered Booking</div><div className="text-text-500 text-xs">Book in under 2 min</div></div>
                  </div>
                </motion.div>
              </div>
              <div className="absolute -top-4 -right-4 w-full h-full bg-primary-200/50 rounded-2xl -z-10" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Doctor */}
      <section id="about" className="py-24 bg-surface-100 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <FadeInUp>
            <div className="text-center mb-16">
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-900 mb-4">Meet Your Doctor</h2>
              <div className="w-16 h-1 bg-primary-700 mx-auto rounded-full" />
            </div>
          </FadeInUp>
          
          <FadeInUp delay={0.2}>
            <div className="bg-white border border-surface-300 rounded-3xl p-6 lg:p-10 shadow-sm">
              <div className="grid lg:grid-cols-2 gap-10 items-center">
                <div className="relative">
                  <img src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=500&h=600&fit=crop" alt="Dr. Vikram Mehta" className="w-full rounded-2xl" />
                  <div className="absolute -bottom-4 left-4 right-4 bg-primary-800 text-white text-center py-3 rounded-xl font-semibold text-sm shadow-md">15+ Years Experience</div>
                </div>
                <div>
                  <h3 className="font-display text-3xl font-bold text-text-900 mb-2">Dr. Vikram Mehta</h3>
                  <p className="text-primary-700 font-semibold mb-6">General Physician & Internal Medicine</p>
                  <div className="space-y-5 mb-8">
                    <div className="flex items-start gap-4"><div className="p-2 bg-amber-50 rounded-lg"><Award className="w-5 h-5 text-amber-500 flex-shrink-0" /></div><div><div className="text-text-900 font-medium">Degrees & Certifications</div><div className="text-text-500 text-sm mt-1">MBBS (AIIMS Delhi), MD (Medicine), FIACM</div></div></div>
                    <div className="flex items-start gap-4"><div className="p-2 bg-primary-50 rounded-lg"><Shield className="w-5 h-5 text-primary-700 flex-shrink-0" /></div><div><div className="text-text-900 font-medium">Awards</div><div className="text-text-500 text-sm mt-1">Best Physician Award 2022 (IJCP), Health Excellence Award 2023</div></div></div>
                    <div className="flex items-start gap-4"><div className="p-2 bg-primary-50 rounded-lg"><Clock className="w-5 h-5 text-primary-700 flex-shrink-0" /></div><div><div className="text-text-900 font-medium">Clinic Hours</div><div className="text-text-500 text-sm mt-1">Mon – Sat: 9:00 AM – 6:00 PM</div></div></div>
                  </div>
                  <p className="text-text-500 leading-relaxed mb-8 border-l-4 border-primary-200 pl-4 italic">"Committed to providing personalized healthcare with a patient-first approach. Specialized in diabetes, hypertension, and preventive health checkups."</p>
                  <a href="#book" className="inline-flex items-center gap-2 bg-primary-800 hover:bg-primary-700 text-white px-7 py-3.5 rounded-xl font-semibold transition-colors shadow-md hover:shadow-lg">Book Consultation <ArrowRight className="w-5 h-5" /></a>
                </div>
              </div>
            </div>
          </FadeInUp>
        </div>
      </section>

      {/* Testimonials (3D Carousel) */}
      <section id="testimonials" className="py-24 overflow-hidden relative">
        <div className="max-w-7xl mx-auto px-6">
          <FadeInUp>
            <div className="text-center mb-6">
              <p className="text-primary-700 font-semibold text-sm uppercase tracking-wider mb-3">Patient testimonials</p>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-900 mb-4">What our patients say about us</h2>
              <div className="w-16 h-1 bg-primary-700 mx-auto rounded-full" />
            </div>
          </FadeInUp>
          
          <FadeInUp delay={0.2}>
            <TestimonialCarousel />
          </FadeInUp>
        </div>
      </section>

      {/* CTA Banner */}
      <section id="book" className="py-24 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #5C3D11 0%, #7B5B3A 50%, #5C3D11 100%)' }}>
        <div className="absolute inset-0 opacity-10">
          <div className="w-full h-full" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")` }} />
        </div>
        <div className="relative max-w-4xl mx-auto px-6 text-center">
          <FadeInUp>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-white mb-6">Ready to book your appointment?</h2>
            <p className="text-white/90 text-lg mb-10 max-w-2xl mx-auto leading-relaxed">Click the chat button at the bottom-right to talk to MKura, our AI assistant. Get the earliest available slot in under 2 minutes.</p>
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="inline-block">
              <div className="inline-flex items-center gap-3 bg-white text-accent-700 px-8 py-4 rounded-xl text-lg font-bold shadow-xl cursor-pointer">
                <MessageCircle className="w-6 h-6" /> Chat with us to book →
              </div>
            </motion.div>
          </FadeInUp>
        </div>
      </section>

      {/* FAQs */}
      <section id="faq" className="py-24 bg-surface-100 overflow-hidden">
        <div className="max-w-4xl mx-auto px-6">
          <FadeInUp>
            <div className="text-center mb-16">
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-900 mb-4">Frequently Asked Questions</h2>
              <p className="text-text-500">Everything you need to know about booking and visiting us</p>
            </div>
          </FadeInUp>
          <div className="grid md:grid-cols-2 gap-5">
            {faqs.map((faq, idx) => (
              <FadeInUp key={idx} delay={idx * 0.1}>
                <FAQItem question={faq.question} answer={faq.answer} />
              </FadeInUp>
            ))}
          </div>
        </div>
      </section>

      {/* Location */}
      <section id="location" className="py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <FadeInUp>
            <div className="text-center mb-16">
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-text-900 mb-4">Visit Our Clinic</h2>
              <p className="text-text-500">Located in the heart of Jaipur, serving patients from across Rajasthan</p>
            </div>
          </FadeInUp>
          <div className="grid lg:grid-cols-5 gap-10">
            <div className="lg:col-span-2 space-y-8">
              {[
                { icon: MapPin, title: 'Address', text: 'Sector 21, Gandhinagar, Jaipur, Rajasthan 302015' },
                { icon: Phone, title: 'Phone', text: '+91 98765 43210' },
                { icon: Mail, title: 'Email', text: 'dr.mehta@mkhealth.com' },
              ].map((item, idx) => (
                <FadeInUp key={idx} delay={idx * 0.1}>
                  <div className="flex items-start gap-5">
                    <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-sm"><item.icon className="w-6 h-6 text-primary-800" /></div>
                    <div className="mt-1"><h4 className="text-text-900 font-semibold mb-1 text-lg">{item.title}</h4><p className="text-text-500">{item.text}</p></div>
                  </div>
                </FadeInUp>
              ))}
              <FadeInUp delay={0.3}>
                <div className="flex items-start gap-5">
                  <div className="w-14 h-14 bg-primary-100 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-sm"><Clock className="w-6 h-6 text-primary-800" /></div>
                  <div className="mt-1"><h4 className="text-text-900 font-semibold mb-1 text-lg">Hours</h4><p className="text-text-500">Mon – Sat: 9:00 AM – 6:00 PM</p><p className="text-text-400 text-sm mt-1">Sunday: Closed</p></div>
                </div>
              </FadeInUp>
            </div>
            <FadeInUp delay={0.2} className="lg:col-span-3 h-full min-h-[400px]">
              <div className="bg-surface-200 border border-surface-300 rounded-3xl overflow-hidden shadow-md h-full w-full">
                <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3557.6755737075803!2d75.7873!3d26.9124!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x396db13e3c4c1a9b%3A0x1a2b3c4d5e6f7890!2sSector%2021%2C%20Gandhinagar%2C%20Jaipur%2C%20Rajasthan!5e0!3m2!1sen!2sin!4v1234567890" width="100%" height="100%" style={{ border: 0, minHeight: '400px' }} allowFullScreen loading="lazy" referrerPolicy="no-referrer-when-downgrade" title="MK Health Clinic Location" />
              </div>
            </FadeInUp>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-surface-100 border-t border-surface-300 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="MK Health Clinic" className="w-10 h-10 rounded-lg object-contain" />
              <div><h1 className="font-display font-bold text-text-900 text-lg leading-none">MK Health Clinic</h1><p className="text-xs text-text-500">Jaipur, Rajasthan</p></div>
            </div>
            <div className="flex items-center gap-8 text-sm text-text-500 font-medium">
              <a href="#about" className="hover:text-primary-800 transition-colors">About</a>
              <a href="#testimonials" className="hover:text-primary-800 transition-colors">Reviews</a>
              <a href="#faq" className="hover:text-primary-800 transition-colors">FAQ</a>
              <a href="#location" className="hover:text-primary-800 transition-colors">Location</a>
            </div>
            <div className="text-text-400 text-sm">© 2026 MK Health Clinic. All rights reserved.</div>
          </div>
        </div>
      </footer>
    </div>
  )
}