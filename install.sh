#!/bin/bash
# install.sh - Автоматический установщик DFSORT

set -e  # Прерывать при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   Установка DFSORT - File Auto-Sorter   ${NC}"
echo -e "${BLUE}========================================${NC}"

# Проверка наличия yay
check_yay() {
    if command -v yay &> /dev/null; then
        echo -e "${GREEN}✓ Yay найден${NC}"
        return 0
    else
        return 1
    fi
}

# Проверка наличия paru
check_paru() {
    if command -v paru &> /dev/null; then
        echo -e "${GREEN}✓ Paru найден${NC}"
        return 0
    else
        return 1
    fi
}

# Установка AUR helper
install_aur_helper() {
    echo -e "${YELLOW}Установка AUR helper...${NC}"

    # Спрашиваем, какой helper использовать
    echo -e "${BLUE}Выберите AUR helper:${NC}"
    echo "1) yay (рекомендуется)"
    echo "2) paru"
    echo "3) Установить вручную позже"
    read -p "Выбор [1-3]: " helper_choice

    case $helper_choice in
        1)
            echo -e "${YELLOW}Установка yay...${NC}"
            sudo pacman -S --needed git base-devel
            git clone https://aur.archlinux.org/yay.git
            cd yay
            makepkg -si
            cd ..
            rm -rf yay
            echo -e "${GREEN}✓ Yay установлен${NC}"
            AUR_HELPER="yay"
            ;;
        2)
            echo -e "${YELLOW}Установка paru...${NC}"
            sudo pacman -S --needed git base-devel
            git clone https://aur.archlinux.org/paru.git
            cd paru
            makepkg -si
            cd ..
            rm -rf paru
            echo -e "${GREEN}✓ Paru установлен${NC}"
            AUR_HELPER="paru"
            ;;
        *)
            echo -e "${YELLOW}Продолжаем без AUR helper${NC}"
            AUR_HELPER=""
            ;;
    esac
}

# Установка зависимостей из официальных репозиториев
install_official_deps() {
    echo -e "${YELLOW}Установка зависимостей из официальных репозиториев...${NC}"
    sudo pacman -S --needed \
        python \
        python-watchdog \
        python-yaml \
        python-magic \
        file \
        python-pip \
        python-build \
        python-installer \
        python-wheel \
        python-setuptools
    echo -e "${GREEN}✓ Официальные зависимости установлены${NC}"
}

# Установка зависимостей из AUR
install_aur_deps() {
    local helper=$1

    if [ -z "$helper" ]; then
        echo -e "${YELLOW}Пропускаем установку AUR-зависимостей${NC}"
        echo -e "${BLUE}Вам нужно установить их вручную:${NC}"
        echo "  python-schedule"
        echo "  python-croniter"
        echo "  python-questionary"
        return
    fi

    echo -e "${YELLOW}Установка зависимостей из AUR...${NC}"

    # Массив пакетов из AUR
    AUR_PACKAGES=(
        "python-schedule"
        "python-croniter"
        "python-questionary"
    )

    for pkg in "${AUR_PACKAGES[@]}"; do
        echo -e "${BLUE}Установка $pkg...${NC}"
        $helper -S --needed --noconfirm $pkg
    done

    echo -e "${GREEN}✓ AUR-зависимости установлены${NC}"
}

# Установка самого DFSORT
install_dfsort() {
    echo -e "${YELLOW}Установка DFSORT...${NC}"

    # Создаём архив
    cd /home/vlad/Dev
    tar -czf dfsort-1.0.0.tar.gz --transform="s/^dfsort/dfsort-1.0.0/" dfsort

    # Собираем и устанавливаем пакет
    cd dfsort
    makepkg -si --noconfirm

    echo -e "${GREEN}✓ DFSORT установлен${NC}"
}

# Установка через pip (альтернативный вариант)
install_pip() {
    echo -e "${YELLOW}Установка через pip...${NC}"

    # Устанавливаем зависимости
    pip install --user schedule croniter questionary

    # Устанавливаем сам пакет
    cd /home/vlad/Dev/dfsort
    pip install --user -e .

    # Добавляем ~/.local/bin в PATH, если ещё не добавлен
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${YELLOW}Добавьте ~/.local/bin в PATH или перелогиньтесь${NC}"
    fi

    echo -e "${GREEN}✓ DFSORT установлен через pip${NC}"
}

# Настройка systemd юнита
setup_systemd() {
    echo -e "${YELLOW}Настройка systemd юнита...${NC}"

    mkdir -p ~/.config/systemd/user
    cp /home/vlad/Dev/dfsort/systemd/dfsort.service ~/.config/systemd/user/

    systemctl --user daemon-reload

    echo -e "${GREEN}✓ systemd юнит настроен${NC}"
    echo -e "${BLUE}Для запуска: systemctl --user start dfsort${NC}"
    echo -e "${BLUE}Для автозапуска: systemctl --user enable dfsort${NC}"
}

# Главное меню
main() {
    echo -e "${BLUE}Выберите способ установки:${NC}"
    echo "1) Полная установка (рекомендуется) - установит всё через AUR"
    echo "2) Установка через pip - для текущего пользователя"
    echo "3) Только подготовка - установит зависимости, но не сам пакет"
    echo "4) Выход"

    read -p "Выбор [1-4]: " choice

    case $choice in
        1)
            install_official_deps

            if ! check_yay && ! check_paru; then
                install_aur_helper
            else
                if check_yay; then
                    AUR_HELPER="yay"
                elif check_paru; then
                    AUR_HELPER="paru"
                fi
            fi

            install_aur_deps "$AUR_HELPER"
            install_dfsort
            setup_systemd

            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}Установка завершена успешно!${NC}"
            echo -e "${BLUE}Для настройки выполните: dfsort --configure${NC}"
            echo -e "${BLUE}Для запуска: dfsort${NC}"
            echo -e "${GREEN}========================================${NC}"
            ;;
        2)
            install_official_deps
            install_pip
            setup_systemd

            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}Установка через pip завершена!${NC}"
            echo -e "${YELLOW}Команда dfsort будет доступна после перезагрузки или добавления ~/.local/bin в PATH${NC}"
            echo -e "${GREEN}========================================${NC}"
            ;;
        3)
            install_official_deps

            if ! check_yay && ! check_paru; then
                install_aur_helper
            fi

            echo -e "${GREEN}Зависимости установлены. Теперь вы можете собрать пакет вручную:${NC}"
            echo "  cd /home/vlad/Dev/dfsort"
            echo "  makepkg -si"
            ;;
        *)
            echo -e "${RED}Установка отменена${NC}"
            exit 0
            ;;
    esac
}

# Запуск
main