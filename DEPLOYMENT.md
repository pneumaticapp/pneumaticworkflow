# Quick Deployment Guide

## Prerequisites
- Docker version 2.27 or above
- Docker compose version 27.0 or above

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/pneumaticapp/pneumaticworkflow.git
   cd pneumaticworkflow
   ```

2. **Configure environment**
   ```bash
   cp pneumatic.env.example pneumatic.env
   # Edit pneumatic.env if needed
   ```

3. **Start the application**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - Main Application: http://localhost
   - API: http://localhost:8001
   - Forms: http://localhost:8002
   - RabbitMQ Management: http://localhost:15672

## Ports Used
- **80**: Main application (frontend)
- **8001**: API backend
- **8002**: Forms
- **15672**: RabbitMQ management interface
- **5432**: PostgreSQL (optional, for external access)
- **6379**: Redis (optional, for external access)

## Environment Variables
All configuration is done through the `pneumatic.env` file. Key variables:

- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password
- `RABBITMQ_PASSWORD`: RabbitMQ password
- `DJANGO_SECRET_KEY`: Django secret key (change in production)

## Production Deployment
For production deployment:
1. Change default passwords in `pneumatic.env`
2. Set `SSL=yes` for HTTPS
3. Configure proper domain names
4. Set up SSL certificates
5. Configure email settings

## Troubleshooting
- Check container logs: `docker compose logs [service-name]`
- Restart services: `docker compose restart [service-name]`
- Full restart: `docker compose down && docker compose up -d`

