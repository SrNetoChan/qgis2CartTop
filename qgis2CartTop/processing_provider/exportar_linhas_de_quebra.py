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


class Exportar_linhas_de_quebra(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    VALOR_CLASSIFICA = 'VALOR_CLASSIFICA'
    VALOR_NATUREZA_LINHA = 'VALOR_NATUREZA_LINHA'
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
                self.tr('Input line layer (3D)'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CLASSIFICA,
                self.tr('valorClassifica'),
                ['Base do declive', 'Alteração no declive', 'Linha de forma', 'Linha de talvegue', 'Linha de cumeada', 'Topo do declive'],
                defaultValue=0,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_NATUREZA_LINHA,
                self.tr('valorNaturezaLinha'),
                ['Escarpado', 'Talude', 'Socalco', 'Combro'],
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
        valor_classifica = self.parameterAsEnum(
            parameters,
            self.VALOR_CLASSIFICA,
            context
            ) + 1

        valor_natureza_linha = self.parameterAsEnum(
            parameters,
            self.VALOR_NATUREZA_LINHA,
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