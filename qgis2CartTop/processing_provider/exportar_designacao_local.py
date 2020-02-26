from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProperty,
                       QgsProcessingParameterBoolean)
import processing
from .utils import get_postgres_connections


class Exportar_designacao_local(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    VALOR_LOCAL_NOMEADO = 'VALOR_LOCAL_NOMEADO'
    POSTGRES_CONNECTION = 'POSTGRES_CONNECTION'


    def initAlgorithm(self, config=None):
        self.postgres_connections_list = get_postgres_connections()

        self.addParameter(
            QgsProcessingParameterEnum(
                self.POSTGRES_CONNECTION,
                self.tr('Ligação PostgreSQL'),
                self.postgres_connections_list,
                defaultValue = 0
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input point layer (2D)'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None
            )
        )

        self.valor_local_nomeado_dict = {
            'Capital do País':'1',
            'Sede administrativa de Região Autónoma':'2',
            'Capital de Distrito':'3',
            'Sede de Concelho':'4',
            'Sede de Freguesia':'5',
            'Forma de relevo':'6',
            'Serra':'6.1',
            'Cabo':'6.2',
            'Ria':'6.3',
            'Pico':'6.4',
            'Península':'6.5',
            'Baía':'6.6',
            'Enseada':'6.7',
            'Ínsua':'6.8',
            'Dunas':'6.9',
            'Fajã':'6.10',
            'Lugar':'7',
            'Cidade':'7.1',
            'Vila':'7.2',
            'Outro aglomerado':'7.3',
            'Designação local':'8',
            'Área protegida':'9',
            'Praia':'10',
            'Oceano':'11',
            'Arquipélago':'12',
            'Ilha':'13',
            'Ilhéu':'14',
            'Outro local nomeado':'15'
        }


        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_LOCAL_NOMEADO,
                self.tr('valorLocalNomeado'),
                list(self.valor_local_nomeado_dict.keys()),
                defaultValue=1,
                optional=False,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Convert enumerator to zero based index value
        valor_local_nomeado = self.parameterAsEnum(
            parameters,
            self.VALOR_LOCAL_NOMEADO,
            context
            ) + 1

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': -1,
                'name': 'inicio_objeto',
                'precision': -1,
                'type': 14
            },{
                'expression': str(valor_local_nomeado),
                'length': 255,
                'name': 'valor_local_nomeado',
                'precision': -1,
                'type': 10
            },{
                'expression': 'nome',
                'length': 255,
                'name': 'nome',
                'precision': -1,
                'type': 10
            }],
            'INPUT': parameters['INPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Export to PostgreSQL (available connections)
        idx = self.parameterAsEnum(
            parameters,
            self.POSTGRES_CONNECTION,
            context
            )

        postgres_connection = self.postgres_connections_list[idx]

        alg_params = {
            'ADDFIELDS': True,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': postgres_connection,
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 3,
            'INDEX': True,
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'LAUNDER': True,
            'OPTIONS': '',
            'OVERWRITE': False,
            'PK': '',
            'PRECISION': True,
            'PRIMARY_KEY': 'identificador',
            'PROMOTETOMULTI': True,
            'SCHEMA': 'public',
            'SEGMENTIZE': '',
            'SHAPE_ENCODING': '',
            'SIMPLIFY': '',
            'SKIPFAILURES': False,
            'SPAT': None,
            'S_SRS': None,
            'TABLE': 'designacao_local',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_designacao_local'

    def displayName(self):
        return '01. Exportar designação local'

    def group(self):
        return '02 - Toponimia'

    def groupId(self):
        return '02toponimia'

    def createInstance(self):
        return Exportar_designacao_local()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo designação local para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto 2D."
        )
