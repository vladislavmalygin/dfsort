#!/bin/PKGBUILD

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Установка DFSORT ===${NC}"

# Проверка прав
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Пожалуйста, не запускайте этот скрипт с sudo${NC}"
    exit 1
fi

# Установка зависимостей
echo -e "${GREEN}Установка зависимостей...${NC}"
pip install --user -r requirements.txt

# Установка пакета в режиме разработки
echo -e "${GREEN}Установка DFSORT...${NC}"
pip install --user -e .

# Создание директорий
echo -e "${GREEN}Создание директорий...${NC}"
mkdir -p ~/.config/dfsort
mkdir -p ~/.local/share/dfsort

# Копирование примера конфига
if [ ! -f ~/.config/dfsort/config.yaml ]; then
    echo -e "${GREEN}Копирование примера конфига...${NC}"
    cp config/config.yaml ~/.config/dfsort/config.yaml
else
    echo -e "${BLUE}Конфиг уже существует, пропускаем...${NC}"
fi

# Установка systemd-юнита
echo -e "${GREEN}Установка systemd-юнита...${NC}"
mkdir -p ~/.config/systemd/user
cp systemd/dfsort.service ~/.config/systemd/user/

# Активация юнита
systemctl --user daemon-reload
systemctl --user enable dfsort.service

echo -e "${GREEN}✓ Установка завершена!${NC}"
echo -e "${BLUE}Для запуска:${NC}"
echo "  dfsort                    # Запуск в режиме watchdog"
echo "  dfsort -o                  # Однократная обработка"
echo "  dfsort --configure         # Конфигуратор"
echo "  systemctl --user start dfsort  # Запуск как демон"