# Pols Q 0.2.0 — Enigma2 / OpenATV 8

Skóra Full HD 1920×1080 inspirowana kolorystyką i czytelnością interfejsu SKY DE: granatowe powierzchnie, niebieskie zaznaczenie i jasnoniebieskie akcenty. Projekt niezależny, bez oficjalnych logotypów SKY. To rozbudowana baza do testów na dekoderze, nie wierna kopia wszystkich funkcji SKY Q.

## Zakres

**64 definicje ekranów w każdym z dwóch wariantów**: PolsQ Standard i PolsQLarge / Duże napisy. Baza funkcjonalna pochodzi z udostępnionej przez użytkownika skóry [TvSat](https://github.com/Baniak88/enigma2-skin) na licencji MIT; zachowano oryginalną licencję. Szczegóły: [źródło i zmiany](docs/SOURCE.md).

- Menu i QuickMenu, telewizja/radio, bukiety, historia kanałów w bocznym panelu.
- Lista 10 kanałów z osobnymi liniami nazwy i audycji, pikonami i podglądem TV 16:9; także wariant bez TV.
- EPG pojedyncze, multi, graficzne, pionowe i PIG; opisy audycji, timery i konflikty nagrań.
- InfoBar, SecondInfoBar, nagrania, odtwarzacz, pauza/przewijanie i stan timeshiftu.
- Ustawienia, wybór skóry, dźwięk/napisy, wtyczki lista/siatka i dialogi.
- Instalator IPK, postęp, błędy, pakiety i logi; dwupanelowy FileCommander.
- Wtyczka **PolsQ — wygląd** do jawnego zapisania profilu listy i rozmiaru interfejsu.

## Efekty od razu w skórze

Paski mają 64 px przejścia fade i około 15% przezroczystości pod tekstem, również pod pikoną. Niebieska linia ma wygaszone końce i subtelną poświatę, a TERAZ zaokrąglone podświetlenie. Pełny opis audycji ma gradient od 94% do 85% krycia; większe krycie niż we wzorcu zapewnia kontrast jasnoniebieskich i szarych napisów na granatowym tle. Zaznaczenie jest jednolite, a długie napisy kończą się wielokropkiem. Zielony znacznik przycisku pilota zachowuje zielony kolor.

Są to statyczne grafiki PNG skalowane natywnie. Animacja otwierania okien zależy od ustawień OpenATV; skóra nie dodaje rozmycia obrazu na żywo ani własnej pętli animacji.

## Wizualizacje

Podglądy pochodzą z układu XML i danych przykładowych. Pikony tekstowe oraz kolorowe pole TV ilustrują układ i przezroczystość; to nie zrzuty z działającego dekodera.

![Lista kanałów](docs/channels.png)
![Pasek z nagrywaniem i fade](docs/infobar-recording.png)
![Graficzne EPG](docs/epg.png)
![Menu główne](docs/menu.png)
![Opis audycji](docs/event-info.png)
![Boczna historia kanałów](docs/history.png)

Pełna [galeria 38 podglądów](docs/GALLERY.md) obejmuje m.in. oba rozmiary, bukiety, instalację, konflikty timerów, wtyczki i FileCommandera.

## Instalacja OpenATV 8

Pobierz [enigma2-plugin-skins-polsq_0.2.0_all.ipk](packages/enigma2-plugin-skins-polsq_0.2.0_all.ipk), prześlij do `/tmp` dekodera i uruchom:

```sh
opkg install /tmp/enigma2-plugin-skins-polsq_0.2.0_all.ipk
```

Zrestartuj GUI, a następnie otwórz **Wtyczki → PolsQ — wygląd**, wybierz Standard lub Duże napisy i naciśnij zielony Zapisz. Wtyczka zaproponuje restart GUI. Zapis ustawia profil listy oraz pikony w natywnych ustawieniach OpenATV. Instalacja i Anuluj nie zmieniają ustawień. Skóra nie zmienia bukietów ani timerów i nie instaluje paczki logotypów kanałów.

Alternatywa: [PolsQ-0.2.0.tar.gz](packages/PolsQ-0.2.0.tar.gz). Rozpakuj do osobnego katalogu na dekoderze i wykonaj `sh install.sh`. Instalator ręczny tworzy kopie poprzednich plików i wycofuje częściową operację przy błędzie. Nie mieszaj instalacji ręcznej z opkg.

**Aktualizacja z prototypu 0.1:** zainstaluj pełną paczkę — sama podmiana skin.xml już nie wystarcza. Nowa wersja używa grafik, szablonów i własnych modułów z runtime.

## Kontrole i ograniczenia

Przeszło 45 testów: geometria obu wariantów, zapisane kontrakty widgetów OpenATV 7.5/7.6/8.0, struktura IPK, powtarzalność archiwów, instalator i wycofanie, pikony, kontrast oraz przezroczystość. Kontrakty źródeł OpenATV przejęto z referencyjnego projektu; w tej zmianie nie pobierano ponownie jego kodu. **Nie wykonano testu GUI na dekoderze.** Docelowy obraz to OpenATV 8; model urządzenia nie został jeszcze podany. PIG zależy od sterownika odbiornika, a zewnętrzne dodatki mogą korzystać z wyglądu systemowego. [Lista ekranów i testów sprzętowych](docs/COMPATIBILITY.md).

## Budowanie ze źródeł

Python 3.12+ i Pillow. Repozytorium zawiera generatory i wynikowy XML; grafiki skóry odtwarza build, a pełny zestaw instalacyjny znajduje się w paczkach.

```sh
python tools/build.py
python -m unittest discover -s tests -v
```

Wyniki trafiają do `dist/`. Nie edytuj wygenerowanego XML bez przeniesienia zmian do `scripts/generate_skin.py`, `scripts/ui_profiles.py` lub `scripts/skin_effects.py`.

## Powrót do poprzedniej skóry

Wybierz poprzednią skórę w ustawieniach i zrestartuj GUI. Gdy GUI nie startuje, zatrzymaj Enigma2 przez SSH (`init 4` w obrazie z runlevel), zrób kopię `/etc/enigma2/settings`, usuń wyłącznie wpis `config.skin.primary_skin=PolsQ/skin.xml` lub `config.skin.primary_skin=PolsQLarge/skin.xml` i uruchom GUI (`init 3`). Użyj odpowiedniej procedury usług dla swojego obrazu.
