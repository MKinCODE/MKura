# MKura — Multi-Agent Healthcare Scheduling Assistant

A production-ready, AI-driven clinic booking system built for **MK Health Clinic**. The platform leverages a multi-agent architecture powered by LLMs to handle conversational appointment booking, automated waitlist management, dynamic slot upgradation, and email notifications. The core AI system, **MKura**, seamlessly manages patient inquiries and scheduling.

## Features

### Patient Experience
- **AI Chat Agent**: Natural conversation to collect patient details (name, email, phone)
- **Earliest Slot Booking**: Automatically finds the earliest available appointment
- **Smart Lead Time**: 1-hour minimum booking window ensures patients can reach the clinic
- **Payment Integration**: Stripe test mode for ₹100 refundable deposit
- **Email Notifications**: Confirmation, reminders, and cancellation emails
- **Cancellation Portal**: Token-based secure cancellation with instant email confirmation

### Doctor Experience
- **Dashboard**: View all bookings and slots for the next 7 days
- **Emergency Blocking**: Block slots with existing bookings - system auto-reschedules patients
- **Real-time Updates**: Instant email notifications to affected patients

### Upgradation System
- **Waitlist Interest**: Patients can opt-in to waitlist during booking
- **Auto-Upgrade**: When someone cancels, the slot is offered to waitlist patients (FIFO)
- **15-Minute Timeout**: Patients have 15 minutes to accept the upgraded slot
- **Chain Continuation**: If declined/expired, offer goes to next patient until slot is filled

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI (Python 3.11) |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7 |
| AI/NLP | Custom entity extraction + Groq API (LLM) |
| Email | SMTP (aiosmtplib) |
| Payment | Stripe Test Mode |
| Auth | JWT (Access + Refresh tokens) |

## Project Structure

```
clinic-scheduler/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage/    # Landing page with doctor info
│   │   │   ├── ChatAgent/      # Chat popup and payment modal
│   │   │   ├── CancellationPage/
│   │   │   ├── DoctorDashboard/
│   │   │   └── ui/
│   │   ├── pages/
│   │   └── services/           # API integration
│   └── ...
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   ├── agents/             # Booking & Upgradation agents
│   │   ├── core/               # Config, security, rate limiting
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Email, payment, slot services
│   │   └── main.py
│   ├── requirements.txt
│   └── seed_data.py            # Demo data seeder
├── docker-compose.yml           # Full stack setup
└── README.md
```

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development without Docker)
- Python 3.11+ (for backend development without Docker)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd clinic-scheduler

# Create backend .env file
cp backend/.env.example backend/.env
```

### 2. Configure Environment Variables

Edit `backend/.env` with your values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/clinic_db
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/clinic_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (generate a new secret key)
SECRET_KEY=your-super-secret-key-minimum-32-characters

# Groq AI (get free API key from https://console.groq.com)
GROQ_API_KEY=your_groq_api_key

# Stripe (get test keys from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email (use Gmail App Password or other SMTP provider)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Frontend URL (for email links)
CLIENT_URL=http://localhost:3000
```

### 3. Start with Docker

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Initialize database and seed demo data
docker-compose exec backend python -m app.seed_data
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Demo Credentials

**Doctor Login:**
- Email: `dr.mehta@mkhealth.com`
- Password: `doctor123`

**Stripe Test Card:**
- Number: `4242 4242 4242 4242`
- Expiry: Any future date
- CVC: Any 3 digits

## Manual Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (or use Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=clinic_db postgres:15
docker run -d -p 6379:6379 redis:7

# Run database migrations and seed
python -m app.seed_data

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Deployment Guide

### Option 1: Railway (Recommended for Resume Projects)

**Backend Deployment:**

1. Create a new Railway project
2. Add PostgreSQL plugin
3. Add Redis plugin
4. Deploy from GitHub (backend folder)
5. Set environment variables in Railway dashboard
6. Run seed command: `python -m app.seed_data`

**Frontend Deployment:**

1. Create a new Railway project
2. Deploy from GitHub (frontend folder)
3. Set environment variable: `VITE_API_URL=https://your-backend-url.railway.app`

**Stripe Webhook (for production):**
```bash
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

### Option 2: Render

1. **Backend**:
   - Create Web Service
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add PostgreSQL and Redis from Render marketplace

2. **Frontend**:
   - Create Static Site
   - Build command: `npm install && npm run build`
   - Output directory: `dist`

### Option 3: Vercel + Railway/Render

**Frontend (Vercel):**
```bash
cd frontend
npm install -g vercel
vercel --prod
```

Set `VITE_API_URL` to your backend URL in Vercel dashboard.

### Option 4: Docker + VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com | sh

# Clone and setup
git clone <your-repo-url>
cd clinic-scheduler

# Create .env file with production values

# Run with Docker Compose
docker-compose -f docker-compose.yml up -d

# Setup Nginx reverse proxy (optional)
sudo apt install nginx
sudo nano /etc/nginx/sites-available/clinic
```

Nginx config example:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

## Required Services Setup

### Stripe Setup
1. Create account at https://stripe.com
2. Get API keys from Developers > API keys
3. For webhooks, use Stripe CLI:
   ```bash
   stripe login
   stripe listen --forward-to localhost:8000/api/webhooks/stripe
   ```

### Groq AI Setup
1. Sign up at https://console.groq.com
2. Create API key in console
3. Free tier includes 30 requests/minute

### Gmail SMTP Setup
1. Enable 2-Factor Authentication on your Google account
2. Generate App Password: Google Account > Security > App Passwords
3. Use the 16-character app password as `SMTP_PASSWORD`

### Alternative Email Providers

**SendGrid:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

**Mailgun:**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain
SMTP_PASSWORD=your_mailgun_password
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Doctor authentication |
| GET | `/api/chat/slots/earliest` | Get earliest available slot |
| POST | `/api/chat/message` | Chat agent message |
| POST | `/api/bookings/create` | Create booking |
| GET | `/api/bookings/{id}/cancel/{token}` | Validate cancellation |
| POST | `/api/bookings/{id}/cancel/{token}` | Cancel booking |
| GET | `/api/slots/available` | Get available slots |
| POST | `/api/slots/block` | Block slot (emergency) |
| GET | `/api/bookings/doctor/all` | Doctor's bookings |
| GET | `/api/bookings/doctor/slots` | Doctor's slots |

## Business Rules

| Rule | Value |
|------|-------|
| Minimum Lead Time | 1 hour from current time |
| Clinic Hours | 9:00 AM - 6:00 PM |
| Same-Day Cutoff | 5:00 PM |
| Slot Duration | 20 minutes |
| Waitlist Upgrade Timeout | 15 minutes |
| Payment Amount | ₹100 (refundable) |

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend python -m app.seed_data
```

### Chat Agent Not Responding
1. Check Groq API key is set correctly
2. Check backend logs: `docker-compose logs backend`
3. Verify rate limiting not triggered

### Emails Not Sending
1. Verify SMTP credentials
2. Check if less secure app access is enabled (for Gmail)
3. Use app password instead of regular password (Gmail)

### Stripe Payment Issues
1. Verify test mode keys are used (not live keys)
2. Check Stripe webhook is configured
3. Check browser console for CORS errors

## Future Enhancements

- [ ] Multi-doctor support
- [ ] WhatsApp integration
- [ ] SMS notifications
- [ ] Google Calendar sync
- [ ] Patient accounts with booking history
- [ ] Admin panel for managing doctors
- [ ] Analytics dashboard
- [ ] Recurring appointments
- [ ] Video consultation integration

## License

MIT License - Feel free to use for your portfolio/resume!

## Support

For questions or issues, please open an issue on GitHub.