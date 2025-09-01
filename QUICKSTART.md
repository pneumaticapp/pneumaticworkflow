# Quick Start Guide

## 🚀 One-Command Deployment

```bash
# 1. Clone the repository
git clone https://github.com/pneumaticapp/pneumaticworkflow.git
cd pneumaticworkflow

# 2. Copy environment file
cp pneumatic.env.example pneumatic.env

# 3. Start the application
docker compose up -d
```

## 🌐 Access the Application

Once containers are running, access:

- **Main App**: http://localhost
- **API**: http://localhost:8001  
- **Forms**: http://localhost:8002
- **RabbitMQ Admin**: http://localhost:15672

## 📋 What's Included

- **Backend**: Django REST API
- **Frontend**: React application
- **Database**: PostgreSQL
- **Cache**: Redis
- **Message Queue**: RabbitMQ
- **Web Server**: Nginx
- **Task Queue**: Celery

## 🔧 Configuration

Edit `pneumatic.env` to customize:
- Database passwords
- Email settings
- Feature toggles
- Domain settings

## 🛠️ Management Commands

```bash
# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop application
docker compose down

# Update and restart
docker compose pull && docker compose up -d
```

## 🐛 Troubleshooting

```bash
# Check container status
docker compose ps

# View specific service logs
docker compose logs pneumatic-backend

# Restart specific service
docker compose restart pneumatic-backend
```

## 📚 Next Steps

- [Full Documentation](DEPLOYMENT.md)
- [Docker Build Guide](DOCKER_BUILD.md)
- [Support Center](https://support.pneumatic.app/en/)

---

**Need help?** Check the [troubleshooting section](DEPLOYMENT.md#troubleshooting) or open an issue on GitHub.

