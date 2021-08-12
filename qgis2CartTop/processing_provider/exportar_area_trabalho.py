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


class ExportarAreaTrabalho(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    DATA = 'DATA'
    NIVEL_DE_DETALHE = 'NIVEL_DE_DETALHE'
    NOME = 'NOME'
    NOME_DO_PRODUTOR = 'NOME_DO_PRODUTOR'
    NOME_DO_PROPRIETARIO = 'NOME_DO_PROPRIETARIO'

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
                self.tr(' Camada de polígono de entrada'),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.DATA,
                self.tr('Data'),
                defaultValue='1900-01-01',
                optional=False,
            )
        )

        self.nivel_de_detalhe_values = ['NdD1','NdD2']
        self.addParameter(
            QgsProcessingParameterEnum(
                self.NIVEL_DE_DETALHE,
                self.tr('Nivel De Detalhe'),
                options=self.nivel_de_detalhe_values,
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterString(
                self.NOME,
                self.tr('Nome'),
                defaultValue='',
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterString(
                self.NOME_DO_PRODUTOR,
                self.tr('Nome Do Produtor'),
                defaultValue='',
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterString(
                self.NOME_DO_PROPRIETARIO,
                self.tr('Nome Do Proprietario'),
                defaultValue='',
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
        nivel_de_detalhe = self.nivel_de_detalhe_values[
            self.parameterAsEnum(
                parameters,
                self.NIVEL_DE_DETALHE,
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
                'expression': f"\'{parameters['DATA']}\'",
                'length': 255,
                'name': 'data',
                'precision': -1,
                'type': 14   
            },{
                'expression': f"\'{nivel_de_detalhe}\'",
                'length': 255,
                'name': 'nivel_de_detalhe',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['NOME']}\'",
                'length': 255,
                'name': 'nome',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['NOME_DO_PRODUTOR']}\'",
                'length': 255,
                'name': 'nome_produtor',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['NOME_DO_PROPRIETARIO']}\'",
                'length': 255,
                'name': 'nome_proprietario',
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
            'TABLE': 'area_trabalho',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_area_trabalho'

    def displayName(self):
        return '01. Exportar Área de trabalho'

    def group(self):
        return '11 - Auxiliar'

    def groupId(self):
        return '11Auxiliar'

    def createInstance(self):
        return ExportarAreaTrabalho()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Área de trabalho para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo polígono 2D."
        )