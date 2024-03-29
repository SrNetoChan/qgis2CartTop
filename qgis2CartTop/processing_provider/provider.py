from qgis.core import QgsProcessingProvider
from .exportar_curvas_de_nivel import Exportar_curvas_de_nivel
from .exportar_pontos_cotados import Exportar_pontos_cotados
from .exportar_linhas_de_quebra import Exportar_linhas_de_quebra
from .exportar_elemento_associado_de_agua import Exportar_elemento_associado_de_agua
from .exportar_elemento_associado_de_eletricidade import Exportar_elemento_associado_de_eletricidade
from .exportar_cabo_eletrico import Exportar_cabo_eletrico
from .exportar_construcao_linear import Exportar_construcao_linear
from .exportar_designacao_local import Exportar_designacao_local
from .exportar_unidades_administrativas import ExportarUnidadesAdministrativas
from .exportar_fronteira import ExportarFronteira
from .exportar_agua_lentica import ExportarAguaLentica
from .exportar_barreira import ExportarBarreira
from .exportar_curso_de_agua_area import ExportarCursoDeAguaArea
from .exportar_curso_de_agua_eixo import ExportarCursoDeAguaEixo
from .exportar_fronteira_terra_agua import ExportarFronteiraTerraAgua
from .exportar_margem import ExportarMargem
from .exportar_nascente import ExportarNascente
from .exportar_no_hidrografico import ExportarNoHidrografico
from .exportar_queda_de_agua import ExportarQuedaDeAgua
from .exportar_zona_humida import ExportarZonaHumida
from .exportar_area_infra_trans_aereo import ExportarAreaInfraTransAereo
from .exportar_infra_trans_aereo import ExportarInfraTransAereo
from .exportar_area_infra_trans_ferrov import ExportarAreaInfraTransFerrov
from .exportar_infra_trans_ferrov import ExportarInfraTransFerrov
from .exportar_no_trans_ferrov import ExportarNoTransFerrov
from .exportar_seg_via_ferrea import ExportarSegViaFerrea
from .exportar_area_infra_trans_cabo import ExportarAreaInfraTransCabo
from .exportar_seg_via_cabo import ExportarSegViaCabo
from .exportar_area_infra_trans_via_navegavel import ExportarAreaInfraTransViaNavegavel
from .exportar_infra_trans_via_navegavel import ExportarInfraTransViaNavegavel
from .exportar_area_infra_trans_rodov import ExportarAreaInfraTransRodov
from .exportar_infra_trans_rodov import ExportarInfraTransRodov
from .exportar_no_trans_rodov import ExportarNoTransRodov
from .exportar_seg_via_rodov import ExportarSegViaRodov
from .exportar_via_rodov_limite import ExportarViaRodovLimite
from .exportar_obra_arte import ExportarObraArte
from .exportar_constru_polig import ExportarConstruPolig
from .exportar_edificio import ExportarEdificio
from .exportar_ponto_interesse import ExportarPontoInteresse
from .exportar_sinal_geodesico import ExportarSinalGeodesico
from .exportar_area_agricola_florestal_mato import ExportarAreaAgricolaFlorestalMato
from .exportar_areas_artificializadas import ExportarAreasArtificializadas
from .exportar_conduta_de_agua import ExportarCondutaDeAgua
from .exportar_elem_assoc_pgq import ExportarElemAssocPGQ
from .exportar_elem_assoc_telecomunicacoes import ExportarElemAssocTelecomunicacoes
from .exportar_oleoduto_gasoduto_subtancias_quimicas import ExportarOleodutoGasodutoSubtanciasQuimicas
from .exportar_mob_urbano_sinal import ExportarMobUrbanoSinal
from .exportar_area_trabalho import ExportarAreaTrabalho
from .criar_nos_rodoviarios import CriarNosRodoviarios
from .criar_nos_hidrograficos import CriarNosHidrograficos
from .criar_nos_ferroviarios import CriarNosFerroviarios

class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(Exportar_curvas_de_nivel())
        self.addAlgorithm(Exportar_pontos_cotados())
        self.addAlgorithm(Exportar_linhas_de_quebra())
        self.addAlgorithm(Exportar_elemento_associado_de_agua())
        self.addAlgorithm(Exportar_elemento_associado_de_eletricidade())
        self.addAlgorithm(Exportar_cabo_eletrico())
        self.addAlgorithm(Exportar_construcao_linear())
        self.addAlgorithm(Exportar_designacao_local())
        self.addAlgorithm(ExportarMobUrbanoSinal())
        self.addAlgorithm(ExportarUnidadesAdministrativas())
        self.addAlgorithm(ExportarFronteira())
        self.addAlgorithm(ExportarAguaLentica())
        self.addAlgorithm(ExportarBarreira())
        self.addAlgorithm(ExportarCursoDeAguaArea())
        self.addAlgorithm(ExportarCursoDeAguaEixo())
        self.addAlgorithm(ExportarFronteiraTerraAgua())
        self.addAlgorithm(ExportarMargem())
        self.addAlgorithm(ExportarNascente())
        self.addAlgorithm(ExportarNoHidrografico())
        self.addAlgorithm(ExportarQuedaDeAgua())
        self.addAlgorithm(ExportarZonaHumida())
        self.addAlgorithm(ExportarAreaInfraTransAereo())
        self.addAlgorithm(ExportarInfraTransAereo())
        self.addAlgorithm(ExportarAreaInfraTransFerrov())
        self.addAlgorithm(ExportarInfraTransFerrov())
        self.addAlgorithm(ExportarNoTransFerrov())
        self.addAlgorithm(ExportarSegViaFerrea())
        self.addAlgorithm(ExportarAreaInfraTransCabo())
        self.addAlgorithm(ExportarSegViaCabo())
        self.addAlgorithm(ExportarAreaInfraTransViaNavegavel())
        self.addAlgorithm(ExportarInfraTransViaNavegavel())
        self.addAlgorithm(ExportarAreaInfraTransRodov())
        self.addAlgorithm(ExportarInfraTransRodov())
        self.addAlgorithm(ExportarNoTransRodov())
        self.addAlgorithm(ExportarSegViaRodov())
        self.addAlgorithm(ExportarViaRodovLimite())
        self.addAlgorithm(ExportarObraArte())
        self.addAlgorithm(ExportarConstruPolig())
        self.addAlgorithm(ExportarEdificio())
        self.addAlgorithm(ExportarPontoInteresse())
        self.addAlgorithm(ExportarSinalGeodesico())
        self.addAlgorithm(ExportarAreaAgricolaFlorestalMato())
        self.addAlgorithm(ExportarAreasArtificializadas())
        self.addAlgorithm(ExportarCondutaDeAgua())
        self.addAlgorithm(ExportarElemAssocPGQ())
        self.addAlgorithm(ExportarElemAssocTelecomunicacoes())
        self.addAlgorithm(ExportarOleodutoGasodutoSubtanciasQuimicas())
        self.addAlgorithm(ExportarAreaTrabalho())
        self.addAlgorithm(CriarNosRodoviarios())
        self.addAlgorithm(CriarNosHidrograficos())
        self.addAlgorithm(CriarNosFerroviarios())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'carttop_export'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('QGIS to CartTop (Criação\Exportação)')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)
