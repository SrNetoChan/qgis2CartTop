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


class ExportarInfraTransAereo(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CATEGORIA_INFRA_TRANS_AEREO = 'VALOR_CATEGORIA_INFRA_TRANS_AEREO'
    VALOR_TIPO_INFRA_TRANS_AEREO = 'VALOR_TIPO_INFRA_TRANS_AEREO'

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

        self.vcita_keys, self.vcita_values = get_lista_codigos('valorCategoriaInfraTransAereo')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CATEGORIA_INFRA_TRANS_AEREO,
                self.tr('Valor Categoria Infra Trans Aereo'),
                self.vcita_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vtita_keys, self.vtita_values = get_lista_codigos('valorTipoInfraTransAereo')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_INFRA_TRANS_AEREO,
                self.tr('Valor Tipo Infra Trans Aereo'),
                self.vtita_keys,
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
        valor_categoria_infra_trans_aereo = self.vcita_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CATEGORIA_INFRA_TRANS_AEREO,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_tipo_infra_trans_aereo = self.vtita_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_TIPO_INFRA_TRANS_AEREO,
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
                'expression': valor_categoria_infra_trans_aereo,
                'length': 255,
                'name': 'valor_categoria_infra_trans_aereo',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_tipo_infra_trans_aereo,
                'length': 255,
                'name': 'valor_tipo_infra_trans_aereo',
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
            'TABLE': 'infra_trans_aereo',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_infra_trans_aereo'

    def displayName(self):
        return '02. Exportar Infra Trans Aereo'

    def group(self):
        return '05 - Transportes (Transporte Aéreo)'

    def groupId(self):
        return '05TransporteAereo'

    def createInstance(self):
        return ExportarInfraTransAereo()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Infra Trans Aereo para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto 2D."
        )