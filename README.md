# 🗂️ DFSORT - File Auto-Sorter

[![AUR](https://img.shields.io/aur/version/dfsort)](https://aur.archlinux.org/packages/dfsort)
[![GitHub release](https://img.shields.io/github/v/release/vladislavmalygin/dfsort)](https://github.com/vladislavmalygin/dfsort/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**DFSORT** - автоматическая сортировка файлов в указанной папке по заданным правилам.  
Версия: **1.0.3** (последний стабильный релиз)

---

## 📋 Оглавление
- [Возможности](#-возможности)
- [Установка](#-установка)
  - [Универсальный способ](#универсальный-способ-рекомендуется)
  - [Arch Linux](#arch-linux)
  - [Debian/Ubuntu/Mint](#debianubuntumint)
  - [Через pip](#через-pip)
  - [Из исходников](#из-исходников)
- [Быстрый старт](#-быстрый-старт)
- [Команды](#-команды)
- [Конфигурация](#-конфигурация)
- [Режимы работы](#-режимы-работы)
- [Автозапуск (systemd)](#-автозапуск-systemd)
- [Примеры](#-примеры)
- [Логи](#-логи)
- [Релизы](#-релизы)
- [Лицензия](#-лицензия)

---

## ✨ Возможности

✅ **Мониторинг папки** в реальном времени (watchdog)  
✅ **Проверка по расписанию** (интервалы или cron)  
✅ **Гибкие правила сортировки**:
  - По расширению файла (регулярные выражения)
  - По MIME-типу (определение типа содержимого)
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
✅ **Systemd-юнит** для автозапуска в фоне  
✅ **Подробное логирование** с ротацией файлов  

---

## 🚀 Установка

### Универсальный способ (рекомендуется для всех)
**Одна команда для любой системы:**
```bash
curl -sSL https://raw.githubusercontent.com/vladislavmalygin/dfsort/main/install.sh | bash

Arch Linux:

# Из AUR (рекомендуется)
yay -S dfsort
# или
paru -S dfsort

Debian/Ubuntu/Mint

# Скачайте .deb пакет с последнего релиза
wget https://github.com/vladislavmalygin/dfsort/releases/download/v1.0.3/dfsort-1.0.3.deb

# Установите
sudo dpkg -i dfsort-1.0.3.deb
sudo apt install -f  # если нужны зависимости

# Установка напрямую из GitHub
pip install git+https://github.com/vladislavmalygin/dfsort.git

# Или после клонирования
git clone https://github.com/vladislavmalygin/dfsort.git
cd dfsort
pip install -r requirements.txt
pip install -e .


git clone https://github.com/vladislavmalygin/dfsort.git
cd dfsort
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .


Быстрый старт
# 1. Запустите конфигуратор (создаст базовый конфиг)
dfsort --configure

# 2. Проверьте сортировку (однократная обработка всех файлов)
dfsort -o

# 3. Запустите в режиме демона
dfsort

Команды

dfsort	Запуск в режиме watchdog (мгновенное отслеживание)
dfsort -o	Однократная обработка всех файлов в папке (с учётом ограничения по времени прописанного в конфиге)
dfsort -d	Запуск в режиме демона (для systemd)
dfsort --configure	Запуск интерактивного конфигуратора
dfsort --manage-config	Управление конфигом (просмотр/удаление/бэкап/восстановление)
dfsort -c ФАЙЛ	Использовать указанный конфиг-файл
dfsort -h	Показать справку
dfsort --version	Показать версию

⚙️ Конфигурация

Конфигурационный файл находится в /etc/dfsort/config.yaml (системный) или ~/.config/dfsort/config.yaml (пользовательский).






