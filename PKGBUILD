# Maintainer: vlad.malygin.02@gmail.com

pkgname=dfsort
pkgver=1.0.0
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
    'python-schedule'
    'python-croniter'
    'python-questionary'
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

    # Устанавливаем конфиг
    install -Dm644 config/config.yaml "$pkgdir/etc/dfsort/config.yaml"

    # Устанавливаем systemd-юнит
    install -Dm644 systemd/dfsort.service "$pkgdir/usr/lib/systemd/user/dfsort.service"
}

post_install() {
    echo "=== DFSORT установлен ==="
    echo "Для настройки выполните: dfsort --configure"
    echo "Для запуска демона: systemctl --user start dfsort"
    echo "Конфиг: /etc/dfsort/config.yaml"
    echo "Логи: ~/.local/share/dfsort/dfsort.log"
}