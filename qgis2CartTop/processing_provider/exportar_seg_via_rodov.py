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


class ExportarSegViaRodov(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_ESTADO_VIA_RODOV = 'VALOR_ESTADO_VIA_RODOV'
    VALOR_CARACT_FISICA_VIA_RODOV = 'VALOR_CARACT_FISICA_VIA_RODOV'
    VALOR_POSICAO_VERTICAL_TRANSPORTES = 'VALOR_POSICAO_VERTICAL_TRANSPORTES'
    VALOR_SENTIDO = 'VALOR_SENTIDO'
    VALOR_TIPO_TROCO_RODOVIARIO = 'VALOR_TIPO_TROCO_RODOVIARIO'
    NUM_VIAS_TRANSITO = 'NUM_VIAS_TRANSITO'
    PAVIMENTADO = 'PAVIMENTADO'

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

        self.vevr_keys, self.vevr_values = get_lista_codigos('valorEstadoViaRodov')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ESTADO_VIA_RODOV,
                self.tr('Valor Estado Via Rodov'),
                self.vevr_keys,
                defaultValue=4,
                optional=False,
            )
        )


        self.vcfvr_keys, self.vcfvr_values = get_lista_codigos('valorCaractFisicaViaRodov')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CARACT_FISICA_VIA_RODOV,
                self.tr('Valor Caract Fisica Via Rodov'),
                self.vcfvr_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vpvt_keys, self.vpvt_values = get_lista_codigos('valorPosicaoVerticalTransportes')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_POSICAO_VERTICAL_TRANSPORTES,
                self.tr('Valor Posicao Vertical Transportes'),
                self.vpvt_keys,
                defaultValue=3,
                optional=False,
            )
        )


        self.vs_keys, self.vs_values = get_lista_codigos('valorSentido')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_SENTIDO,
                self.tr('Valor Sentido'),
                self.vs_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vttr_keys, self.vttr_values = get_lista_codigos('valorTipoTrocoRodoviario')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_TROCO_RODOVIARIO,
                self.tr('Valor Tipo Troco Rodoviario'),
                self.vttr_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.NUM_VIAS_TRANSITO,
                self.tr('Num Vias Transito'),
                type=0,
                defaultValue=2,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PAVIMENTADO,
                self.tr('Pavimentado'),
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

        # Convert enumerator to actual value
        valor_estado_via_rodov = self.vevr_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ESTADO_VIA_RODOV,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_caract_fisica_via_rodov = self.vcfvr_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CARACT_FISICA_VIA_RODOV,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_posicao_vertical_transportes = self.vpvt_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_POSICAO_VERTICAL_TRANSPORTES,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_sentido = self.vs_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_SENTIDO,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_tipo_troco_rodoviario = self.vttr_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_TIPO_TROCO_RODOVIARIO,
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
                'expression': valor_estado_via_rodov,
                'length': 255,
                'name': 'valor_estado_via_rodov',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_caract_fisica_via_rodov,
                'length': 255,
                'name': 'valor_caract_fisica_rodov',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_posicao_vertical_transportes,
                'length': 255,
                'name': 'valor_posicao_vertical_transportes',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_sentido,
                'length': 255,
                'name': 'valor_sentido',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_tipo_troco_rodoviario,
                'length': 255,
                'name': 'valor_tipo_troco_rodoviario',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['NUM_VIAS_TRANSITO']}\'",
                'length': 255,
                'name': 'num_vias_transito',
                'precision': -1,
                'type': 2   
            },{
                'expression': f"\'{parameters['PAVIMENTADO']}\'",
                'length': 255,
                'name': 'pavimentado',
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
            'TABLE': 'seg_via_rodov',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_seg_via_rodov'

    def displayName(self):
        return '15. Exportar Segmento da via rodoviária'

    def group(self):
        return '05 - Transportes (Transporte Rodoviário)'

    def groupId(self):
        return '05TransporteRodoviario'

    def createInstance(self):
        return ExportarSegViaRodov()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Segmento da via rodoviária para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 3D."
        )