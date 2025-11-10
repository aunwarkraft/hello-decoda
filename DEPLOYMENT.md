# Deployment Guide

This guide covers deploying the Healthcare Appointment Booking System to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
  - [Manual Deployment](#manual-deployment)
  - [Cloud Platform Deployment](#cloud-platform-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Production Checklist](#production-checklist)

---

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- OR Node.js 20+ and Python 3.11+ (for manual deployment)
- PostgreSQL (recommended for production) or SQLite (for development)
- Domain name and SSL certificate (for production)

---

## Deployment Options

### Docker Compose (Recommended)

The easiest way to deploy the entire application is using Docker Compose.

#### 1. Clone and Setup

```bash
git clone <repository-url>
cd hello-decoda
```

#### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your production values:

```env
# Frontend API URL
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api

# Backend Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/appointments
APP_ENV=production
TIMEZONE=America/Toronto

# CORS Origins
CORS_ORIGINS=["https://yourdomain.com"]
```

#### 3. Build and Start

```bash
# Build images
pnpm docker:build

# Start services
pnpm docker:up

# View logs
pnpm docker:logs
```

#### 4. Initialize Database

The database will be automatically initialized on first run. If you need to reinitialize:

```bash
docker-compose exec backend python __init__db.py
```

#### 5. Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Manual Deployment

#### Frontend Deployment

1. **Build the application:**

```bash
cd frontend
pnpm install
pnpm build
```

2. **Start production server:**

```bash
pnpm start
```

Or use a process manager like PM2:

```bash
pm2 start npm --name "decoda-frontend" -- start
```

3. **Serve with Nginx (recommended):**

Create an Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

#### Backend Deployment

1. **Setup Python environment:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your production values
```

3. **Initialize database:**

```bash
python __init__db.py
```

4. **Start with Gunicorn (recommended for production):**

First, add Gunicorn to `requirements.txt`:

```txt
gunicorn>=21.2.0
```

Then start:

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

Or use a process manager:

```bash
pm2 start "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000" --name "decoda-backend"
```

5. **Serve with Nginx:**

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### Cloud Platform Deployment

#### Vercel (Frontend)

1. Install Vercel CLI: `npm i -g vercel`
2. Deploy: `cd frontend && vercel`
3. Set environment variable: `NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api`

#### Railway / Render / Fly.io (Backend)

1. Connect your repository
2. Set environment variables:
   - `DATABASE_URL`
   - `CORS_ORIGINS`
   - `TIMEZONE`
   - `APP_ENV=production`
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### AWS / Google Cloud / Azure

Use containerized deployment with Docker Compose or Kubernetes. See the Docker Compose section above.

---

## Environment Configuration

### Frontend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://api.yourdomain.com/api` |

### Backend Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./appointments.db` | `postgresql://user:pass@host:5432/db` |
| `APP_ENV` | Application environment | `development` | `production` |
| `TIMEZONE` | Practice timezone | `America/Toronto` | `America/New_York` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000"]` | `["https://yourdomain.com"]` |

---

## Database Setup

### SQLite (Development)

SQLite is used by default. The database file is created automatically at `backend/appointments.db`.

### PostgreSQL (Production - Recommended)

1. **Install PostgreSQL:**

```bash
# Ubuntu/Debian
sudo apt-get install postgresql

# macOS
brew install postgresql
```

2. **Create database:**

```bash
createdb appointments
```

3. **Update DATABASE_URL:**

```env
DATABASE_URL=postgresql://username:password@localhost:5432/appointments
```

4. **Run migrations:**

```bash
cd backend
python __init__db.py
```

### Database Migrations

For production, consider using Alembic for database migrations:

```bash
pip install alembic
alembic init alembic
# Configure alembic.ini and create migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## Production Checklist

### Security

- [ ] Use HTTPS (SSL/TLS certificates)
- [ ] Set strong database passwords
- [ ] Configure CORS origins properly
- [ ] Enable rate limiting on API endpoints
- [ ] Use environment variables for secrets
- [ ] Enable security headers (HSTS, CSP, etc.)
- [ ] Regular security updates

### Performance

- [ ] Enable database connection pooling
- [ ] Configure caching (Redis recommended)
- [ ] Enable CDN for static assets
- [ ] Optimize database queries
- [ ] Monitor application performance

### Monitoring

- [ ] Set up application logging
- [ ] Configure error tracking (Sentry, etc.)
- [ ] Set up health checks
- [ ] Monitor database performance
- [ ] Set up uptime monitoring

### Backup

- [ ] Configure automated database backups
- [ ] Test backup restoration process
- [ ] Store backups in secure location
- [ ] Document recovery procedures

### Scaling

- [ ] Use load balancer for multiple instances
- [ ] Configure horizontal scaling
- [ ] Use managed database service
- [ ] Implement caching layer

---

## Troubleshooting

### Database Connection Issues

- Verify `DATABASE_URL` is correct
- Check database server is running
- Verify network connectivity
- Check firewall rules

### CORS Errors

- Verify `CORS_ORIGINS` includes your frontend domain
- Check for trailing slashes in URLs
- Ensure protocol matches (http vs https)

### Build Failures

- Check Node.js and Python versions
- Verify all dependencies are installed
- Check for environment variable issues
- Review build logs for specific errors

---

## Support

For issues or questions, please refer to the main README.md or open an issue in the repository.

