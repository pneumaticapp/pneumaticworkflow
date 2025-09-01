#!/bin/bash

# Pneumatic Workflow - Stop Script
# Этот скрипт останавливает и очищает приложение

set -e

echo "🛑 Остановка Pneumatic Workflow..."

# Останавливаем сервисы
echo "⏹️  Остановка сервисов..."
docker compose down

# Спрашиваем про удаление данных
read -p "🗑️  Удалить все данные (volumes)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Удаление всех данных..."
    docker compose down -v
    echo "✅ Все данные удалены!"
else
    echo "💾 Данные сохранены в volumes"
fi

# Спрашиваем про удаление образов
read -p "🗑️  Удалить образы? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Удаление образов..."
    docker compose down --rmi all
    echo "✅ Образы удалены!"
else
    echo "💾 Образы сохранены"
fi

echo ""
echo "✅ Приложение остановлено!"

