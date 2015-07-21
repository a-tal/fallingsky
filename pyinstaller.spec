# -*- mode: python -*-
a = Analysis(['.\\fallingsky\\main.py'],
             pathex=['fallingsky'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
for d in a.datas:
    if 'pyconfig' in d[0]:
        a.datas.remove(d)
        break
pyz = PYZ(a.pure)
exe = EXE(pyz,
          Tree('.\\fallingsky\\images', prefix='images\\'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='fallingsky.exe',
          debug=False,
          strip=None,
          upx=True,
          console=False )
