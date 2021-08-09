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


class ExportarCursoDeAguaEixo(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CURSO_DE_AGUA = 'VALOR_CURSO_DE_AGUA'
    VALOR_POSICAO_VERTICAL = 'VALOR_POSICAO_VERTICAL'
    DELIMITACAO_CONHECIDA = 'DELIMITACAO_CONHECIDA'
    FICTICIO = 'FICTICIO'

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

        self.vcda_keys, self.vcda_values = get_lista_codigos('valorCursoDeAgua')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CURSO_DE_AGUA,
                self.tr('Valor Curso De Agua'),
                self.vcda_keys,
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
                defaultValue=1,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterBoolean(
                self.DELIMITACAO_CONHECIDA,
                self.tr('Delimitacao Conhecida'),
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FICTICIO,
                self.tr('Ficticio'),
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
        valor_curso_de_agua = self.vcda_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CURSO_DE_AGUA,
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
                'expression': valor_curso_de_agua,
                'length': 255,
                'name': 'valor_curso_de_agua',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_posicao_vertical,
                'length': 255,
                'name': 'valor_posicao_vertical',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['DELIMITACAO_CONHECIDA']}\'",
                'length': 255,
                'name': 'delimitacao_conhecida',
                'precision': -1,
                'type': 1   
            },{
                'expression': f"\'{parameters['FICTICIO']}\'",
                'length': 255,
                'name': 'ficticio',
                'precision': -1,
                'type': 1
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
            'DIM': 1,
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
            'TABLE': 'curso_de_agua_eixo',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_curso_de_agua_eixo'

    def displayName(self):
        return '04. Exportar Curso de Água (Eixo)'

    def group(self):
        return '04 - Hidrografia'

    def groupId(self):
        return '04Hidrografia'

    def createInstance(self):
        return ExportarCursoDeAguaEixo()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Curso De Agua Eixo para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 3D."
        )