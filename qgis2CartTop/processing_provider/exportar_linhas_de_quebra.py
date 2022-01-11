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


class Exportar_linhas_de_quebra(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CLASSIFICA = 'VALOR_CLASSIFICA'
    VALOR_NATUREZA_LINHA = 'VALOR_NATUREZA_LINHA'


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
                self.tr('Camada de Linhas de Entrada (3D)'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )

        self.vc_keys, self.vc_values = get_lista_codigos('valorClassifica')

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CLASSIFICA,
                self.tr('Valor Classifica'),
                self.vc_keys,
                defaultValue=0,
                optional=False,
            )
        )

        self.vnl_keys, self.vnl_values = get_lista_codigos('valorNaturezaLinha')


        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_NATUREZA_LINHA,
                self.tr('Valor Natureza Linha'),
                self.vnl_keys,
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

        # Convert enumerators to actual values
        valor_classifica = self.vc_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CLASSIFICA,
                context
                )
            ]
        
        valor_natureza_linha = self.vnl_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_NATUREZA_LINHA,
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
                'expression': str(valor_classifica),
                'length': 255,
                'name': 'valor_classifica',
                'precision': -1,
                'type': 10
            },{
                'expression': str(valor_natureza_linha),
                'length': 255,
                'name': 'valor_natureza_linha',
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
            'TABLE': 'linha_de_quebra',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_linhas_de_quebra'

    def displayName(self):
        return '02. Exportar linhas de quebra'

    def group(self):
        return '03 - Altimetria'

    def groupId(self):
        return '03altimetria'

    def createInstance(self):
        return Exportar_linhas_de_quebra()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo linha de quebra para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 3D."
        )