from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProperty,
                       QgsProcessingParameterBoolean,
                       QgsProcessingUtils,
                       QgsProcessingParameterProviderConnection)
import processing
from .utils import get_lista_codigos


class Exportar_cabo_eletrico(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_POSICAO_VERTICAL ='VALOR_POSICAO_VERTICAL'
    VALOR_DESIGNACAO_TENSAO = 'VALOR_DESIGNACAO_TENSAO'


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

        self.vdt_keys, self.vdt_values = get_lista_codigos('valorDesignacaoTensao')


        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_DESIGNACAO_TENSAO,
                self.tr('Valor Designacao Tensao'),
                self.vdt_keys,
                defaultValue=3,
                optional=False,
            )
        )

        self.vpv_keys, self.vpv_values = get_lista_codigos('valorPosicaoVertical')


        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_POSICAO_VERTICAL,
                self.tr('Valor Posicao Vertical'),
                self.vpv_keys,
                defaultValue=1,
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
        valor_designacao_tensao = self.vdt_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_DESIGNACAO_TENSAO,
                context
                )
            ]

        valor_posicao_vertical = self.vpv_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_POSICAO_VERTICAL,
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
                'expression': str(valor_designacao_tensao),
                'length': 255,
                'name': 'valor_designacao_tensao',
                'precision': -1,
                'type': 10
            },{
                'expression': str(valor_posicao_vertical),
                'length': 255,
                'name': 'valor_posicao_vertical',
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
            'ADDFIELDS': False,
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
            'TABLE': 'cabo_electrico',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_cabo_eletrico'

    def displayName(self):
        return '02. Exportar cabo elétrico'

    def group(self):
        return '08 - Infraestruturas e serviços'

    def groupId(self):
        return '08infraestruturas'

    def createInstance(self):
        return Exportar_cabo_eletrico()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo cabo elétrico para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 2D ."
        )