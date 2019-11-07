from qgis.core import QgsProcessingProvider

from .example_processing_algorithm import ExampleProcessingAlgorithm
from .exportar_curvas_de_nivel import Exportar_curvas_de_nivel
from .exportar_pontos_cotados import Exportar_pontos_cotados
from .exportar_linhas_de_quebra import Exportar_linhas_de_quebra
from .exportar_elemento_associado_de_agua import Exportar_elemento_associado_de_agua
from .exportar_elemento_associado_de_eletricidade import Exportar_elemento_associado_de_eletricidade
from .exportar_cabo_eletrico import Exportar_cabo_eletrico



class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(ExampleProcessingAlgorithm())
        self.addAlgorithm(Exportar_curvas_de_nivel())
        self.addAlgorithm(Exportar_pontos_cotados())
        self.addAlgorithm(Exportar_linhas_de_quebra())
        self.addAlgorithm(Exportar_elemento_associado_de_agua())
        self.addAlgorithm(Exportar_elemento_associado_de_eletricidade())
        self.addAlgorithm(Exportar_cabo_eletrico())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'carttop'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('QGIS to CartTop')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)