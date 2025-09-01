# Troubleshooting Guide

## Common Issues and Solutions

### 1. Redis Connection Issues

**Problem**: Redis fails to start with "wrong number of arguments" error
```
*** FATAL CONFIG FILE ERROR (Redis 6.2.6) ***
>>> 'requirepass'
wrong number of arguments
```

**Solution**: 
- Redis command is now hardcoded in docker-compose.yml
- Restart containers: `docker compose down && docker compose up -d`

### 2. RabbitMQ Authentication Issues

**Problem**: Celery cannot connect to RabbitMQ
```
ACCESS_REFUSED - Login was refused using authentication mechanism PLAIN
```

**Solution**:
- RabbitMQ credentials are now hardcoded in docker-compose.yml
- Check RabbitMQ logs: `docker compose logs rabbitmq`
- Restart containers: `docker compose down && docker compose up -d`

### 3. Celery Worker Issues

**Problem**: Celery worker fails to start with UID error
```
KeyError: 'getpwuid(): uid not found: 1000'
```

**Solution**:
- Removed `--uid=1000 --gid=1000` flags from Celery commands
- Celery now runs as root user (acceptable in Docker containers)
- This is the standard approach for Docker deployments

### 4. Service Startup Order

**Problem**: Services start before dependencies are ready
```
dependency failed to start: container pneumatic-postgres has no healthcheck configured
```

**Solution**:
- Added healthchecks for all services (PostgreSQL, Redis, RabbitMQ, Backend, Frontend)
- Updated `depends_on` to use health conditions
- Services now wait for dependencies to be healthy
- PostgreSQL healthcheck uses `pg_isready` command
- Backend healthcheck uses Django's `check --deploy` command
- Frontend healthcheck verifies PM2 process is running

## Debugging Commands

### Check Service Status
```bash
# View all containers
docker compose ps

# Check specific service logs
docker compose logs redis
docker compose logs rabbitmq
docker compose logs celery
docker compose logs pneumatic-backend
```

### Restart Services
```bash
# Restart specific service
docker compose restart redis
docker compose restart rabbitmq
docker compose restart celery

# Restart all services
docker compose down && docker compose up -d
```

### Check Health Status
```bash
# Check if services are healthy
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

### Access Service Shells
```bash
# Access Redis CLI
docker compose exec redis redis-cli -a redis_password

# Access RabbitMQ management
# Open http://localhost:15672 in browser
# Username: rabbitmq_user
# Password: rabbitmq_password

# Access PostgreSQL
docker compose exec postgres psql -U postgres_user -d postgres_db
```

## Environment Variables

### Current Configuration
- **Redis Password**: `redis_password` (hardcoded)
- **RabbitMQ User**: `rabbitmq_user` (hardcoded)
- **RabbitMQ Password**: `rabbitmq_password` (hardcoded)
- **PostgreSQL User**: `postgres_user` (from env file)
- **PostgreSQL Password**: `postgres_password` (from env file)

### Customizing Credentials
To change credentials, edit the `docker-compose.yml` file:

```yaml
# Redis
command: redis-server --loglevel warning --databases 16 --dbfilename dump.rdb --dir /data --requirepass YOUR_REDIS_PASSWORD --save 20 1 300 100 60 10000

# RabbitMQ
environment:
  - RABBITMQ_DEFAULT_USER=YOUR_RABBITMQ_USER
  - RABBITMQ_DEFAULT_PASS=YOUR_RABBITMQ_PASSWORD
```

## Performance Issues

### High Memory Usage
```bash
# Check container resource usage
docker stats

# Restart memory-intensive services
docker compose restart pneumatic-backend
docker compose restart celery
```

### Slow Startup
```bash
# Check startup times
docker compose logs --timestamps

# Optimize by increasing healthcheck intervals
# Edit docker-compose.yml healthcheck sections
```

## Network Issues

### Port Conflicts
```bash
# Check if ports are in use
netstat -tulpn | grep :80
netstat -tulpn | grep :8001
netstat -tulpn | grep :8002

# Change ports in docker-compose.yml if needed
```

### DNS Issues
```bash
# Test internal DNS resolution
docker compose exec pneumatic-backend ping rabbitmq
docker compose exec pneumatic-backend ping redis
docker compose exec pneumatic-backend ping postgres
```

## Data Persistence

### Backup Data
```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U postgres_user postgres_db > backup.sql

# Backup Redis (if needed)
docker compose exec redis redis-cli -a redis_password BGSAVE
```

### Reset Data
```bash
# Remove all data volumes
docker compose down -v
docker compose up -d
```

## Log Analysis

### Common Log Patterns

**Redis Ready**:
```
Ready to accept connections
```

**RabbitMQ Ready**:
```
Server startup complete
```

**Celery Ready**:
```
celery@hostname ready
```

**Django Ready**:
```
Starting development server
```

### Log Levels
- **ERROR**: Critical issues requiring immediate attention
- **WARNING**: Issues that don't prevent operation
- **INFO**: General operational information
- **DEBUG**: Detailed debugging information

## Getting Help

1. **Check logs first**: `docker compose logs [service-name]`
2. **Restart services**: `docker compose restart [service-name]`
3. **Full restart**: `docker compose down && docker compose up -d`
4. **Check health**: `docker compose ps`
5. **Verify configuration**: Check `docker-compose.yml` and `pneumatic.env`

For persistent issues, check:
- Docker version compatibility
- Available system resources
- Network connectivity
- File permissions
