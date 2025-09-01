[![Documentation](https://img.shields.io/badge/docs-support.pneumatic.app-blue)](https://support.pneumatic.app/en/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://hub.docker.com/)
[![Status](https://img.shields.io/badge/status-tested%20%26%20working-green)]()

<img width="1000" alt="Pneumatic Workflow" src="https://github.com/user-attachments/assets/57e9d9df-24bf-42fe-a843-6f9c9b00bfac">

# Pneumatic Workflow - Single File Deployment
# Pneumatic Workflow - Развертывание одним файлом

**English** | [Русский](#русский)

---

## 🇺🇸 English

### About Pneumatic

**Pneumatic** is an open-source SaaS workflow management system designed to streamline and organize workflows in businesses of any size. Originally developed as a cloud-based platform, Pneumatic empowers teams by enabling them to set up, run, and optimize workflows collaboratively, tracking each stage as tasks move from team to team.

[:tv: Product Overview (< 5 min)](https://www.youtube.com/watch?v=GC67ocuOFfE)

### Key Features

- **Workflow Templates:** Create custom workflow templates and reuse them for repetitive processes
- **Multi-Workflow Management:** Run multiple workflows in parallel, adapting them as needed
- **Task Buckets for Staff:** Individual task management with personal task buckets
- **Automated Workflow Tracking:** Real-time insight into workflow stages with automated handoffs

### Quick Start with Docker Hub Images

This directory contains a single-file deployment configuration using pre-built Docker Hub images.

#### Prerequisites

- Docker version 2.27 or above
- Docker Compose version 27.0 or above
- 4GB RAM minimum (8GB recommended)

#### Automatic Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/pneumaticapp/pneumaticworkflow.git

# Navigate to deployment directory
cd pneumaticworkflow/single-file-deployment

# Run automatic setup script
./start.sh
```

#### Manual Setup

```bash
# 1. Navigate to deployment directory
cd single-file-deployment

# 2. Create required directories
mkdir -p logs/nginx www staticfiles

# 3. Start the application
docker compose up -d

# 4. Check status
docker compose ps
```

#### Access the Application

After successful startup:

- **Main Application**: http://localhost (redirects to /auth/signin/)
- **API Direct**: http://localhost:8001
- **Forms**: http://localhost:8002
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

#### Management Commands

```bash
# Automatic shutdown
./stop.sh

# Manual shutdown
docker compose down

# Restart specific service
docker compose restart pneumatic-backend

# View logs
docker compose logs -f

# Update images and restart
docker compose pull
docker compose up -d
```

### Configuration

All settings are in the `pneumatic.env` file. Key parameters:

- **Database**: PostgreSQL with named volume
- **Cache**: Redis with password
- **Queues**: RabbitMQ with user and password
- **Frontend**: React application with PM2
- **Backend**: Django with Celery worker and beat

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (Django)      │◄──►│   (PostgreSQL)  │
│   Port: 8000    │    │   Port: 6000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Nginx       │
                    │   (Reverse      │
                    │    Proxy)       │
                    │   Port: 80      │
                    └─────────────────┘
                                 ▲
                                 │
                    ┌─────────────────┐
                    │     Client      │
                    │   (Browser)     │
                    └─────────────────┘
```

### Troubleshooting

#### Services not starting
```bash
# Check logs
docker compose logs

# Check status
docker compose ps
```

#### Insufficient memory
```bash
# Increase Docker Desktop limits
# Or reduce NODE_OPTIONS in pneumatic.env
```

#### Port conflicts
```bash
# Change ports in docker-compose.yml
# Or stop other services
```

### Security

⚠️ **Important**: This is a development configuration. For production:

1. Change all passwords in `pneumatic.env`
2. Configure SSL certificates
3. Use external database
4. Set up backups
5. Add monitoring

### Documentation

For more detailed information about Pneumatic features, visit the [Pneumatic Support Center](https://support.pneumatic.app/en/)

### License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](../LICENSE) file for details.

---

## 🇷🇺 Русский

### О Pneumatic

**Pneumatic** - это система управления рабочими процессами с открытым исходным кодом, разработанная для оптимизации и организации рабочих процессов в компаниях любого размера. Изначально разработанная как облачная платформа, Pneumatic позволяет командам совместно настраивать, запускать и оптимизировать рабочие процессы, отслеживая каждый этап по мере продвижения задач от команды к команде.

[:tv: Обзор продукта (< 5 мин)](https://www.youtube.com/watch?v=GC67ocuOFfE)

### Ключевые возможности

- **Шаблоны рабочих процессов:** Создавайте пользовательские шаблоны и используйте их для повторяющихся процессов
- **Управление множественными процессами:** Запускайте несколько процессов параллельно, адаптируя их по необходимости
- **Ведра задач для сотрудников:** Индивидуальное управление задачами с персональными ведрами задач
- **Автоматическое отслеживание:** Отслеживание в реальном времени с автоматической передачей между командами

### Быстрый старт с образами Docker Hub

Этот каталог содержит конфигурацию развертывания одним файлом с использованием готовых образов Docker Hub.

#### Требования

- Docker версии 2.27 или выше
- Docker Compose версии 27.0 или выше
- Минимум 4GB RAM (рекомендуется 8GB)

#### Автоматическая настройка (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/pneumaticapp/pneumaticworkflow.git

# Перейдите в папку развертывания
cd pneumaticworkflow/single-file-deployment

# Запустите автоматический скрипт
./start.sh
```

#### Ручная настройка

```bash
# 1. Перейдите в папку развертывания
cd single-file-deployment

# 2. Создайте необходимые директории
mkdir -p logs/nginx www staticfiles

# 3. Запустите приложение
docker compose up -d

# 4. Проверьте статус
docker compose ps
```

#### Доступ к приложению

После успешного запуска:

- **Основное приложение**: http://localhost (перенаправляет на /auth/signin/)
- **API напрямую**: http://localhost:8001
- **Формы**: http://localhost:8002
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)

#### Команды управления

```bash
# Автоматическая остановка
./stop.sh

# Ручная остановка
docker compose down

# Перезапуск конкретного сервиса
docker compose restart pneumatic-backend

# Просмотр логов
docker compose logs -f

# Обновление образов и перезапуск
docker compose pull
docker compose up -d
```

### Конфигурация

Все настройки находятся в файле `pneumatic.env`. Основные параметры:

- **База данных**: PostgreSQL с именованным томом
- **Кэш**: Redis с паролем
- **Очереди**: RabbitMQ с пользователем и паролем
- **Фронтенд**: React приложение с PM2
- **Бэкенд**: Django с Celery worker и beat

### Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React)       │◄──►│   (Django)      │◄──►│   (PostgreSQL)  │
│   Port: 8000    │    │   Port: 6000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Nginx       │
                    │   (Reverse      │
                    │    Proxy)       │
                    │   Port: 80      │
                    └─────────────────┘
                                 ▲
                                 │
                    ┌─────────────────┐
                    │     Client      │
                    │   (Browser)     │
                    └─────────────────┘
```

### Устранение неполадок

#### Сервисы не запускаются
```bash
# Проверьте логи
docker compose logs

# Проверьте статус
docker compose ps
```

#### Недостаточно памяти
```bash
# Увеличьте лимиты Docker Desktop
# Или уменьшите NODE_OPTIONS в pneumatic.env
```

#### Конфликты портов
```bash
# Измените порты в docker-compose.yml
# Или остановите другие сервисы
```

### Безопасность

⚠️ **Важно**: Это конфигурация для разработки. Для продакшена:

1. Измените все пароли в `pneumatic.env`
2. Настройте SSL сертификаты
3. Используйте внешнюю базу данных
4. Настройте бэкапы
5. Добавьте мониторинг

### Документация

Для более подробной информации о возможностях Pneumatic посетите [Центр поддержки Pneumatic](https://support.pneumatic.app/en/)

### Лицензия

Этот проект лицензирован под Apache License, Version 2.0 - см. файл [LICENSE](../LICENSE) для подробностей.

---

## 📁 Структура файлов / File Structure

```
single-file-deployment/
├── docker-compose.yml    # Единый файл развертывания / Single deployment file
├── nginx.conf           # Конфигурация nginx / Nginx configuration
├── pneumatic.env        # Переменные окружения / Environment variables
├── start.sh             # Скрипт автоматического запуска / Auto-start script
├── stop.sh              # Скрипт остановки / Stop script
├── QUICK_START.md       # Краткая инструкция / Quick start guide
├── README.md            # Подробная документация / Detailed documentation
└── .gitignore           # Исключения для Git / Git exclusions
```

## ✨ Особенности / Features

- ✅ **Один файл docker-compose.yml** - вся конфигурация в одном месте
- ✅ **Готовые образы из Docker Hub** - не нужно собирать образы локально
- ✅ **Один .env файл** - все настройки в одном месте
- ✅ **Healthchecks** - автоматическая проверка состояния сервисов
- ✅ **Автоматические скрипты** - start.sh и stop.sh для удобства
- ✅ **Протестировано** - конфигурация проверена и работает
- ✅ **Двуязычная документация** - на русском и английском языках
