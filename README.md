# 🗂️ DFSORT - File Auto-Sorter

[![AUR](https://img.shields.io/aur/version/dfsort)](https://aur.archlinux.org/packages/dfsort)
[![GitHub release](https://img.shields.io/github/v/release/vladislavmalygin/dfsort)](https://github.com/vladislavmalygin/dfsort/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**DFSORT** - автоматическая сортировка файлов в указанной папке по заданным правилам.

## 📋 Оглавление
- [Возможности](#-возможности)
- [Установка](#-установка)
  - [Arch Linux](#arch-linux)
  - [Debian/Ubuntu/Mint](#debianubuntumint)
  - [Через pip](#через-pip)
  - [Универсальный скрипт](#универсальный-скрипт)
- [Быстрый старт](#-быстрый-старт)
- [Команды](#-команды)
- [Конфигурация](#-конфигурация)
- [Режимы работы](#-режимы-работы)
- [Автозапуск](#-автозапуск)
- [Сборка из исходников](#-сборка-из-исходников)
- [Лицензия](#-лицензия)

## ✨ Возможности

✅ **Мониторинг папки** в реальном времени (watchdog)  
✅ **Проверка по расписанию** (интервалы или cron)  
✅ **Гибкие правила сортировки**:
  - По расширению файла (regex)
  - По MIME-типу
  - По возрасту файла
✅ **Действия**:
  - Перемещение в указанную папку
  - Распаковка архивов (zip, tar, tar.gz)
  - Удаление файлов
✅ **Обработка конфликтов**:
  - Переименование (файл_1.ext)
  - Перезапись
  - Пропуск
✅ **Создание подпапок по дате** (например, %Y/%m)  
✅ **Белый список папок** - обрабатываются только указанные подпапки  
✅ **Бэкап конфигов** - хранение 2 последних версий  
✅ **Интерактивный конфигуратор** для лёгкой настройки  
✅ **Подробное логирование** с ротацией файлов  
✅ **Systemd-юнит** для автозапуска  

## 🚀 Установка

### Arch Linux

```bash
# Из AUR (рекомендуется)
yay -S dfsort
# или
paru -S dfsort

# Все зависимости установятся автоматически!

# Скачайте .deb пакет с последнего релиза
wget https://github.com/vladislavmalygin/dfsort/releases/download/v1.0.1/dfsort-1.0.1.deb

# Установите
sudo dpkg -i dfsort-1.0.1.deb
sudo apt install -f  # если нужны зависимости

# Или используйте универсальный скрипт (рекомендуется)
curl -sSL https://raw.githubusercontent.com/vladislavmalygin/dfsort/main/install.sh | bash


# Установка из PyPI (когда опубликуем)
pip install dfsort

# Или напрямую из GitHub
pip install git+https://github.com/vladislavmalygin/dfsort.git

bash <(curl -sSL https://raw.githubusercontent.com/vladislavmalygin/dfsort/main/install.sh)

# 1. Запустите конфигуратор (создаст конфиг)
dfsort --configure

# 2. Проверьте сортировку (однократная обработка)
dfsort -o

# 3. Запустите в режиме демона
dfsort

