#!/bin/sh
# Instalacja Pols Q prosto z GitHuba na dekoderze z OpenATV:
#   wget -qO- https://raw.githubusercontent.com/Baniak88/enigma2-skin-pols/main/online-install.sh | sh
# Restart GUI po instalacji:
#   wget -qO- https://raw.githubusercontent.com/Baniak88/enigma2-skin-pols/main/online-install.sh | sh -s -- --restart
# Inna gałąź: BRANCH=nazwa przed "sh", np. ... | BRANCH=claude/new-session-dlhvdu sh
set -eu
VERSION=0.4.3
REPO=Baniak88/enigma2-skin-pols
BRANCH=${BRANCH:-main}
IPK=enigma2-plugin-skins-polsq_${VERSION}_all.ipk
URL=https://raw.githubusercontent.com/$REPO/$BRANCH/packages/$IPK
TMP=/tmp/$IPK

fail() { printf 'PolsQ: %s\n' "$1" >&2; rm -f "$TMP"; exit 1; }

[ "$(id -u)" = 0 ] || fail 'uruchom jako root (zaloguj się przez SSH/telnet jako root).'
command -v opkg >/dev/null 2>&1 || fail 'brak opkg — to nie wygląda na obraz Enigma2/OpenATV.'

printf 'PolsQ %s — pobieranie z %s\n' "$VERSION" "$URL"
rm -f "$TMP"
if command -v wget >/dev/null 2>&1; then
    wget -q -O "$TMP" "$URL" || fail 'pobieranie nie powiodło się (sprawdź internet i datę systemową dekodera).'
elif command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$TMP" "$URL" || fail 'pobieranie nie powiodło się (sprawdź internet i datę systemową dekodera).'
else
    fail 'brak wget i curl.'
fi
# Pakiet .ipk to archiwum ar: zaczyna się od "!<arch>".
[ "$(head -c 7 "$TMP")" = '!<arch>' ] || fail 'pobrany plik nie jest pakietem .ipk (zła gałąź lub wersja?).'

opkg install --force-reinstall "$TMP" || fail 'opkg zgłosił błąd instalacji.'
rm -f "$TMP"

case "${1:-}" in
    --restart)
        printf '%s\n' 'PolsQ: restart GUI…'
        if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet enigma2 2>/dev/null; then
            systemctl restart enigma2
        else
            init 4; sleep 3; init 3
        fi
        ;;
    *)
        printf '%s\n' 'PolsQ: gotowe. Zrestartuj GUI (Menu → Standby/Restart → Restart GUI), wybierz skórkę PolsQ i ustaw wygląd w Wtyczki → PolsQ — wygląd.'
        ;;
esac
