#!/bin/PKGBUILD

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Удаление DFSORT ===${NC}"

# Остановка сервиса
echo -e "${GREEN}Остановка сервиса...${NC}"
systemctl --user stop dfsort.service
systemctl --user disable dfsort.service

# Удаление systemd-юнита
echo -e "${GREEN}Удаление systemd-юнита...${NC}"
rm -f ~/.config/systemd/user/dfsort.service
systemctl --user daemon-reload

# Удаление пакета
echo -e "${GREEN}Удаление пакета...${NC}"
pip uninstall -y dfsort

# Спрашиваем про конфиги
read -p "Удалить конфигурационные файлы? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Удаление конфигов...${NC}"
    rm -rf ~/.config/dfsort
    rm -rf ~/.local/share/dfsort
fi

echo -e "${GREEN}✓ Удаление завершено!${NC}"