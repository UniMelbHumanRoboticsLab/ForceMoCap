from PySide6 import QtWidgets, QtCore # use 6.9.0
from PySide6.QtCore import QTimer,Qt
from PySide6.QtGui import QFont
from vispy import scene
from vispy.app import use_app
print(use_app('pyside6'))

import pyqtgraph as pg # use dev pyqtgraph
pg.setConfigOptions(antialias=False)     # lines render faster
pg.setConfigOptions(useOpenGL=True)
pg.setConfigOptions(useCupy=True)
pg.setConfigOptions(useNumba=True)
pg.setConfigOptions(crashWarning=True)
pg.systemInfo()