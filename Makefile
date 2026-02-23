.PHONY: all install install-pip install-full clean uninstall

all: help

help:
	@echo "Доступные команды:"
	@echo "  make install       - установить через pip (для текущего пользователя)"
	@echo "  make install-full  - полная установка с AUR helper"
	@echo "  make deps-official - установить официальные зависимости"
	@echo "  make deps-aur      - установить AUR-зависимости"
	@echo "  make pkg           - собрать пакет"
	@echo "  make clean         - очистить файлы сборки"
	@echo "  make uninstall     - удалить пакет"

install:
	@echo "Установка через pip..."
	@sudo pacman -S --needed python python-watchdog python-yaml python-magic file python-pip
	@pip install --user schedule croniter questionary
	@pip install --user -e .
	@mkdir -p ~/.config/systemd/user
	@cp systemd/dfsort.service ~/.config/systemd/user/
	@echo "Установка завершена. Добавьте ~/.local/bin в PATH если нужно"

install-full:
	@echo "Полная установка..."
	@./install.sh

deps-official:
	@echo "Установка официальных зависимостей..."
	@sudo pacman -S --needed python python-watchdog python-yaml python-magic file python-pip python-build python-installer python-wheel python-setuptools

deps-aur:
	@echo "Установка AUR-зависимостей..."
	@if command -v yay &> /dev/null; then \
		yay -S python-schedule python-croniter python-questionary; \
	elif command -v paru &> /dev/null; then \
		paru -S python-schedule python-croniter python-questionary; \
	else \
		echo "Установите yay или paru сначала"; \
	fi

pkg:
	@echo "Сборка пакета..."
	@cd .. && tar -czf dfsort-1.0.0.tar.gz --transform="s/^dfsort/dfsort-1.0.0/" dfsort
	@makepkg -si

clean:
	@echo "Очистка..."
	@rm -rf pkg src *.tar.gz *.pkg.tar.zst
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

uninstall:
	@echo "Удаление..."
	@sudo pacman -R dfsort 2>/dev/null || true
	@pip uninstall -y dfsort 2>/dev/null || true
	@rm -f ~/.config/systemd/user/dfsort.service
	@systemctl --user daemon-reload
	@echo "Пакет удален"