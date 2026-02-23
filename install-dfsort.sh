#!/bin/bash

set - e

# Цвета
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
NC = '\033[0m'

echo - e
"${BLUE}========================================${NC}"
echo - e
"${GREEN}   Установка DFSORT - File Auto-Sorter   ${NC}"
echo - e
"${BLUE}========================================${NC}"

# Определение системы
if [-f / etc / os - release]; then
./ etc / os - release
OS =$ID
VER =$VERSION_ID
else
OS =$(uname - s)
fi

echo - e
"${GREEN}✓ Определена система: $OS $VER${NC}"

install_arch()
{
    echo - e
"${BLUE}Установка для Arch Linux...${NC}"

if command - v
yay & > / dev / null;
then
yay - S
dfsort
elif command - v
paru & > / dev / null;
then
paru - S
dfsort
else
echo - e
"${RED}Установите AUR helper (yay/paru) сначала${NC}"
exit
1
fi
}

install_debian()
{
    echo - e
"${BLUE}Установка для Debian/Ubuntu/Mint...${NC}"


sudo
apt
update
sudo
apt
install - y
python3
python3 - pip
python3 - venv
pipx
git

cd / tmp
rm - rf
dfsort
git
clone
https: // github.com / vladislavmalygin / dfsort.git
cd
dfsort

pipx
ensurepath
pipx
install.

pipx
inject
dfsort
watchdog
pyyaml
python - magic
schedule
croniter
questionary
2 > / dev / null | | true

mkdir - p
~ /.config / dfsort
if [ ! -f
~ /.config / dfsort / config.yaml]; then
cp
config / config.yaml
~ /.config / dfsort / 2 > / dev / null | | true
fi
}

install_pip()
{
    echo - e
"${BLUE}Установка через pip...${NC}"

cd
~
python3 - m
venv
dfsort - venv
source
dfsort - venv / bin / activate

pip
install - -upgrade
pip
pip
install
watchdog
pyyaml
python - magic
schedule
croniter
questionary

cd / tmp
rm - rf
dfsort
git
clone
https: // github.com / vladislavmalygin / dfsort.git
cd
dfsort
pip
install - e.

cat > ~ /.local / bin / dfsort << 'INNEREOF'
# !/bin/bash
source
~ / dfsort - venv / bin / activate
python - m
dfsort.cli
"$@"
INNEREOF
chmod + x
~ /.local / bin / dfsort

echo
'export PATH=$PATH:~/.local/bin' >> ~ /.bashrc

echo - e
"${GREEN}✓ Добавьте PATH: source ~/.bashrc${NC}"
}

case $OS in
arch | manjaro)
install_arch \
    ;;
ubuntu | debian | linuxmint | pop)
install_debian \
    ;;
* )
echo - e
"${RED}Неизвестная ОС. Используем универсальный метод...${NC}"
install_pip \
    ;;
esac

# Финальная проверка
echo - e
"${BLUE}========================================${NC}"
echo - e
"${GREEN}✅ Установка завершена!${NC}"
echo - e
"${BLUE}========================================${NC}"
echo
"Для настройки выполните:"
echo
"  dfsort --configure"
echo
""
echo
"Для запуска:"
echo
"  dfsort              # демон"
echo
"  dfsort -o           # однократно"
echo
"  dfsort --help       # справка"
echo - e
"${BLUE}========================================${NC}"

# Проверка установки
if command - v
dfsort & > / dev / null;
then
echo - e
"${GREEN}✓ dfsort найден в PATH${NC}"
dfsort - -version
else
echo - e
"${RED}✗ dfsort не найден. Перезапустите терминал.${NC}"
fi