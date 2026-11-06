"""Enigma2 #AARRGGBB has transparency alpha, inverse to normal RGBA opacity."""


def rgba(value):
    value=value.lstrip('#')
    if len(value)==8:
        transparency=int(value[:2],16);value=value[2:]
    elif len(value)==6:
        transparency=0
    else:
        raise ValueError('Expected #RRGGBB or Enigma2 #AARRGGBB')
    return tuple(int(value[i:i+2],16) for i in (0,2,4))+(255-transparency,)

