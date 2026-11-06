from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.config import ConfigSelection, NoSave, config, configfile, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import QUIT_RESTART, TryQuitMainloop

from .profiles import apply_profile


class PolsQSettings(Screen, ConfigListScreen):
    """Changing a temporary choice does nothing until Save is selected."""
    def __init__(self, session):
        Screen.__init__(self, session)
        self.skinName = ['PolsQSettings', 'Setup']
        self.setTitle('PolsQ — wygląd i czytelność')
        self['key_red'] = StaticText('Anuluj')
        self['key_green'] = StaticText('Zapisz')
        self['description'] = Label()
        self['footnote'] = Label('Po zapisaniu potrzebny jest restart GUI. Anuluj pozostawia ustawienia bez zmian.')
        current = 'large' if config.skin.primary_skin.value.startswith('PolsQLarge/') else 'standard'
        self.profile = NoSave(ConfigSelection(default=current, choices=[('standard', 'Standard'), ('large', 'Duże napisy')]))
        ConfigListScreen.__init__(self, [getConfigListEntry('Rozmiar interfejsu', self.profile)], session=session)
        self['config'].onSelectionChanged.append(self.selectionChanged)
        self['actions'] = ActionMap(['SetupActions', 'ColorActions', 'OkCancelActions'], {
            'cancel': self.keyCancel, 'red': self.keyCancel, 'green': self.keySave,
            'ok': self.keyRight,
        }, -2)
        self.onLayoutFinish.append(self.selectionChanged)

    def selectionChanged(self):
        self['description'].setText('Standard: 10 pozycji. Nazwa kanału u góry, audycja pod spodem.\n\nDuże napisy: także 10 pozycji, z nieco większą czcionką.\n\nNaciśnij ZIELONY — Zapisz po aktualizacji, aby ustawić 10 pozycji również w starszym trybie listy. Historia kanałów pojawia się w panelu po lewej. Lista kanałów i timery pozostają bez zmian.')

    def keyCancel(self):
        self.close()

    def keySave(self):
        apply_profile(config, self.profile.value)
        configfile.save()
        self.session.openWithCallback(self.restartAnswer, MessageBox,
            'Zapisano wygląd PolsQ. Uruchomić ponownie interfejs GUI, aby zastosować zmiany?',
            type=MessageBox.TYPE_YESNO, default=False)

    def restartAnswer(self, answer):
        if answer:
            self.session.open(TryQuitMainloop, QUIT_RESTART)
        else:
            self.close()


def main(session, **kwargs):
    session.open(PolsQSettings)


def Plugins(**kwargs):
    return [PluginDescriptor(name='PolsQ — wygląd', description='Standard lub duże napisy, czytelna lista kanałów i pikony', where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main)]

