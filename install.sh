#!/bin/bash
# install.sh - Универсальный установщик DFSORT

set -e

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Установка DFSORT - File Auto-Sorter   ${NC}"
echo -e "${BLUE}========================================${NC}"

# Определение системы
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    OS=$(uname -s)
fi

echo -e "${GREEN}✓ Определена система: $OS $VER${NC}"

# Функция для Arch Linux
install_arch() {
    echo -e "${BLUE}Установка для Arch Linux...${NC}"

    # Проверка AUR helper
    if command -v yay &> /dev/null; then
        echo -e "${GREEN}✓ Найден yay${NC}"
        yay -S dfsort
    elif command -v paru &> /dev/null; then
        echo -e "${GREEN}✓ Найден paru${NC}"
        paru -S dfsort
    else
        echo -e "${YELLOW}AUR helper не найден. Устанавливаем через pipx...${NC}"
        sudo pacman -S --needed python-pipx
        pipx ensurepath
        pipx install git+https://github.com/vladislavmalygin/dfsort.git
        pipx inject dfsort watchdog pyyaml python-magic schedule croniter questionary 2>/dev/null || true
    fi
}

# Функция для Debian/Ubuntu/Mint
install_debian() {
    echo -e "${BLUE}Установка для Debian/Ubuntu/Mint...${NC}"

    # Системные зависимости
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv pipx curl wget git

    # Проверка версии
    if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
        # Для новых систем - через pipx
        echo -e "${BLUE}Установка через pipx...${NC}"
        pipx ensurepath
        pipx install git+https://github.com/vladislavmalygin/dfsort.git
    else
        # Для старых систем - через pip
        echo -e "${BLUE}Установка через pip...${NC}"
        pip3 install --user git+https://github.com/vladislavmalygin/dfsort.git
        echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
    fi
}

# Функция для Fedora/RHEL
install_fedora() {
    echo -e "${BLUE}Установка для Fedora/RHEL...${NC}"

    # Системные зависимости
    sudo dnf install -y python3 python3-pip python3-virtualenv pipx git

    # Установка через pipx
    pipx ensurepath
    pipx install git+https://github.com/vladislavmalygin/dfsort.git
}

# Функция для openSUSE
install_opensuse() {
    echo -e "${BLUE}Установка для openSUSE...${NC}"

    # Системные зависимости
    sudo zypper install -y python3 python3-pip python3-virtualenv pipx git

    # Установка через pipx
    pipx ensurepath
    pipx install git+https://github.com/vladislavmalygin/dfsort.git
}

# Функция для macOS
install_macos() {
    echo -e "${BLUE}Установка для macOS...${NC}"

    # Проверка brew
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Установка Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Установка python и pipx
    brew install python3 pipx
    pipx ensurepath

    # Установка dfsort
    pipx install git+https://github.com/vladislavmalygin/dfsort.git
}

# Функция для универсальной установки (через виртуальное окружение)
install_universal() {
    echo -e "${BLUE}Универсальная установка через виртуальное окружение...${NC}"

    # Создание виртуального окружения
    cd ~
    python3 -m venv dfsort-venv
    source dfsort-venv/bin/activate

    # Установка зависимостей
    pip install --upgrade pip
    pip install watchdog pyyaml python-magic schedule croniter questionary

    # Клонирование и установка
    cd /tmp
    rm -rf dfsort
    git clone https://github.com/vladislavmalygin/dfsort.git
    cd dfsort
    pip install -e .

    # Создание запускателя
    mkdir -p ~/.local/bin
    cat > ~/.local/bin/dfsort << 'INNEREOF'
#!/bin/bash
source ~/dfsort-venv/bin/activate
python -m dfsort.cli "$@"
INNEREOF
    chmod +x ~/.local/bin/dfsort

    # Добавление в PATH
    echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
    echo 'export PATH=$PATH:~/.local/bin' >> ~/.zshrc 2>/dev/null || true

    echo -e "${GREEN}✓ Добавьте PATH: source ~/.bashrc${NC}"
}

# Выбор метода установки (если скрипт запущен с аргументами)
if [ "$1" = "arch" ]; then
    install_arch
elif [ "$1" = "debian" ]; then
    install_debian
elif [ "$1" = "fedora" ]; then
    install_fedora
elif [ "$1" = "macos" ]; then
    install_macos
else
    # Автоматическое определение
    case $OS in
        arch|manjaro|arcolinux|endeavouros)
            install_arch
            ;;
        ubuntu|debian|linuxmint|pop|elementary|zorin|kali)
            install_debian
            ;;
        fedora|rhel|centos|rocky|alma)
            install_fedora
            ;;
        opensuse*|suse)
            install_opensuse
            ;;
        darwin)
            install_macos
            ;;
        *)
            echo -e "${YELLOW}Неизвестная ОС. Используем универсальный метод...${NC}"
            install_universal
            ;;
    esac
fi

# Обновление PATH для текущей сессии
export PATH=$PATH:~/.local/bin

# Финальная проверка
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}📦 DFSORT установлен!${NC}"
echo ""
echo "⚙️  Настройка:"
echo "  dfsort --configure"
echo ""
echo "🚀 Запуск:"
echo "  dfsort              # демон"
echo "  dfsort -o           # однократно"
echo "  dfsort --help       # справка"
echo ""
echo "📝 Логи: ~/.local/share/dfsort/dfsort.log"
echo ""

# Проверка установки
if command -v dfsort &> /dev/null; then
    echo -e "${GREEN}✓ dfsort готов к работе!${NC}"
    dfsort --version 2>/dev/null || echo -e "${YELLOW}Перезапустите терминал для применения PATH${NC}"
else
    echo -e "${YELLOW}⚠️  Перезапустите терминал или выполните: source ~/.bashrc${NC}"
fi

echo -e "${BLUE}========================================${NC}"