from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProperty,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterProviderConnection)
import processing
from .utils import get_lista_codigos


class Exportar_pontos_cotados(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CLASSIFICA_LAS = 'VALOR_CLASSIFICA_LAS'


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
                self.tr('Camada de Pontos de Entrada (3D)'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None
            )
        )

        self.vcl_keys, self.vcl_values = get_lista_codigos('valorClassificaLAS')

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CLASSIFICA_LAS,
                self.tr('Valor Classifica LAS'),
                self.vcl_keys,
                defaultValue=0,
                optional=False,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Convert enumerator to actual value
        valor_classifica_las = self.vcl_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CLASSIFICA_LAS,
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
                'expression': valor_classifica_las,
                'length': 255,
                'name': 'valor_classifica_las',
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

        alg_params = {
            'ADDFIELDS': False,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters[self.LIGACAO_RECART],
            'DIM': 1,
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
            'TABLE': 'ponto_cotado',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_postos_cotados'

    def displayName(self):
        return '03. Exportar pontos cotados'

    def group(self):
        return '03 - Altimetria'

    def groupId(self):
        return '03altimetria'

    def createInstance(self):
        return Exportar_pontos_cotados()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo ponto cotado para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto 3D."
        )