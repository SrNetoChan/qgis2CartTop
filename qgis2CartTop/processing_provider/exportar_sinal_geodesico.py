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


class ExportarSinalGeodesico(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_LOCAL_GEODESICO = 'VALOR_LOCAL_GEODESICO'
    VALOR_ORDEM = 'VALOR_ORDEM'
    VALOR_TIPO_SINAL_GEODESICO = 'VALOR_TIPO_SINAL_GEODESICO'
    DATA_REVISAO = 'DATA_REVISAO'

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

        self.vlg_keys, self.vlg_values = get_lista_codigos('valorLocalGeodesico')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_LOCAL_GEODESICO,
                self.tr('Valor Local Geodesico'),
                self.vlg_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vo_keys, self.vo_values = get_lista_codigos('valorOrdem')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ORDEM,
                self.tr('Valor Ordem'),
                self.vo_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vtsg_keys, self.vtsg_values = get_lista_codigos('valorTipoSinalGeodesico')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_SINAL_GEODESICO,
                self.tr('Valor Tipo Sinal Geodesico'),
                self.vtsg_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterString(
                self.DATA_REVISAO,
                self.tr('Data Revisao'),
                defaultValue='1900-01-01',
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
        valor_local_geodesico = self.vlg_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_LOCAL_GEODESICO,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_ordem = self.vo_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ORDEM,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_tipo_sinal_geodesico = self.vtsg_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_TIPO_SINAL_GEODESICO,
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
                'expression': valor_local_geodesico,
                'length': 255,
                'name': 'valor_local_geodesico',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_ordem,
                'length': 255,
                'name': 'valor_ordem',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_tipo_sinal_geodesico,
                'length': 255,
                'name': 'valor_tipo_sinal_geodesico',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['DATA_REVISAO']}\'",
                'length': 255,
                'name': 'data_revisao',
                'precision': -1,
                'type': 14
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
            'TABLE': 'sinal_geodesico',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_sinal_geodesico'

    def displayName(self):
        return '05. Exportar Sinal geodésico'

    def group(self):
        return '06 - Construções'

    def groupId(self):
        return '06Construcoes'

    def createInstance(self):
        return ExportarSinalGeodesico()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Sinal geodésico para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto 3D."
        )