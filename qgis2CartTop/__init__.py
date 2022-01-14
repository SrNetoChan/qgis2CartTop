#-----------------------------------------------------------
# Copyright (C) 2019 Alexandre Neto
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 3
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Plugin structure based on Martin Dobias Minimal plugin
# https://github.com/wonder-sk/qgis-minimal-plugin
#---------------------------------------------------------------------

from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.core import QgsApplication
from .processing_provider.provider import Provider
from .processing_provider_validacao.provider_validacao import Provider_validacao

def classFactory(iface):
    return qgis2CartTop(iface)


class qgis2CartTop:
    def __init__(self, iface):
        self.iface = iface

    def initProcessing(self):
        self.provider = Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)
        self.provider_validacao = Provider_validacao()
        QgsApplication.processingRegistry().addProvider(self.provider_validacao)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        QgsApplication.processingRegistry().removeProvider(self.provider_validacao)