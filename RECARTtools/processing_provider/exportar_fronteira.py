from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterProviderConnection,
                       QgsProcessingParameterString,
                       QgsProperty,
                       QgsProcessingParameterBoolean)
import processing
from .utils import get_lista_codigos


class ExportarFronteira(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_ESTADO_FRONTEIRA = 'VALOR_ESTADO_FRONTEIRA'
    DATA_PUBLICACAO = 'DATA_PUBLICACAO'


    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.LIGACAO_RECART,
                'Ligação PostgreSQL',
                'postgres',
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input line layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )

        self.vef_keys, self.vef_values = get_lista_codigos('valorEstadoFronteira')

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ESTADO_FRONTEIRA,
                self.tr('Valor Estado Fronteira'),
                self.vef_keys,
                defaultValue=0,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.DATA_PUBLICACAO, 
                'Data de publicação',
                multiLine=False, 
                defaultValue='2021-02-05'
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Convert enumerator to actual value
        valor_estado_fronteira = self.vef_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ESTADO_FRONTEIRA,
                context
                )
            ]

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': -1,
                'name': 'inicio_objeto',
                'precision': -1,
                'type': 14
            },{
                'expression': valor_estado_fronteira,
                'length': 255,
                'name': 'valor_estado_fronteira',
                'precision': -1,
                'type': 10
            },{
                'expression': f"\'{parameters['DATA_PUBLICACAO']}\'",
                'length': 255,
                'name': 'data_publicacao',
                'precision': 0,
                'type': 14
            }],
            'INPUT': parameters['INPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'ADDFIELDS': True,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters[self.LIGACAO_RECART],
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 4,
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
            'TABLE': 'fronteira',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_fronteira'

    def displayName(self):
        return '04. Exportar fronteira'

    def group(self):
        return '01 - Unidades Administrativas'

    def groupId(self):
        return '01UnidadesAdministrativas'

    def createInstance(self):
        return ExportarFronteira()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo fronteira para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 2D."
        )