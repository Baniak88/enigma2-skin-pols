"""Explicit profile changes used only after the viewer presses Save."""
PROFILES = {
    'standard': {'skin': 'PolsQ/skin.xml', 'template': 'PolsQ', 'rows': 8, 'two_lines': True},
    'large': {'skin': 'PolsQLarge/skin.xml', 'template': 'PolsQLarge', 'rows': 8, 'two_lines': True},
}


def apply_profile(config, name):
    profile = PROFILES[name]
    changes = []
    def change(group, key, value, add_choice=False):
        field = getattr(group, key, None) if group is not None else None
        if field is None:
            return
        if add_choice and hasattr(field, 'setChoices'):
            choices = field.getSelectionList() if hasattr(field, 'getSelectionList') else list(field.choices.choices)
            values = [item[0] if isinstance(item, tuple) else item for item in choices]
            if value not in values:
                field.setChoices(choices + [(value, value)])
        if isinstance(field.value, str):
            value = str(value)
        field.value = value
        changes.append(field)
    change(config.skin, 'primary_skin', profile['skin'])
    usage = getattr(config, 'usage', None)
    for key, value in {
        'serviceitems_per_page': 8,
        'serviceitems_per_page_twolines': profile['rows'],
        'servicelist_twolines': profile['two_lines'],
        'servicelist_column': 425,
        'service_icon_enable': True,
        'show_channel_numbers_in_servicelist': True,
        'show_event_progress_in_servicelist': 'barright',
        'servicenum_fontsize': 0, 'servicename_fontsize': 0,
        'serviceinfo_fontsize': 0, 'progressinfo_fontsize': 0,
    }.items():
        change(usage, key, value)
    epg = getattr(config, 'epgselection', None)
    for group in ('graph', 'infobar', 'single', 'multi', 'vertical'):
        change(getattr(epg, group, None), 'itemsperpage', 0)
    selection = getattr(config, 'channelSelection', None)
    change(selection, 'screenStyle', 'ChannelSelection', add_choice=True)
    change(selection, 'widgetStyle', profile['template'], add_choice=True)
    change(selection, 'showPicon', True)
    change(selection, 'showNumber', True)
    for field in changes:
        field.save()
    return profile

