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
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterField)

import processing
from .utils import get_lista_codigos


class ExportarNoTransRodov(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_TIPO_NO_TRANS_RODOV = 'VALOR_TIPO_NO_TRANS_RODOV'
    CAMPO_COM_TIPO_NO_TRANS_RODOV = 'CAMPO_COM_TIPO_NO_TRANS_RODOV'

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
                self.tr(' Camada de ponto de entrada'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None
            )
        )

        self.vtntr_keys, self.vtntr_values = get_lista_codigos('valorTipoNoTransRodov')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_NO_TRANS_RODOV,
                self.tr('Valor Tipo No Trans Rodov'),
                self.vtntr_keys,
                defaultValue=0,
                optional=False,
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_COM_TIPO_NO_TRANS_RODOV,
                self.tr(' Campo com tipo de nó de Transporte Rodoviário'),
                type=QgsProcessingParameterField.String,
                parentLayerParameterName=self.INPUT,
                allowMultiple=False,
                defaultValue='',
                optional=True,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Convert enumerator to actual value
        valor_tipo_no_trans_rodov = self.vtntr_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_TIPO_NO_TRANS_RODOV,
                context
                )
            ]

        expression = valor_tipo_no_trans_rodov
        
        # Get the name of the selected fields
        campo_com_tipo_no_trans_rodov = self.parameterAsString(
            parameters,
            self.CAMPO_COM_TIPO_NO_TRANS_RODOV,
            context
        )

        # If nivel de detalhe is set, automatically determine which value of Valor Tipo Curva to use
        if campo_com_tipo_no_trans_rodov != '':
            expression = f'\"{campo_com_tipo_no_trans_rodov}\"'

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': -1,
                'name': 'inicio_objeto',
                'precision': -1,
                'type': 14
   
            },{
                'expression': expression,
                'length': 255,
                'name': 'valor_tipo_no_trans_rodov',
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
            'TABLE': 'no_trans_rodov',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_no_trans_rodov'

    def displayName(self):
        return '14. Exportar Nó de transporte rodoviário'

    def group(self):
        return '05 - Transportes (Transporte Rodoviário)'

    def groupId(self):
        return '05TransporteRodoviario'

    def createInstance(self):
        return ExportarNoTransRodov()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Nó de transporte rodoviário para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto 3D.\n\n" \
                       "Opcionalmente, é possível indicar um campo que contenha valores " \
                       "do tipo de nó de transporte rodoviário, sobrepondo-se ao valor " \
                       "escolhido na opção Valor Tipo No Trans Rodov."
        )