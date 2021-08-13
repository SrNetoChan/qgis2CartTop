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


class Exportar_curvas_de_nivel(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    HOMOGENIZE_Z_VALUES = 'HOMOGENIZE_Z_VALUES'
    VALOR_TIPO_CURVA = 'VALOR_TIPO_CURVA'
    NIVEL_DE_DETALHE = 'NIVEL_DE_DETALHE'


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

        self.vtc_keys, self.vtc_values = get_lista_codigos('valorTipoCurva')
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_CURVA,
                self.tr('Valor tipo curva'),
                self.vtc_keys,
                defaultValue = 1
            )
        )

        self.ndd_dict = {
            'Skip':'0',
            'NdD1':'2',
            'NdD2':'5'
        }

        self.addParameter(
            QgsProcessingParameterEnum(
                self.NIVEL_DE_DETALHE,
                self.tr('Determinar Valor Tipo Curva pelo nível de detalhe'),
                optional=True,
                options = list(self.ndd_dict.keys()),
                defaultValue = 0
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Check if homogenize

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        n_steps = 3
        if parameters[self.HOMOGENIZE_Z_VALUES]:
            n_steps += 1

        feedback = QgsProcessingMultiStepFeedback(n_steps, model_feedback)
        results = {}
        outputs = {}

        # Extract Z values (majority) for further use in
        # Homogenize Z values or Nivel de detalhe
        alg_params = {
            'COLUMN_PREFIX': 'z_',
            'INPUT': parameters['INPUT'],
            'SUMMARIES': [11],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractZValues'] = processing.run('native:extractzvalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Convert enumerator to actual value
        valor_tipo_curva = self.parameterAsEnum(
            parameters,
            self.VALOR_TIPO_CURVA,
            context
            )

        vtc_exp = self.vtc_values[valor_tipo_curva]
        
        # If nivel de detalhe is set, automatically determine which value of Valor Tipo Curva to use
        if parameters[self.NIVEL_DE_DETALHE] != 0:
            vtc_exp = f"CASE WHEN z_majority % {parameters[self.NIVEL_DE_DETALHE] * 5} = 0 THEN '1'"  \
                             f"WHEN z_majority % {parameters[self.NIVEL_DE_DETALHE]} = 0 THEN '2'" \
                             f"ELSE '3' END"

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': -1,
                'name': 'inicio_objeto',
                'precision': -1,
                'type': 14
            },{
                'expression': vtc_exp,
                'length': 255,
                'name': 'valor_tipo_curva',
                'precision': -1,
                'type': 10
            },{
                'expression': 'z_majority',
                'length': -1,
                'name': 'z_majority',
                'precision': -1,
                'type': 2
            }],
            'INPUT': outputs['ExtractZValues']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('qgis:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        if parameters[self.HOMOGENIZE_Z_VALUES]:
            # Use z_majority values to Set Z value
            alg_params = {
                'INPUT': outputs['RefactorFields']['OUTPUT'],
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
                       "A opção Homogenize Z Values permite corrigir vertices " \
                       "com valores anómalos em Z comparados com os restantes.\n\n" \
                       "Quando seleccionado um nível de detalhe o valor tipo curva será " \
                       "definido automaticamente tendo em conta o valor de cota de cada curva"
                       )
