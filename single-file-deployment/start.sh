#!/bin/bash

# Pneumatic Workflow - Quick Start Script
# Этот скрипт автоматически подготавливает и запускает приложение

set -e

echo "🚀 Запуск Pneumatic Workflow..."

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не установлен. Установите Docker и попробуйте снова."
    exit 1
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
    exit 1
fi

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p logs/nginx
mkdir -p www
mkdir -p staticfiles

# Проверяем наличие файлов
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Файл docker-compose.yml не найден!"
    exit 1
fi

if [ ! -f "pneumatic.env" ]; then
    echo "❌ Файл pneumatic.env не найден!"
    exit 1
fi

# Останавливаем существующие контейнеры
echo "🛑 Остановка существующих контейнеров..."
docker compose down 2>/dev/null || true

# Удаляем старые образы (опционально)
read -p "🗑️  Удалить старые образы? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Удаление старых образов..."
    docker compose down --rmi all 2>/dev/null || true
fi

# Запускаем сервисы
echo "🚀 Запуск сервисов..."
docker compose up -d

# Ждем запуска
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Проверяем статус
echo "📊 Статус сервисов:"
docker compose ps

# Проверяем здоровье сервисов
echo "🏥 Проверка здоровья сервисов..."
for i in {1..30}; do
    if docker compose ps | grep -q "healthy"; then
        echo "✅ Сервисы запущены и здоровы!"
        break
    fi
    echo "⏳ Ожидание... ($i/30)"
    sleep 10
done

# Показываем доступные URL
echo ""
echo "🌐 Доступные URL:"
echo "   Основное приложение: http://localhost"
echo "   API напрямую:        http://localhost:8001"
echo "   Формы:               http://localhost:8002"
echo "   RabbitMQ Management: http://localhost:15672"
echo ""
echo "📋 Полезные команды:"
echo "   Логи:                docker compose logs -f"
echo "   Статус:              docker compose ps"
echo "   Остановка:           docker compose down"
echo ""

# Проверяем доступность основного приложения
echo "🔍 Проверка доступности приложения..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|302"; then
    echo "✅ Приложение доступно!"
else
    echo "⚠️  Приложение может быть еще не готово. Проверьте логи: docker compose logs"
fi

echo ""
echo "🎉 Развертывание завершено!"

