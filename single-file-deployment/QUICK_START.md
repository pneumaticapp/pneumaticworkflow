# 🚀 Быстрый старт Pneumatic Workflow

## Вариант 1: Автоматический запуск (рекомендуется)

```bash
# Перейдите в папку развертывания
cd single-file-deployment

# Запустите автоматический скрипт
./start.sh
```

## Вариант 2: Ручной запуск

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

## 🌐 Доступ к приложению

После успешного запуска:

- **Основное приложение**: http://localhost
- **API напрямую**: http://localhost:8001  
- **Формы**: http://localhost:8002
- **RabbitMQ Management**: http://localhost:15672

## 🛑 Остановка

```bash
# Автоматическая остановка
./stop.sh

# Или ручная остановка
docker compose down
```

## 📋 Полезные команды

```bash
# Логи всех сервисов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs pneumatic-frontend

# Перезапуск сервиса
docker compose restart pneumatic-backend

# Статус сервисов
docker compose ps
```

## ⚠️ Важно

- Убедитесь, что Docker и Docker Compose установлены
- Порты 80, 8001, 8002 должны быть свободны
- Для продакшена измените пароли в `pneumatic.env`

