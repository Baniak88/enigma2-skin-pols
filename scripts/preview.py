#!/usr/bin/env python3
"""Podglądy prawdziwych współrzędnych XML z danymi przykładowymi, bez emulacji GUI."""
import argparse
import base64
from html import escape
import io
from pathlib import Path
import textwrap
import xml.etree.ElementTree as E
from build import VERSION
from skin_colors import rgba

ROOT=Path(__file__).resolve().parents[1]
from demo_video import render as render_demo
DEMO=ROOT/'docs/tv-demo.png'
if not DEMO.exists():render_demo()
SKIN=E.parse(ROOT/'PolsQ/skin.xml').getroot()
COLORS={c.get('name'):c.get('value') for c in SKIN.findall('colors/color')}
CHANNELS=['Sky Cinema HD','Sky Cinema Action','Sky Sport HD','Sky Atlantic HD','Das Erste HD','ZDF HD','RTL HD','ProSieben HD']
SHORT=['CINEMA','ACTION','SPORT','ATLANTIC','ERSTE','ZDF','RTL','PRO7']
SHOWS=['Wszystko przed nami','Wieczór filmowy','Magazyn sportowy','Nowy rozdział','Wiadomości dnia','Na dobre i na złe','Fakty','Wydarzenia']
CHANNEL_ROWS=[('TVP 1 HD','Akacjowa 38','TVP 1'),
    ('TVP 2 HD','Jeden z dziesięciu 157 (odc. 3)','TVP 2'),
    ('TVN HD','Detektywi 7 (odc. 50)','TVN'),
    ('Polsat HD','Wydarzenia','POLSAT'),
    ('TV PULS HD','Lombard. Życie pod zastaw 19 (odc. 49)','PULS'),
    ('Puls 2 HD','Pingwiny z Madagaskaru 1 (odc. 20)','PULS 2'),
    ('TVN 7 HD','Sędzia Anna Maria Wesołowska','TVN 7'),
    ('TV4 HD','Policjantki i policjanci','TV4'),
    ('TV6 HD','Policjanci z sąsiedztwa','TV6'),
    ('Polsat News Polityka HD','Debata polityczna — wydanie specjalne','POLITYKA')]
BOUQUETS=['Polskie','Polsat Box','Canal+','Canal+ (stary układ)','Telewizja na kartę','Polskie FTA','Filmy i seriale','Sport','Informacyjne','Dzieci']
HISTORY_ROWS=[('', '»', 'CANAL+ SERIALE HD', 'ABBA. Wbrew wszystkim', 'Opis audycji', '16:35 – 17:30 (+16 min)', 'C+ SERIALE', 'ref1'),
    ('', '', 'Polsat Film HD', 'Dywizjon 303. Historia prawdziwa', 'Opis audycji', '15:45 – 17:50 (+36 min)', 'POLSAT FILM', 'ref2'),
    ('', '', 'TVN Fabuła', 'Książę w Nowym Jorku', 'Opis audycji', '16:40 – 19:00 (+106 min)', 'TVN FABUŁA', 'ref3'),
    ('', '', 'Comedy Central HD', 'Przyjaciele 8: Ten, w którym Rachel ma dziecko (odc. 24)', 'Opis audycji', '16:55 – 17:25 (+11 min)', 'COMEDY', 'ref4'),
    ('', '', 'TVN HD', 'Detektywi (odc. 380)', 'Opis audycji', '16:55 – 18:00 (+46 min)', 'TVN', 'ref5'),
    ('', '', 'Polsat News HD', 'Wydarzenia — wydanie specjalne', 'Opis audycji', '17:00 – 18:00 (+46 min)', 'NEWS', 'ref6')]
out=[]
PROFILE='PolsQ'
STATE='success'


def color(value):
    raw=COLORS.get(value,value if value and value.startswith('#') else COLORS['white'])
    return '#'+''.join(f'{c:02x}' for c in rgba(raw)[:3])


def opacity(value):
    raw=COLORS.get(value,value if value and value.startswith('#') else COLORS['white'])
    return rgba(raw)[3]/255


def rect(x,y,w,h,fill):
    if w<=0 or h<=0:return
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color(fill)}" fill-opacity="{opacity(fill):.6f}"/>')


def text(x,y,w,h,value,size=28,fill='white',align='left',nowrap=False,bold=False,mono=False):
    lines=[]
    for paragraph in value.replace('\\n','\n').splitlines():
        capacity=max(1,int(w/(size*.57)))
        lines.extend([paragraph[:capacity-1]+'…' if len(paragraph)>capacity else paragraph] if nowrap else textwrap.wrap(paragraph,capacity))
        if not paragraph:lines.append('')
    anchor={'left':'start','center':'middle','right':'end'}.get(align,'start')
    tx=x+w if anchor=='end' else x+w/2 if anchor=='middle' else x
    limit=max(1,int(h/(size*1.25)))
    if len(lines)>limit:lines[limit-1]=lines[limit-1].rstrip(' .')+'…'
    for i,line in enumerate(lines[:limit]):
        family=' font-family="monospace"' if mono else ''
        out.append(f'<text x="{tx}" y="{y+size+i*size*1.25}" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="{color(fill)}" text-anchor="{anchor}"{family}>{escape(line)}</text>')


def png(path,x,y,w,h):
    encoded=base64.b64encode(path.read_bytes()).decode()
    out.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{encoded}"/>')


def fake_picon(index,x,y,w,h,title=None):
    # Celowo tekstowa próbka, bez kopiowania prawdziwych logo.
    # Przezroczysta próbka logo dziedziczy tło listy albo paska.
    text(x+4,y+h*.25,w-8,h*.7,title or SHORT[index],max(15,min(30,int(w/8))),'white','center')


def value(node,screen):
    src=node.get('source','');key=node.get('name','');conv=node.find('convert')
    kind=conv.get('type') if conv is not None else '';arg=conv.text if conv is not None else ''
    if src=='Title' and screen.startswith('ChannelSelection') and STATE=='bouquets':return 'TV — Użytkownik — Listy kanałów'
    if src=='Title':return {'Menu':'Menu główne','EventView':'Zapaleńcy. Historia polskiego filmu animowanego','InfoBarEventView':'Zapaleńcy. Historia polskiego filmu animowanego','QuickMenu':'Szybki dostęp do ustawień','ChoiceBox':'Wybór nośnika','ChannelSelection':'Ulubione — telewizja','BouquetSelector':'Wybierz bukiet','GraphicalEPG':'Ulubione — wtorek, 3 listopada','Setup':'Ustawienia listy kanałów','SkinSelection':'Ustawienia skórki','PolsQSettings':'Wybierz rozmiar interfejsu','ConflictTimerOverview':'Konflikt zaplanowanych nagrań','IpkgInstaller':'Instalacja rozszerzeń z /tmp','Opkg':'Instalacja pakietów','PackageAction':'Pobierz wtyczki','Processing':'Trwa operacja','Console':'Wynik polecenia','PackageActionLog':'Dziennik instalacji','FileCommander':'File Commander','FileCommanderContextMenu':'Operacje na plikach','FileCommanderData':'Informacje o pliku','FileCommanderTextEditor':'Edytor tekstu','PluginBrowserGrid':'Wtyczki','PluginBrowserList':'Wtyczki'}.get(screen,'')
    if src=='global.CurrentTime':return '20:45'
    if src=='description':return 'Informacje o dekoderze, obrazie OpenATV, tunerach, pamięci i połączeniu sieciowym.'
    key=src or key
    if screen in ('EventView','InfoBarEventView'):
        if key=='channel':return 'CANAL+ FILM HD'
        if key=='datetime':return '5 lis, 20:00 — 21:30'
        if key=='duration':return '90 min'
        if key=='epg_description':return 'Zapaleńcy. Historia polskiego filmu animowanego\n\nDokument pokazuje, jak sztuka animacji odzwierciedla zmieniającą się rzeczywistość społeczną w Polsce. Film ukazuje ewolucję technik i tematów, które uczyniły polską animację fenomenem światowym.\n\nPL, 2024\nReżyseria: Marcin Giżycki\nWystępują: Zbigniew Rybczyński\n\nHistoria twórców, ich eksperymentów i filmów, które zdobyły uznanie na całym świecie.'
        if key.startswith('key_'):return {'key_green':'Dodaj timer','key_yellow':'Pojedynczy EPG','key_blue':'EPG wielu kanałów'}.get(key,'')
    if screen=='PolsQSettings':
        if key=='description':return 'Standard: 10 pozycji. Nazwa kanału u góry, audycja pod spodem.\n\nDuże napisy: także 10 pozycji, z nieco większą czcionką.\n\nNaciśnij ZIELONY — Zapisz również po aktualizacji, aby ustawić 10 pozycji również w starszym trybie listy.'
        if key=='footnote':return 'Po zapisaniu potrzebny jest restart GUI. Anuluj pozostawia ustawienia bez zmian.'
        if key.startswith('key_'):return {'key_red':'Anuluj','key_green':'Zapisz'}.get(key,'')
    if screen in ('HistoryZap','HistoryZapSelector'):
        if key.startswith('key_'):return {'key_red':'Anuluj','key_green':'Wybierz'}.get(key,'')
    if screen in ('ConflictTimerOverview','TimerSanityConflict'):
        if key=='description':return 'Dwa nagrania korzystają z tego samego tunera w nakładających się godzinach. Wybierz timer i zmień jego czas lub wyłącz go.'
        if key.startswith('key_'):return {'key_red':'Usuń','key_yellow':'Wyłącz','key_blue':'Ignoruj'}.get(key,'')
    if screen=='TimeshiftState':
        if key=='state':return 'Pauza'
        if key=='eventname':return 'Fakty — oglądanie z opóźnieniem'
    if screen=='SkinSelection':
        if key=='Title':return 'Ustawienia skórki'
        if key=='description':return 'Wybierz skórkę graficznego interfejsu użytkownika. Zielony przycisk zapisuje wybór. Domyślnie: PolsQ.'
        if key=='footnote':return '* Zmiana tej opcji może wymagać restartu interfejsu GUI.'
        if key.startswith('key_'):return {'key_red':'Anuluj','key_green':'Zapisz'}.get(key,'')
    if screen in ('PluginBrowserGrid','PluginBrowserList'):
        if key=='description':return 'Enhanced Movie Center — konfiguracja i ustawienia odtwarzania nagrań.'
        if key.startswith('key_'):return {'key_red':'Usuń wtyczki','key_green':'Zainstaluj wtyczki','key_yellow':'Aktualizuj wtyczki','key_blue':'Edytuj'}.get(key,'')
    if screen=='FileCommander':
        if key in ('sortleft','sortright'):return 'Sortuj: katalogi wg nazwy ↑ · pliki wg nazwy ↑'
        if key.startswith('key_'):return {'key_menu':'MENU','key_info':'INFO','key_help':'HELP'}.get(key,'')
    if screen=='FileCommanderContextMenu':
        if key=='description':return 'Wybierz operację dla zaznaczonego pliku lub katalogu. Dostępność działań zależy od aktualnego wyboru.'
        if key=='key_menu':return 'MENU'
    if screen=='FileCommanderTextEditor':
        if key=='path':return '/tmp/example.conf'
        if key=='location':return 'Wiersz 1 / 4'
        if key.startswith('key_'):return {'key_red':'Anuluj','key_green':'Zapisz','key_yellow':'Usuń wiersz','key_blue':'Wstaw wiersz'}.get(key,'')
    if screen=='FileCommanderData':
        if key=='data':return 'Ścieżka: /tmp/PolsQ.ipk\nTyp: pakiet instalacyjny\nRozmiar: 58 kB\nUprawnienia: -rw-r--r--'
        if key.startswith('key_'):return {'key_red':'Zamknij'}.get(key,'')
    if key.startswith('key_') and node.get('render')=='FixedLabel' and node.get('text')==' ':
        # Determine visibility from the source, but the marker itself has no text.
        return value(E.Element('widget',source=key),screen)
    if screen=='IpkgInstaller':
        if key=='introduction':return 'OK — zaznacz pakiet. Zielony — zainstaluj zaznaczone pakiety.'
        if key.startswith('key_'):return {'key_red':'Zamknij','key_green':'Instaluj','key_blue':'Zaznacz / odznacz'}.get(key,'')
    if screen=='Processing' and key=='description':return 'Instalowanie rozszerzeń. Proszę czekać…'
    if screen=='Opkg':
        if key=='status':return {'success':'Zakończono — zainstalowano 1 pakiet (0 błędów).','progress':'Instalowanie rozszerzeń… Proszę czekać.','error':'Zakończono z błędem — 1 błąd podczas instalacji.'}[STATE]
        if key=='package':return 'enigma2-plugin-skins-polsq' if STATE=='progress' else ''
        if key=='log':return ''
        if STATE=='progress' and key.startswith('key_'):return ''
        if key.startswith('key_'):return {'key_red':'Zamknij','key_blue':'Dziennik'}.get(key,'')
    if screen in ('Console','PackageActionLog'):
        if key in ('text','log'):return 'Instalowanie enigma2-plugin-skins-polsq…\n\nPolsQ — INSTALACJA ZAKOŃCZONA POMYŚLNIE\nUruchom ponownie interfejs GUI, aby wczytać zmiany.'
        if key.startswith('key_'):return {'key_red':'Zamknij','key_green':'Ukryj','key_yellow':'Zapisz log'}.get(key,'')
    if screen=='PackageAction':
        if key=='description':return 'Wybierz kategorię lub pakiet. OK — zaznacz, zielony — wykonaj operację.'
        if key.startswith('key_'):return {'key_red':'Zamknij','key_green':'Instaluj','key_blue':'Szukaj'}.get(key,'')
    if screen=='QuickMenu':
        if key=='description':return 'Aktualizacje oprogramowania, tworzenie kopii zapasowych i przywracanie ustawień. Wybierz działanie w prawej kolumnie.'
        if key.startswith('key_'):return {'key_red':'Zamknij','key_green':'Info o systemie','key_yellow':'Urządzenia'}.get(key,'')
    if screen=='Setup':
        if key=='description':return 'Wybierz sposób oznaczania kanałów kodowanych. Ustawienia po prawej używają tego samego kroju i rozmiaru pisma co nazwy opcji.'
        if key.startswith('key_'):return {'key_red':'Anuluj','key_green':'Zapisz','key_yellow':'Domyślne'}.get(key,'')
    if screen=='ChoiceBox' and key=='text':return 'Wybierz nośnik do przeskanowania.'
    if key.startswith('key_'):
        if screen=='ChannelSelection':return {'key_red':'Wszystkie','key_green':'Listy odbioru','key_yellow':'Dostawcy','key_blue':'Bukiety'}.get(key,'')
        if screen=='BouquetSelector':return {'key_red':'Anuluj','key_green':'Wybierz'}.get(key,'')
        if screen=='Menu':return {'key_red':'Wyjdź','key_blue':'Tryb edycji'}.get(key,'')
        return {'key_red':'Wyszukaj','key_green':'Dodaj timer','key_yellow':'Szukaj w EPG','key_blue':'AutoTimer'}.get(key,'')
    if src=='session.RecordState':return '● REC' if STATE=='recording' else ''
    if screen.startswith('ChannelSelection') and STATE=='bouquets' and kind in ('EventTime','PolsQEventRemaining'):return ''
    if kind=='PolsQEventRemaining':return 'Do końca: 15 min'
    if kind=='ServiceName':return (BOUQUETS[0] if STATE=='bouquets' else CHANNEL_ROWS[0][0]) if screen.startswith('ChannelSelection') else CHANNELS[0]
    if kind=='EventName':
        if screen.startswith('ChannelSelection'):
            if STATE=='bouquets':return ''
            return 'Uczestnicy programu mierzą się z wymagającymi zadaniami w kuchni. O zwycięstwie zdecydują umiejętności, współpraca i opanowanie.' if arg=='ExtendedDescription' else CHANNEL_ROWS[0][1]
        if arg=='ExtendedDescription':return 'Wieczór z wielkim kinem. Nieoczekiwane spotkanie zmienia życie bohaterów. Opowieść o odwadze, przyjaźni i wyborach, które zostają z nami na długo.'
        return 'Nocna zmiana' if src.endswith('Next') else SHOWS[0]
    if kind=='EventTime':
        return '+45 min' if arg=='Remaining' else '21:30' if src.endswith('Next') else '– 21:30' if arg=='EndTime' else '20:00'
    return node.get('text','')


def draw_list(name,key,x,y,w,h):
    if name=='PolsQSettings' and key=='config':
        row=int(SKIN.find("screen[@name='PolsQSettings']/widget[@name='config']").get('itemHeight'))
        rect(x,y,w,row,'selected')
        text(x+20,y+24,w*.6,44,'Rozmiar interfejsu',34 if PROFILE=='PolsQLarge' else 30)
        text(x+w*.64,y+24,w*.34,44,'Duże napisy' if PROFILE=='PolsQLarge' else 'Standard',34 if PROFILE=='PolsQLarge' else 30,'white','right')
    elif key=='timerlist':
        for i,(title,time) in enumerate([('Fakty','20:30 — 21:00'),('Film wieczoru','20:45 — 22:30')]):
            yy=y+i*112
            rect(x,yy,w,104,'selected' if i==0 else 'panel')
            png(ROOT/'PolsQ/icons/timer_rec.png',x+16,yy+28,44,44)
            text(x+84,yy+12,w-380,44,title,32,'white',nowrap=True)
            text(x+84,yy+60,w-380,34,'TVN HD' if i==0 else 'Polsat HD',25,'muted')
            text(x+w-330,yy+32,302,44,time,28,'white','right')
    elif name in ('PluginBrowserGrid','PluginBrowserList'):
        names=['Enhanced Movie Center (Ustawienia)','Media skaner','Menedżer plików','Odtwarzacz multimedialny','Odtwarzacz zdjęć','Open FM','OpenWebif','s4aUpdater','Ustawienia IMDb','Ustawienia transkodowania']
        icons=['movie_selection','scan','mainmenu','video_menu','information','audio_menu','network','setup','information','video_menu']
        for i,(title,icon) in enumerate(zip(names,icons)):
            if name.endswith('Grid'):
                xx=x+(i%4)*448;yy=y+(i//4)*228
                rect(xx+8,yy+8,432,212,'green' if i==0 else 'line')
                rect(xx+10,yy+10,428,208,'selected' if i==0 else 'panel')
                png(ROOT/'PolsQ/mainmenu'/(icon+'.png'),xx+148,yy+24,152,84)
                text(xx+24,yy+130,400,76,title,30,'white','center')
            elif i<6:
                yy=y+i*100
                if i==0:rect(x,yy,w,100,'selected')
                png(ROOT/'PolsQ/mainmenu'/(icon+'.png'),x+24,yy+12,100,60)
                text(x+156,yy+4,w-180,42,title,30,'white',nowrap=True)
                text(x+156,yy+48,w-180,40,'Przykładowy opis wtyczki',24,'muted',nowrap=True)
    elif name=='FileCommander':
        if key.startswith('head'):
            text(x+16,y,w-32,44,'/',28,'white',nowrap=True)
            text(x+16,y+60,176,32,'drwxr-xr-x',22,'muted',nowrap=True)
            text(x+212,y+60,156,32,'4.0 kB',22,'muted','right',nowrap=True)
            text(x+396,y+60,452,32,'śr 4 lis 2026 13:40',22,'muted','right',nowrap=True)
        else:
            for i,title in enumerate(['Back USB: Elements 25A2 (DISK_1)','Internal flash']):
                if key=='listleft' and i==1:rect(x,y+i*64,w,64,'selected')
                png(ROOT/'PolsQ/extensions/storage.png',x+12,y+i*64+16,32,32)
                text(x+60,y+i*64+12,776,40,title,28,'white',nowrap=True)
    elif name=='FileCommanderContextMenu':
        for i,title in enumerate(['Informacje o pliku','Nowy katalog','Kopiuj','Przenieś','Zmień nazwę','Ustawienia']):
            if i==0:rect(x,y,w,72,'selected')
            text(x+64,y+i*72+16,w-136,40,title,30,'white',nowrap=True)
    elif name=='FileCommanderTextEditor':
        for i,title in enumerate(['# Przykładowy plik konfiguracyjny','name=PolsQ','language=pl','enabled=true']):
            if i==0:rect(x,y,w,40,'selected')
            text(x+16,y+i*40+5,w-32,34,title,26,'white',nowrap=True,mono=True)
    elif name=='QuickMenu':
        if key=='mainlist':
            rows=[('Menedżer oprogramowania','Aktualizacje i kopie zapasowe','setup'),('Softcam','Uruchom / zatrzymaj / wybierz','missing'),('System','Ustawienia systemu','setup'),('Montowanie','Ustawienia montowania','missing'),('Sieć','Połączenie sieciowe','missing'),('Audio / Wideo','Dźwięk i obraz','video_menu'),('Tuner','Konfiguracja i wyszukiwanie','mainmenu'),('Wtyczki','Dostępne rozszerzenia','plugin_selection')]
            for i,(title,desc,icon) in enumerate(rows):
                if i==0:rect(x,y,w,76,'selected')
                png(ROOT/'PolsQ/mainmenu'/(icon+'.png'),x+12,y+i*76+14,52,48)
                text(x+88,y+i*76+4,w-112,40,title,30,'white',nowrap=True)
                text(x+88,y+i*76+44,w-112,28,desc,22,'white' if i==0 else 'muted',nowrap=True)
        else:
            rows=[('Aktualizacja oprogramowania','Sprawdź dostępne aktualizacje'),('Instalacja systemu online','Zainstaluj obraz systemu z sieci'),('Kopia zapasowa systemu','Utwórz pełną kopię obrazu'),('Kopia zapasowa ustawień','Zachowaj konfigurację i listy kanałów'),('Przywróć ustawienia','Wczytaj zapisaną kopię ustawień'),('Domyślne pliki kopii zapasowej','Wybierz zakres kopii'),('Dodatkowe pliki kopii zapasowej','Dodaj własne pliki'),('Wykluczone pliki kopii zapasowej','Pomiń wybrane pliki i katalogi')]
            for i,(title,desc) in enumerate(rows):
                text(x+20,y+i*76+4,w-40,40,title,30,'white',nowrap=True)
                text(x+20,y+i*76+44,w-40,28,desc,23,'muted',nowrap=True)
    elif name=='IpkgInstaller':
        rows=[f'enigma2-plugin-skins-polsq_{VERSION}_all.ipk','enigma2-plugin-extensions-example_1.0_all.ipk']
        for i,title in enumerate(rows):
            if i==0:rect(x,y,w,72,'selected')
            png(ROOT/'PolsQ/icons'/('lock_on.png' if i==0 else 'lock_off.png'),x+12,y+i*72+20,32,32)
            text(x+64,y+i*72+16,w-136,40,title,30,'white',nowrap=True)
    elif name=='PackageAction':
        rows=[('Skórki','',True),('PolsQ','Interfejs Full HD dla OpenATV',False),('Rozszerzenia','',True),('Przykładowa wtyczka','Opis dostępnego rozszerzenia',False)]
        for i,(title,description,category) in enumerate(rows):
            yy=y+i*88
            if i==1:rect(x,yy,w,88,'selected')
            text(x+16,yy+24,56,44,'›' if category else '·',32,'green','center')
            text(x+92,yy+(24 if category else 6),w-260,48 if category else 40,title,32 if category else 30,'white',nowrap=True)
            if not category:
                text(x+92,yy+48,w-260,32,description,24,'white' if i==1 else 'muted',nowrap=True)
                text(x+w-390,yy+8,280,36,VERSION if i==1 else '1.0',24,'muted','right',nowrap=True)
    elif name in ('Setup','SkinSelection') and key=='config':
        rows=[('Skórka GUI *','PolsQ'),('Czcionka zapasowa','Fallback Font 1'),('Ekran wyboru kanału','PolsQ'),('Automatyczne odświeżanie','Wyłącz'),('Szybkie przeładowanie skórki','Nie')] if name=='SkinSelection' else [('Znacznik kodowania','Żaden'),('Znacznik nagrywania','Czerwony'),('Postęp audycji','Pasek po prawej'),('Wyświetlanie pikon','Włącz'),('Liczba wierszy','8'),('Rozmiar numeru kanału','0'),('Rozmiar nazwy kanału','0'),('Rozmiar informacji o audycji','0'),('Rozmiar informacji o postępie','0'),('Zachowanie przy przełączaniu','Czarny ekran')]
        for i,(title,current) in enumerate(rows):
            if i==0:rect(x,y,w,64,'selected')
            text(x+20,y+i*64+16,w*.60-20,40,title,30,'white',nowrap=True)
            text(x+w*.64,y+i*64+16,w*.36-20,40,current,30,'white','right',nowrap=True)
    elif name=='ChoiceBox':
        rows=[('Back USB: Elements 25A2 (DISK_1)','/media/hdd/'),('Internal flash','/'),('Katalog tymczasowy','/tmp')]
        for i,(title,path) in enumerate(rows):
            if i==0:rect(x,y,w,72,'selected')
            png(ROOT/'PolsQ/icons/folder.png',x+12,y+i*72+20,36,32)
            text(x+64,y+i*72+16,int(w*.6),40,title,30,'white',nowrap=True)
            text(x+int(w*.65),y+i*72+16,int(w*.3),40,path,30,'white',nowrap=True)
    elif name in ('HistoryZap','HistoryZapSelector'):
        from validate import check_template
        node=SKIN.find(f"screen[@name='{name}']/widget[@source='menu']/convert")
        template=check_template(node.text);rh=template['itemHeight']
        for i,row in enumerate(HISTORY_ROWS[:int(h//rh)]):
            yy=y+i*rh;selected=i==2
            if selected:rect(x,yy,w,rh,'selected')
            for kind,entry in template['template']:
                xx,dy=entry['pos'];nw,nh=entry['size'];nx,ny=x+xx,yy+dy
                fill=entry.get('color_sel' if selected else 'color')
                if kind=='rect':fill=entry.get('backgroundColorSelected' if selected else 'backgroundColor')
                fill=f'#{fill:08x}' if fill is not None else 'white'
                if kind=='rect':rect(nx,ny,nw,nh,fill)
                elif kind=='pixmap':fake_picon(i,nx,ny,nw,nh,row[6])
                elif kind=='text':
                    field=entry['text'];family,font=template['fonts'][entry['font']]
                    text(nx,ny+(nh-font*1.25)/2,nw,nh,row[field],font,fill,
                        'center' if field==1 else 'left',nowrap=True,bold=family=='PolsQStrong')
    elif name=='Menu':
        rows=['Informacje','Timery','Nagrania','Wtyczki','Ustawienia','Czuwanie / restart']
        icons=['information','timermenu','movie_selection','plugin_selection','setup','shutdown']
        for i,row in enumerate(rows):
            xx=x+(i%3)*570;yy=y+(i//3)*176
            if i==0:png(ROOT/'PolsQ/assets/q-tile-focus.png',xx,yy,570,176)
            png(ROOT/'PolsQ/mainmenu'/(icons[i]+'.png'),xx+32,yy+28,64,64)
            text(xx+32,yy+108,498,54,row,32 if PROFILE=='PolsQLarge' else 28,'white',nowrap=True,bold=True)
    elif name=='BouquetSelector':
        widget=SKIN.find("screen[@name='BouquetSelector']/widget[@name='menu']")
        rh=int(widget.get('itemHeight'));font=int(widget.get('font').split(';')[1])
        for i,row in enumerate(BOUQUETS[:int(h//rh)]):
            if i==0:rect(x,y,w,rh,'selected');rect(x,y,4,rh,'green')
            text(x+16,y+i*rh+(rh-font*1.25)/2,w-32,rh,row,font,'white',nowrap=True)
    elif name.startswith('ChannelSelection'):
        template=E.parse(ROOT/PROFILE/'skinTemplates.xml').getroot().find('template')
        mode=template.find("mode[@name='other']" if STATE=='bouquets' else "mode[@name='bouquets']");rh=int(mode.get('itemHeight'))
        fonts=[font.rsplit(';',1) for font in template.get('fonts').split(',')]
        sample=[(name,'','') for name in BOUQUETS] if STATE=='bouquets' else CHANNEL_ROWS
        for i,(channel,show,logo) in enumerate(sample[:int(h//rh)]):
            yy=y+i*rh
            if i==0:png(ROOT/'PolsQ/assets/q-channel-focus.png',x,yy,w,rh)
            for node in mode:
                xx,dy=map(int,node.get('position').split(','));nw,nh=map(int,node.get('size').split(','))
                nx,ny=x+xx,yy+dy
                if node.tag=='rectangle':rect(nx,ny,nw,nh,node.get('foregroundColorSelected') if i==0 else node.get('foregroundColor'))
                elif node.tag=='pixmap':
                    if STATE=='bouquets':
                        if node.get('index')=='FolderImage':png(ROOT/PROFILE/'icons/folder.png',nx,ny,nw,nh)
                    else:fake_picon(i,nx,ny,nw,nh,logo)
                elif node.tag=='progress':
                    rect(nx,ny,nw,nh,'line');rect(nx,ny,nw*(.7-i*.07),nh,'green')
                elif node.tag=='text':
                    v={'Number':str(i+1),'ServiceName':channel,'EntryName':channel,'Title1':show}.get(node.get('index'),'')
                    family,size=fonts[int(node.get('font'))];font=int(size)
                    text(nx,ny+(nh-font*1.25)/2,nw,nh,v,font,node.get('foregroundColorSelected',node.get('foregroundColor','white')) if i==0 else node.get('foregroundColor','white'),node.get('horizontalAlignment','left'),nowrap=True,bold=family=='PolsQStrong')
    elif name=='GraphicalEPG' and key=='list':
        service=320;rows=int(SKIN.find("screen[@name='GraphicalEPG']/widget[@name='list']").get('NumberOfRows'));rowh=h/rows;area=w-service
        for i,(channel,show) in enumerate(zip(CHANNELS[:rows],SHOWS)):
            yy=y+i*rowh
            rect(x,yy,service-2,rowh-2,'panel')
            fake_picon(i,x+12,yy+8,80,rowh-16)
            text(x+106,yy+18,service-118,rowh-18,channel,23,'green' if i==0 else 'white',nowrap=True)
            titles=[show,'Nocna zmiana' if i==0 else 'Kolejna audycja','Program wieczorny']
            for j,show in enumerate(titles):
                xx=x+service+j*area/3
                rect(xx,yy,area/3-2,rowh-2,'selected' if i==0 and j==0 else 'now' if j==0 else 'panel')
                if i==0 and j==0:rect(xx,yy,3,rowh-2,'green')
                text(xx+12,yy+18,area/3-26,rowh-18,show,25,'white',nowrap=True)
                if (i,j) in ((1,1),(3,2)):
                    png(ROOT/'PolsQ/icons/epgclock.png',xx+area/3-44,yy+rowh-34,28,28)


def render(name,target,make_png=False,profile='PolsQ',state='success'):
    global out,SKIN,COLORS,PROFILE,STATE
    PROFILE=profile;STATE=state
    SKIN=E.parse(ROOT/profile/'skin.xml').getroot()
    COLORS={c.get('name'):c.get('value') for c in SKIN.findall('colors/color')}
    s=SKIN.find(f"screen[@name='{name}']");ox,oy=map(int,s.get('position').split(','));sw,sh=map(int,s.get('size').split(','))
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',f'<title>PolsQ — {name} — dane przykładowe</title>','<g font-family="DejaVu Sans, sans-serif">']
    rect(0,0,1920,1080,'#20282c')
    if name in ('InfoBar','EventView','InfoBarEventView','HistoryZap','HistoryZapSelector'):
        png(DEMO,0,0,1920,1080)
    rect(ox,oy,sw,sh,s.get('backgroundColor'))
    for n in sorted(s,key=lambda n:int(n.get('zPosition','0'))):
        x,y=map(int,n.get('position').split(','));w,h=map(int,n.get('size').split(','));x+=ox;y+=oy
        key=n.get('name') or n.get('source','')
        if key in ('lab1','number','bouquetlist') or re_timeline(key):continue
        if name=='FileCommander' and key in ('status','quickselect'):continue
        if key.startswith('key_') and not value(n,name):continue
        if n.get('backgroundColor') and n.get('backgroundColor')!='transparent' and n.get('transparent')!='1':rect(x,y,w,h,n.get('backgroundColor'))
        if n.get('render')=='FixedLabel' and n.get('text')==' ':continue
        if n.get('render')=='PolsQVideoFade':continue  # hidden once the reveal ends
        if n.get('render')=='Pig':
            png(DEMO,x,y,w,h)
        elif n.get('render')=='Picon':fake_picon(0,x,y,w,h)
        elif n.tag=='ePixmap':png(ROOT/n.get('pixmap'),x,y,w,h)
        elif key=='menuimage':png(ROOT/'PolsQ/mainmenu/information.png',x,y,w,h)
        elif key=='preview':png(ROOT/PROFILE/'prev.png',x,y,w,h)
        elif key=='timeline_text':
            for i,t in enumerate(['20:00','20:30','21:00','21:30','22:00','22:30']):text(x+320+i*(w-320)/6,y,(w-320)/6,h,t,26,'muted')
        elif n.get('render')=='Progress' or key in ('progress','slider','activityslider'):
            rect(x,y,w,h,n.get('backgroundColor','line'))
            rect(x,y,int(w*(0 if name.startswith('ChannelSelection') and STATE=='bouquets' else 1 if name=='Opkg' and key=='slider' else 0 if name=='Opkg' else .5)),h,'green')
        elif key in ('menu','list','config','timerlist','mainlist','sublist','plugins','pluginGrid','pluginList','listleft','listright','headleft','headright') or (name=='FileCommanderTextEditor' and key=='data'):
            draw_list(name,key,x,y,w,h)
        else:
            size=int(n.get('font','Regular;28').split(';')[-1])
            display=n.get('text') if n.get('render')=='FixedLabel' and key.startswith('key_') else value(n,name)
            text(x,y,w,h,display,size,n.get('foregroundColor','white'),n.get('halign','left'),n.get('noWrap')=='1' or n.get('wrap')=='ellipsis',n.get('font','').startswith('PolsQStrong;'),n.get('font','').startswith('PolsQMono;'))
    if name=='GraphicalEPG':
        guide=s.find("widget[@name='list']");gx,gy=map(int,guide.get('position').split(','));gw,gh=map(int,guide.get('size').split(','))
        rect(gx+320+360,gy,3,gh,'green')
    out+=['</g>','</svg>']
    dest=ROOT/'docs'/target;dest.parent.mkdir(exist_ok=True);dest.write_text('\n'.join(out)+'\n')
    if make_png:render_png(dest)
    print(dest)


def re_timeline(key):
    return key.startswith('timeline') and key!='timeline_text'


def render_png(path):
    from PIL import Image,ImageDraw,ImageFont
    im=Image.new('RGBA',(1920,1080),(0,0,0,255));draw=ImageDraw.Draw(im)
    for n in E.parse(path).getroot().iter():
        tag=n.tag.split('}')[-1]
        if tag=='rect':
            x,y,w,h=[float(n.get(k)) for k in ('x','y','width','height')]
            alpha=round(float(n.get('fill-opacity','1'))*255)
            if alpha==255:
                draw.rectangle((x,y,x+w,y+h),fill=n.get('fill'))
            elif alpha:
                layer=Image.new('RGBA',im.size,(0,0,0,0))
                rgb=tuple(int(n.get('fill')[i:i+2],16) for i in (1,3,5))
                ImageDraw.Draw(layer).rectangle((x,y,x+w,y+h),fill=rgb+(alpha,))
                im=Image.alpha_composite(im,layer);draw=ImageDraw.Draw(im)
        elif tag=='text':
            font=ImageFont.truetype('DejaVuSansMono.ttf' if n.get('font-family')=='monospace' else 'DejaVuSans-Bold.ttf' if n.get('font-weight')=='bold' else 'DejaVuSans.ttf',int(n.get('font-size')))
            draw.text((float(n.get('x')),float(n.get('y'))),n.text or '',font=font,fill=n.get('fill'),anchor={'start':'ls','middle':'ms','end':'rs'}[n.get('text-anchor')])
        elif tag=='image':
            pic=Image.open(io.BytesIO(base64.b64decode(n.get('href').split(',')[1]))).convert('RGBA')
            pic=pic.resize((int(float(n.get('width'))),int(float(n.get('height')))))
            im.alpha_composite(pic,dest=(int(float(n.get('x'))),int(float(n.get('y')))))
        elif tag=='polygon':
            points=[tuple(map(float,p.split(','))) for p in n.get('points').split()]
            draw.polygon(points,fill=n.get('fill'))
    im.resize((1280,720),Image.Resampling.LANCZOS).save(path.with_suffix('.png'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--png',action='store_true')
    p.add_argument('--thumbnail',action='store_true',help='Zapisz PolsQ/prev.png dla wyboru skórek OpenATV (wymaga Pillow)')
    args=p.parse_args()
    for name,target in [('Menu','menu.svg'),('QuickMenu','quickmenu.svg'),('ChoiceBox','choices.svg'),('ChannelSelection','channels.svg'),('BouquetSelector','bouquets.svg'),('GraphicalEPG','epg.svg'),('InfoBar','infobar.svg'),('Setup','setup.svg'),('EventView','event-info.svg'),('InfoBarEventView','event-info-overlay.svg'),('SkinSelection','skin-selection.svg'),('IpkgInstaller','installer.svg'),('Opkg','install-result.svg'),('PackageAction','packages.svg'),('Processing','processing.svg'),('Console','console.svg'),('FileCommander','filemanager.svg'),('FileCommanderContextMenu','file-operations.svg'),('FileCommanderData','file-info.svg'),('FileCommanderTextEditor','file-editor.svg'),('PluginBrowserGrid','plugin-grid.svg'),('PluginBrowserList','plugin-list.svg')]:
        render(name,target,args.png or (args.thumbnail and name=='Menu'))
        # Refresh before SkinSelection embeds the thumbnail, so a palette
        # change is visible there on the first build as well.
        if args.thumbnail and name=='Menu':
            from PIL import Image
            with Image.open(ROOT/'docs/menu.png') as image:
                image.convert('RGBA').resize((640,360),Image.Resampling.LANCZOS).save(ROOT/'PolsQ/prev.png')
            print(ROOT/'PolsQ/prev.png')

    for name,target,state in [('PolsQSettings','appearance.svg','success'),('ConflictTimerOverview','timer-conflict.svg','success'),('TimeshiftState','timeshift.svg','success'),('Opkg','install-progress.svg','progress'),('Opkg','install-error.svg','error'),('InfoBar','infobar-recording.svg','recording')]:
        render(name,target,args.png,state=state)
    render('ChannelSelection','channel-bouquets.svg',args.png,state='bouquets')
    render('ChannelSelection','channel-bouquets-large.svg',args.png,profile='PolsQLarge',state='bouquets')
    render('HistoryZap','history.svg',args.png)
    render('HistoryZap','history-large.svg',args.png,profile='PolsQLarge')
    for name,target in [('Menu','menu-large.svg'),('ChannelSelection','channels-large.svg'),('InfoBar','infobar-large.svg'),('GraphicalEPG','epg-large.svg'),('PolsQSettings','appearance-large.svg'),('EventView','event-info-large.svg')]:
        render(name,target,args.png or (args.thumbnail and name=='Menu'),profile='PolsQLarge')
        if args.thumbnail and name=='Menu':
            from PIL import Image
            with Image.open(ROOT/'docs/menu-large.png') as image:
                image.convert('RGBA').resize((640,360),Image.Resampling.LANCZOS).save(ROOT/'PolsQLarge/prev.png')

