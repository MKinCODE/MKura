# MKura 🩺 — Multi-Agent AI Healthcare Scheduling Platform

**MKura** is an enterprise-grade, conversation-driven healthcare scheduling platform designed to automate patient booking lifecycles, waitlist optimizations, and doctor-side operations. By leveraging a **Multi-Agent AI architecture** powered by high-frequency LLMs, the platform removes administrative friction, eliminates empty booking slots, and provides a premium patient-centric care portal.

---

## 🚀 Architectural & Engineering Highlights

This project is built using modern software engineering patterns designed for high throughput, low latency, and robust state consistency:

### 1. Autonomous Multi-Agent AI Orchestration
*   **Booking Agent**: A conversation-driven assistant utilizing the sub-second **Groq API (Llama 3)**. Instead of traditional static web forms, it uses structured natural language processing (**Intent Classifier + Entity Extractor**) to organically extract patient metadata (name, email, phone) and recommend the earliest available appointment slots.
*   **Upgradation Agent**: An asynchronous state coordinator running a **First-In-First-Out (FIFO) waitlist queue**. When a booking is cancelled, it holds the slot, locks it from general availability, and extends a 15-minute priority upgrade offer via a secure, tokenized link to the next patient in line. If ignored or rejected, it automatically cascades the offer to subsequent candidates.

### 2. Event-Driven Doctor Operations
*   **Emergency Slot Blocking**: If a doctor experiences an emergency and blocks a slot, the system automatically triggers an event-driven rescheduling pipeline. Impacted patients are notified immediately with customizable rescheduling actions, keeping clinical calendars fluid without administrative overhead.
*   **Real-time Calendar Board**: A 7-day responsive grid visualization showing patient status, slot states (available, booked, waitlisted, blocked), and automatic day-to-day schedule rolling.

### 3. Integrated Email & Transient State Controls
*   **Gmail REST API Integration**: Bypasses typical SMTP port blocks on cloud providers by interacting directly with the Gmail API via Google OAuth2 token refreshing. Dispatches confirmation, cancellation, and waitlist priority upgrade links securely.
*   **Simulated Demo Payment Lifecycle**: Replaced heavy external SDK dependencies with a modular, lightweight simulated checkout drawer. The checkout processes a ₹100 deposit with realistic transitions, and securely resumes the booking chat session on completion.
*   **Concurrency & Booking Safeguards**: Implements a strict **1-hour minimum lead-time constraint** to prevent short-notice doctor disruptions. Automatically enforces hard boundaries by filtering out past-date slots and expired same-day times across all endpoints.

---

## 📊 System Architecture & Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Patient as Patient (Web UI)
    participant Chat as AI Chat Agent (Groq)
    participant DB as PostgreSQL (DB)
    participant UpStash as Redis (Cache/Rate-Limits)
    participant Gmail as Gmail REST API
    actor Doctor as Doctor Portal

    Patient->>Chat: "Book a slot for tomorrow morning"
    Chat->>UpStash: Check Rate-Limiting & Session State
    Chat->>DB: Query Available Slots (Batched Optimization)
    DB-->>Chat: Returns Available Slots
    Chat-->>Patient: Proposes slot + triggers Booking Checkout
    Patient->>Patient: Submits simulated ₹100 payment
    Patient->>DB: Persists Booking (Status: Confirmed)
    DB-->>Gmail: Dispatch OAuth2 fresh tokenized confirmation email
    Gmail-->>Patient: Email received with cancellation & reschedule link
    
    Note over Doctor, DB: If Doctor blocks slot due to emergency:
    Doctor->>DB: Block Slot (Trigger reassignment)
    DB->>DB: Cascades bookings to next available slots
    DB-->>Gmail: Dispatch rescheduling alerts to affected patients
```

---

## 🛠️ Advanced Tech Stack & Rationale

| Layer | Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Frontend Framework** | `React 18` + `TypeScript` + `Vite` | Fast bundler speeds, strict type-safety across components, and optimized production asset compiling. |
| **Styling & UI** | `Tailwind CSS` + `Framer Motion` | Modern glassmorphism themes, customized HSL color palette, and physics-based micro-animations for premium visual feedback. |
| **Backend API** | `FastAPI (Python 3.11)` | Asynchronous ASGI framework providing native dependency injection, automatic Pydantic validation, and high-performance throughput. |
| **Database ORM** | `PostgreSQL 15` + `SQLAlchemy (Asyncio)` | Robust relational storage with asynchronous engine execution, ensuring non-blocking PostgreSQL connection pooling. |
| **Cache & Middleware** | `Redis 7` | Ultra-fast key-value store handling low-latency API rate-limiting and session synchronization. |
| **Generative AI** | `Groq SDK (Llama 3 70B)` | Sub-second inference latency, allowing natural conversational flows and seamless token extraction. |
| **Transactional Email** | `Gmail REST API (Google Cloud OAuth2)` | Modern RESTful email delivery that bypasses port 587/465 blocks common on cloud hosts (e.g. Render). |

---

## 📂 Project Structure

```
Multi-agent-clinic-scheduler/
├── backend/                         # FastAPI Application Service
│   ├── app/
│   │   ├── api/                     # REST API Controllers & Dependencies
│   │   │   ├── routes/              # Auth, Bookings, Slots, and Chat router endpoints
│   │   │   └── deps.py              # Auth middleware & Database session injectors
│   │   ├── agents/                  # Intelligent AI Agents layer
│   │   │   ├── nlp/                 # Entity Extractor & Intent Classifier services
│   │   │   ├── booking_agent.py     # Dialogue state and scheduling AI agent
│   │   │   └── upgradation_agent.py # Queue parser and FIFO waitlist scheduler
│   │   ├── core/                    # App configurations, secrets, and Redis rate limiters
│   │   ├── models/                  # Database relational models (Doctor, Slot, Booking, Waitlist)
│   │   ├── schemas/                 # Strongly-typed input/output Pydantic structures
│   │   ├── services/                # Asynchronous helper services (Gmail REST API, Slot seeder)
│   │   └── main.py                  # Lifespan initializer, CORS, and /health route
│   ├── requirements.txt             # Python backend dependencies manifest
│   └── seed_data.py                 # Seeds clinic calendar and default Doctor accounts
├── frontend/                        # React Frontend Application
│   ├── src/
│   │   ├── components/              # Modular shared UI assets
│   │   │   └── ChatAgent/           # Frosted glass AI chat agent overlay and Payment drawer
│   │   ├── pages/                   # Main Page Views
│   │   │   ├── Landing.tsx          # Premium landing page featuring coverflow carousel and chat modal trigger
│   │   │   ├── DoctorLogin.tsx      # Multi-factor-styled Doctor credential page
│   │   │   ├── DoctorDashboard.tsx  # Interactive 7-day doctor grid with slot-blocking action
│   │   │   └── Cancellation.tsx     # Direct, tokenized client cancellation portal
│   │   ├── services/                # Axios-configured API clients
│   │   ├── index.css                # Custom global utility tokens and fonts
│   │   └── App.tsx                  # Client router configurations
│   └── package.json                 # Frontend dependencies and bundler configurations
├── docker-compose.yml               # Production-like multi-container orchestrator
└── README.md                        # Project documentation
```

---

## 📈 Clinic Business Rules & Thresholds

| Standard Rule | Set Value | Purpose |
| :--- | :--- | :--- |
| **Clinic Operating Hours** | `9:00 AM - 6:00 PM` | Defines clinic scheduling boundary windows. |
| **Default Appointment Duration**| `20 Minutes` | Maximum length allocated per patient booking. |
| **Minimum Booking Lead Time** | `1 Hour` | Enforces clinical buffer windows (prevents immediate walk-ins). |
| **Same-Day Slot Booking Cutoff** | `5:00 PM` | Prevents late-afternoon bookings from scheduling on the same day. |
| **Waitlist Upgrade Hold Timer** | `15 Minutes` | The amount of time a waitlisted patient has to claim an upgrade. |
| **Simulated Payment Amount** | `₹100` | Refundable booking token used in the demo mode modal. |

---

## 🔧 Environment Configuration & Setup

### 1. Gmail API OAuth2 Credentials Setup
Since this platform uses the **Gmail REST API**, you need to generate Google OAuth2 credentials:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and search for **Gmail API**, then click **Enable**.
3. Go to the **OAuth Consent Screen** tab, select **External**, and set up your app credentials. Add your sender email as a **Test User** (since your app will be in testing mode).
4. Go to **Credentials**, click **Create Credentials** -> **OAuth Client ID**, select **Web Application**.
5. Under **Authorized Redirect URIs**, enter `https://developers.google.com/oauthplayground` (useful for retrieving the refresh token easily). Save and note your `Client ID` and `Client Secret`.
6. Navigate to [Google OAuth Playground](https://developers.google.com/oauthplayground):
   * Click the settings gear (top right), check **Use your own OAuth credentials**, and paste your `Client ID` and `Client Secret`.
   * Under step 1, select the scope `https://www.googleapis.com/auth/gmail.send` and click **Authorize APIs**.
   * Sign in with your Google Test User account and approve permissions.
   * Under step 2, click **Exchange authorization code for tokens** to copy the generated **Refresh Token**.

### 2. Setting up local `.env` files
Create a `.env` file in `/backend` using the variables below:
```env
APP_NAME="MK Health Clinic API"
DEBUG=True
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/clinic_db"
DATABASE_URL_SYNC="postgresql://postgres:postgres@localhost:5432/clinic_db"
REDIS_URL="redis://localhost:6379/0"
SECRET_KEY="your-super-secret-key-make-it-long-in-prod"
CLIENT_URL="http://localhost:3000"

# Groq API Key for AI scheduling agent
GROQ_API_KEY="your_groq_api_key"

# Gmail REST API OAuth2 Configurations
GMAIL_CLIENT_ID="your_google_client_id"
GMAIL_CLIENT_SECRET="your_google_client_secret"
GMAIL_REFRESH_TOKEN="your_google_refresh_token"
GMAIL_SENDER_EMAIL="your_sender_gmail_account@gmail.com"

# Seeding configurations
SEED_DOCTOR_EMAIL="mousam1234@mkhealth.com"
SEED_DOCTOR_PASSWORD="doctor123"
```

Create a `.env` file in `/frontend`:
```env
VITE_API_URL="http://localhost:8000"
```

---

## ⚡ Running Locally

### Option A: Quick-start using Docker Compose (Recommended)
Make sure you have Docker installed, then run the following command in the root folder:
```bash
docker-compose up --build
```
This single command spins up PostgreSQL, Redis, the FastAPI backend (port `8000`), and the React frontend (port `3000`), automatically running database migrations and seeding the default doctor slots on startup.

### Option B: Running Manually

#### 1. Database & Cache Services
Ensure you have local instances of **PostgreSQL** (with database name `clinic_db`) and **Redis** running on their default ports (`5432` and `6379`).

#### 2. Start the Backend API
```bash
cd backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python seed_data.py # Seed doctors, weekly schedules, and calendar slots
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. Start the Frontend client
```bash
cd frontend
npm install
npm run dev
```

---

## 🔌 Render Deployment & Hosting Optimizations

When deploying the application to **Render's Free Tier**, two main limitations arise: cold starts and execution timeouts due to heavily throttled database transaction loops. The following solutions are built into this repository:

### 1. Eliminating Cold Starts (Keep Awake Ping)
Render's free web service spins down after 15 minutes of inactivity, causing the first visitor to wait 50–120 seconds for the app to wake up.
* **Solution**: The backend exposes a lightweight, database-free, fast-responding `/health` check.
* **Action**: Configure a free account on [Cron-Job.org](https://cron-job.org/) to hit your deployed backend URL: `https://your-backend-name.onrender.com/health` every **10 to 12 minutes**. Since it bypasses SQL queries, it wakes the server instantly with zero overhead.

### 2. High-Performance Query Optimization
On Render's CPU-throttled containers, running database operations inside loops chokes FastAPI's event loop. 
* **Refactoring details**: The slot retrieval code batches doctor details once per call and restricts slot cleanups to run once at the initiation of requests rather than inside day-by-day nested iteration loops. This reduces query complexity from $O(N)$ database round-trips to $O(1)$ batched requests, preventing API Gateway Timeouts (504).

---


## ⚖️ License
Distributed under the **MIT License**. Feel free to use this system to showcase multi-agent orchestration, clean coding architectures, or modern responsive web interfaces in your portfolios!