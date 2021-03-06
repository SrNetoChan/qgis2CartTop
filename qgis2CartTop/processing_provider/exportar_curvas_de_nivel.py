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


class Exportar_curvas_de_nivel(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    HOMOGENIZE_Z_VALUES = 'HOMOGENIZE_Z_VALUES'
    VALOR_TIPO_CURVA = 'VALOR_TIPO_CURVA'
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
            QgsProcessingParameterBoolean(
                self.HOMOGENIZE_Z_VALUES,
                'Homogenize Z values'
            )
        )

        self.valor_tipo_curva_dict = {
            'Mestra':'1',
            'Secundária':'2',
            'Auxiliar':'3'
        }

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_CURVA,
                self.tr('Valor tipo curva'),
                list(self.valor_tipo_curva_dict.keys()),
                defaultValue = 1
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Check if homogenize

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        if parameters[self.HOMOGENIZE_Z_VALUES]:
            feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        else:
            feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Convert enumerator to zero based index value
        valor_tipo_curva = self.parameterAsEnum(
            parameters,
            self.VALOR_TIPO_CURVA,
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
                'expression': str(valor_tipo_curva),
                'length': 255,
                'name': 'valor_tipo_curva',
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

        if parameters[self.HOMOGENIZE_Z_VALUES]:
            # If Homogenize Z Values option is checked
            # Correct possible wrong Z values along lines
            # Extract Z values
            alg_params = {
                'COLUMN_PREFIX': 'z_',
                'INPUT': outputs['RefactorFields']['OUTPUT'],
                'SUMMARIES': [11],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ExtractZValues'] = processing.run('native:extractzvalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(2)
            if feedback.isCanceled():
                return {}

            # Set Z value
            alg_params = {
                'INPUT': outputs['ExtractZValues']['OUTPUT'],
                'Z_VALUE': QgsProperty.fromExpression('"z_majority"'),
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['SetZValue'] = processing.run('qgis:setzvalue', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

            feedback.setCurrentStep(3)
            if feedback.isCanceled():
                return {}
        else:
            outputs['SetZValue'] = outputs['RefactorFields']

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
            'INPUT': outputs['SetZValue']['OUTPUT'],
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
            'TABLE': 'curva_de_nivel',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_curvas_de_nivel'

    def displayName(self):
        return '01. Exportar curvas de nível'

    def group(self):
        return '03 - Altimetria'

    def groupId(self):
        return '03altimetria'

    def createInstance(self):
        return Exportar_curvas_de_nivel()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo curva de nível para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 3D.\n\n" \
                       "A opção Homogenize Z Values permite corrigir vertices "
                       "com valores anómalos em Z comparados com os restantes.")
