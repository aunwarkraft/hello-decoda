# Quick Deployment Guide

This is a quick reference guide for deploying the Healthcare Appointment Booking System.

## 🚀 Quick Start with Docker Compose

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your production values
# - NEXT_PUBLIC_API_URL: Your backend API URL
# - DATABASE_URL: Your database connection string
# - CORS_ORIGINS: Your frontend domain(s) as JSON array
```

### 2. Deploy

```bash
# Build and start all services
pnpm docker:build
pnpm docker:up

# View logs
pnpm docker:logs

# Stop services
pnpm docker:down
```

### 3. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 📋 Environment Variables

### Frontend (.env in root)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Backend (backend/.env)

```env
DATABASE_URL=sqlite:///./appointments.db
APP_ENV=production
TIMEZONE=America/Toronto
CORS_ORIGINS=["http://localhost:3000"]
```

**Note**: `CORS_ORIGINS` can be:
- JSON array: `["https://yourdomain.com"]`
- Comma-separated: `https://yourdomain.com,https://www.yourdomain.com`

---

## 🐳 Docker Commands

```bash
# Build images
pnpm docker:build

# Start services (detached)
pnpm docker:up

# Stop services
pnpm docker:down

# View logs
pnpm docker:logs

# Restart services
pnpm docker:restart

# Rebuild and restart
pnpm docker:build && pnpm docker:up -d
```

---

## 🔧 Manual Deployment

### Frontend

```bash
cd frontend
pnpm install
pnpm build
pnpm start
```

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
python __init__db.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## ☁️ Cloud Deployment

### Vercel (Frontend)

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `cd frontend && vercel`
3. Set `NEXT_PUBLIC_API_URL` in Vercel dashboard

### Railway / Render (Backend)

1. Connect repository
2. Set environment variables:
   - `DATABASE_URL`
   - `CORS_ORIGINS`
   - `TIMEZONE`
   - `APP_ENV=production`
3. Deploy

---

## 📚 Full Documentation

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

