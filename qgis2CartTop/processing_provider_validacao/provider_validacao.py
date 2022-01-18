from qgis.core import QgsProcessingProvider
from .consolidar_curvas_de_nivel import Consolidar_curvas_de_nivel
from .consolidar_linha_de_quebra import Consolidar_quebra_de_linha

class Provider_validacao(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(Consolidar_curvas_de_nivel())
        self.addAlgorithm(Consolidar_quebra_de_linha())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'carttop_validacao'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('QGIS to CartTop (Validação\Correcção)')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)
