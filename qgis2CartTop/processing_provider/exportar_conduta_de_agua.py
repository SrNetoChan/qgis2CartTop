from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterProviderConnection,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProperty,
                       QgsProcessingParameterBoolean)

import processing
from .utils import get_lista_codigos


class ExportarCondutaDeAgua(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CONDUTA_AGUA = 'VALOR_CONDUTA_AGUA'
    VALOR_POSICAO_VERTICAL = 'VALOR_POSICAO_VERTICAL'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                self.LIGACAO_RECART,
                'Ligação PostgreSQL',
                'postgres',
                defaultValue=None
            )
        )

        input_layer = self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr(' Camada de linha de entrada'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )

        self.vca_keys, self.vca_values = get_lista_codigos('valorCondutaAgua')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CONDUTA_AGUA,
                self.tr('Valor Conduta Agua'),
                self.vca_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vpv_keys, self.vpv_values = get_lista_codigos('valorPosicaoVertical')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_POSICAO_VERTICAL,
                self.tr('Valor Posicao Vertical'),
                self.vpv_keys,
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
        valor_conduta_agua = self.vca_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CONDUTA_AGUA,
                context
                )
            ]
        # Convert enumerator to actual value
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
                'expression': valor_conduta_agua,
                'length': 255,
                'name': 'valor_conduta_agua',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_posicao_vertical,
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

        alg_params = {
            'ADDFIELDS': False,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters[self.LIGACAO_RECART],
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 0,
            'INDEX': False,
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'LAUNDER': False,
            'OPTIONS': '',
            'OVERWRITE': False,
            'PK': '',
            'PRECISION': True,
            'PRIMARY_KEY': 'identificador',
            'PROMOTETOMULTI': False,
            'SCHEMA': 'public',
            'SEGMENTIZE': '',
            'SHAPE_ENCODING': '',
            'SIMPLIFY': '',
            'SKIPFAILURES': False,
            'SPAT': None,
            'S_SRS': None,
            'TABLE': 'conduta_de_agua',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_conduta_de_agua'

    def displayName(self):
        return '03. Exportar Conduta de água'

    def group(self):
        return '08 - Infraestruturas e serviços'

    def groupId(self):
        return '08infraestruturas'

    def createInstance(self):
        return ExportarCondutaDeAgua()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Conduta de água para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 2D."
        )