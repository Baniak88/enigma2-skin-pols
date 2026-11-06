# Zgodność i zakres Pols Q 0.3.0

Docelowy obraz: OpenATV 8. Kontrakty widgetów 7.5/7.6/8.0 pochodzą z referencyjnego TvSat (zob. SOURCE.md i scripts/openatv-contracts.json). Potwierdzono statyczne dopasowanie do tego zapisanego zestawu, bez nowego pobierania źródeł OpenATV. Nie potwierdzono uruchomienia na sprzęcie.

## 64 definicje w obu wariantach

- `Menu`
- `QuickMenu`
- `ChannelSelection`
- `ChannelSelection_PIG`
- `ChannelSelection_NoPIG`
- `ChannelSelectionRadio`
- `HistoryZap`
- `HistoryZapSelector`
- `SimpleChannelSelection`
- `SlimChannelSelection`
- `BouquetSelector`
- `EPGBouquetSelector`
- `EPGSelection`
- `QuickEPG`
- `EPGSelectionMulti`
- `GraphicalEPG`
- `GraphicalEPGPIG`
- `GraphicalInfoBarEPG`
- `EPGvertical`
- `EPGverticalPIG`
- `EventView`
- `InfoBarEventView`
- `Setup`
- `PolsQSettings`
- `SkinSelection`
- `setup_Skin`
- `SetupSkin`
- `ChoiceBox`
- `ChannelContextMenu`
- `MessageBox`
- `MessageBoxSimple`
- `MessageBoxModal`
- `MovieSelection`
- `MovieSelectionSlim`
- `TimerOverview`
- `RecordTimerOverview`
- `TimerEditList`
- `ConflictTimerOverview`
- `TimerSanityConflict`
- `PluginBrowserList`
- `PluginBrowserGrid`
- `AudioSelection`
- `QuickSubtitlesConfigMenu`
- `FileCommander`
- `FileCommanderContextMenu`
- `FileCommanderData`
- `FileCommanderFileViewer`
- `FileCommanderTextEditor`
- `IpkgInstaller`
- `Opkg`
- `PackageAction`
- `PluginAction`
- `Console`
- `PackageActionLog`
- `PluginActionLog`
- `Processing`
- `InfoBar`
- `SecondInfoBar`
- `MoviePlayer`
- `PVRState`
- `TimeshiftState`
- `NumberZap`
- `Volume`
- `Mute`

## Do sprawdzenia na dekoderze

- Uruchomienie GUI w obu rozmiarach i wybór profilu.
- TV/radio, 8 wierszy, pikony, bukiety i historia.
- PIG oraz wariant bez podglądu.
- InfoBar, nagrywanie, timeshift, pauza i przewijanie.
- EPG, dodawanie timerów i rzeczywisty konflikt tunerów.
- Instalacja/aktualizacja IPK, błędy instalacji i powrót do poprzedniej skóry.
- FileCommander, wtyczki lista/siatka i długie polskie napisy.

Skóra definiuje ekrany, nie dostarcza EPG, kanałów, paczki pikonów, VOD ani wtyczek zewnętrznych. Wtyczki nieobjęte listą mogą korzystać z wyglądu systemowego.

## Nowe menu kafelkowe

W OpenATV 8.0 sprawdzono obsługę `listOrientation=grid` i pary wymiarów `(570,176)` w TemplatedMultiContent. Dla stylu początkowego None zadeklarowano także bezpośredni template oraz skalarne itemHeight/itemWidth. Wciąż wymagany jest test wszystkich klawiszy pilota i przewijania wielu stron na fizycznym odbiorniku.
