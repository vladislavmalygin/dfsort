# Maintainer: vlad.malygin.02@gmail.com

pkgname=dfsort
pkgver=0.5.0
pkgrel=1
pkgdesc="File Auto-Sorter - автоматическая сортировка файлов"
arch=('any')
url="https://github.com/vladislavmalygin/dfsort"
license=('MIT')
depends=(
    'python'
    'python-watchdog'
    'python-yaml'
    'python-magic'
    'python-pip'
    'file'
)
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("$pkgname-$pkgver.tar.gz::https://github.com/vladislavmalygin/$pkgname/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname-$pkgver"

    # Устанавливаем Python-пакет
    python -m installer --destdir="$pkgdir" dist/*.whl

    # Устанавливаем зависимости через pip (в системный site-packages)
    export PIP_ROOT="$pkgdir"
    export PYTHONPATH="$pkgdir/usr/lib/python3.11/site-packages"
    pip install --root="$pkgdir" --prefix=/usr --ignore-installed \
        schedule \
        croniter \
        questionary

    # Устанавливаем конфиг
    install -Dm644 config/config.yaml "$pkgdir/etc/dfsort/config.yaml"

    # Устанавливаем systemd-юнит (пользовательский)
    install -Dm644 systemd/dfsort.service "$pkgdir/usr/lib/systemd/user/dfsort.service"

    # Создаём симлинк для совместимости (не нужен, уже есть от installer)
    # mkdir -p "$pkgdir/usr/bin"
    # ln -s /usr/bin/dfsort "$pkgdir/usr/bin/dfsort"
}

# Функция для установки после установки пакета
post_install() {
    echo "=== DFSORT установлен ==="
    echo "Для настройки выполните: dfsort --configure"
    echo "Для запуска демона: systemctl --user start dfsort"
    echo "Конфиг: /etc/dfsort/config.yaml"
    echo "Логи: ~/.local/share/dfsort/dfsort.log"
}