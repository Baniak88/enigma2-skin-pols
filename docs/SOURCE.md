# Źródło i adaptacja

Bazę komponentów, generatorów, narzędzi pakowania, runtime i testów zaadaptowano z repozytorium Baniak88/enigma2-skin, commit `582f8cd69d9d40f04292573bfd204534ec39d926`, TvSat 0.6.6, licencja MIT. Oryginalna licencja i copyright CanalPL contributors pozostają w LICENSE oraz w paczkach instalacyjnych.

Pols Q 0.3.0 zmienia przestrzeń nazw, ścieżki instalacji, nazwy pakietów i modułów na PolsQ/PolsQLarge/polsq. Skórki mogą współistnieć z TvSat. Wprowadzono paletę granat/niebieski/cyjan, dostosowane grafiki i kontrast gradientu opisu audycji, własne nagłówki oraz dokumentację i podglądy Pols Q. Zachowano zielony kolor fizycznej funkcji pilota niezależnie od koloru akcentu.

API systemowe i zachowanie pilota pozostają natywne dla OpenATV. Nie skopiowano logotypów ani materiałów graficznych SKY. Inspiracja SKY DE dotyczy kierunku wizualnego; nie oznacza implementacji jego systemu VOD, ekranu startowego ani usług operatora.

README wzorca podaje 62 ekrany, lecz jego aktualny generator tworzy 64 definicje. Pols Q ma 64 w każdym wariancie; aktualna lista jest generowana z XML w COMPATIBILITY.md.

Wersja 0.3.0 wprowadza własną kompozycję w scripts/q_layout.py: menu kafelkowe, odwrócony układ kanałów, kartowy InfoBar oraz nowy nagłówek EPG. Proceduralne tła, cienie, zaokrąglenia i sześć różnych ikon powstają w scripts/q_assets.py. Krajobraz jest generowany wyłącznie dla dokumentacji przez scripts/demo_video.py; na dekoderze renderer Pig pokazuje rzeczywisty kanał.
