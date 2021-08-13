from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterString,
                       QgsProperty,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterProviderConnection)
import processing
from .utils import get_lista_codigos


class Exportar_construcao_linear(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CONSTRUCAO_LINEAR = 'VALOR_CONSTRUCAO_LINEAR'
    LARGURA = 'LARGURA'
    NOME = 'NOME'
    SUPORTE = 'SUPORTE'


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
                self.tr('Camada de Linhas de Entrada (2D)'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )

        self.vcl_keys, self.vcl_values = get_lista_codigos('valorConstrucaoLinear')

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CONSTRUCAO_LINEAR,
                self.tr('Valor Construcao Linear'),
                self.vcl_keys,
                defaultValue=0,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.LARGURA,
                self.tr('largura'),
                defaultValue=None,
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.NOME,
                self.tr('nome'),
                defaultValue=None,
                optional=True,
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SUPORTE,
                self.tr('suporte'),
                defaultValue=0,
                optional=False,
            )
        )




    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)

        results = {}
        outputs = {}

        # Convert enumerator(s) to actual values
        valor_construcao_linear = self.vcl_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CONSTRUCAO_LINEAR,
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
            }, {
                'expression': valor_construcao_linear,
                'length': 255,
                'name': 'valor_construcao_linear',
                'precision': -1,
                'type': 10
            }, {
                'expression': str(parameters['NOME']),
                'length': 255,
                'name': 'nome',
                'precision': -1,
                'type': 10
            }, {
                'expression': str(parameters['SUPORTE']),
                'length': -1,
                'name': 'suporte',
                'precision': -1,
                'type': 1
            }, {
                'expression': parameters['LARGURA'],
                'length': -1,
                'name': 'largura',
                'precision': -1,
                'type': 6
            }],
            'INPUT': parameters['INPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        outputs['RefactorFields'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Sanitize Z and M values from 3D Layers
        # Input table only accepts 2D
        alg_params = {
            'DROP_M_VALUES': True,
            'DROP_Z_VALUES': True,
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DropMzValues'] = processing.run('native:dropmzvalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        alg_params = {
            'ADDFIELDS': True,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters[self.LIGACAO_RECART],
            'DIM': 1,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 4,
            'INDEX': True,
            'INPUT': outputs['DropMzValues']['OUTPUT'],
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
            'TABLE': 'constru_linear',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_construcao_linear'

    def displayName(self):
        return '01. Exportar construção linear'

    def group(self):
        return '06 - Construções'

    def groupId(self):
        return '06Construcoes'

    def createInstance(self):
        return Exportar_construcao_linear()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo construcao linear para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 2D.\n\n" \
                       "Camadas 3D irão perder os valores de Z.")
