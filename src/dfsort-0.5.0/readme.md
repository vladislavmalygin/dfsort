# 1. Клонируем репозиторий
git clone https://github.com/vladislavmalygin/dfsort.git
cd dfsort

# 3. Собираем пакет
makepkg -si

# 4. Или устанавливаем вручную
./install.sh


# Запуск из любого места
dfsort --configure
dfsort -o #разовый запуск, сначала нужно настроить конфиг
dfsort

# Управление через systemd
systemctl --user start dfsort     # Запуск демона
systemctl --user stop dfsort      # Остановка
systemctl --user enable dfsort    # Автозапуск
systemctl --user status dfsort    # Статус

# Логи
journalctl --user -u dfsort -f    # Просмотр логов в реальном времени