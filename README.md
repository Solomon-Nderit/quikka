# Quikka

**Quikka** is a lightweight, mobile-first appointment booking and payment platform tailored for service providers in Kenya (starting with hairstylists). It enables customers to select a service, book a time slot, and pay seamlessly via M-Pesa or other mobile payment options.

---

## 🛠️ Tech Stack

* **Backend:** Python (FastAPI)
* **Frontend:** HTML, TailwindCSS, Vanilla JS (initially)
* **Database:** SQLite (dev) → PostgreSQL (prod)
* **Payment Integration:** M-Pesa Daraja API (later extensible to Stripe, PayPal)
* **Calendar Integration (optional):** Google Calendar or internal scheduling system
* **Deployment (later stage):** Railway or Render for backend, Netlify for frontend

---

## 🔧 Features (MVP Scope)

### Stylist Side:

* ✅ Create account
* ✅ Create service page (name, services offered, duration, price)
* ✅ Set availability (e.g. Mon–Fri, 10am–5pm)
* 🔄 Receive bookings
* 🔄 Get paid via M-Pesa (STK push)
* 🕓 View upcoming appointments

### Customer Side:

* ✅ Visit stylist link (e.g. `quikka.me/janehair`)
* ✅ Choose a service + available time
* ✅ Enter phone number
* 🔄 Pay via M-Pesa
* 🔄 Receive booking confirmation (on-screen + SMS optional)

---

```

---

## 🧪 Setup Guide (Local Dev)

### Requirements

* Python 3.10+
* Node.js + npm (if using build tools)
* Ngrok (for testing M-Pesa locally)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/quikka.git
cd quikka
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
```

### 2. Run Server

```bash
uvicorn app.main:app --reload
```

App will run on `http://127.0.0.1:8000`

### 3. Frontend

Pages will be served via Jinja2 templates for now. Later, we may separate into a React/Vue frontend.

---

## 🛣️ Roadmap

### Week 1 (DONE / IN PROGRESS)

* [x] Stylist Sign-up
* [x] Service creation form
* [x] Availability scheduler
* [ ] Booking logic
* [ ] M-Pesa sandbox integration

### Week 2

* [ ] Booking calendar + time validation
* [ ] Customer-side flow
* [ ] M-Pesa STK push

### Week 3

* [ ] SMS confirmation (Africa's Talking?)
* [ ] Add minimal dashboard for stylists
* [ ] Refactor codebase, add tests

### Week 4

* [ ] Polish UI + Tailwind
* [ ] Deploy to Netlify + Railway
* [ ] Write documentation
* [ ] Add Google Calendar support (if time permits)

---

## 🔐 Security Notes

* M-Pesa integration should use secure credentials in `.env`
* All STK pushes must be verified with callbacks
* No password storage: use hashed tokens or OAuth (future)

---

## 🙋🏽‍♂️ Contributors

* **Solomon Wahome** – Founder & Developer

---

## 📬 Contact / Feedback

For feedback, reach out via [Twitter](https://twitter.com/) or email: ``

---

## License

MIT License. See `LICENSE` file.
