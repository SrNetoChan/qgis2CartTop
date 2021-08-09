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


class ExportarSegViaFerrea(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_CATEGORIA_BITOLA = 'VALOR_CATEGORIA_BITOLA'
    VALOR_ESTADO_LINHA_FERREA = 'VALOR_ESTADO_LINHA_FERREA'
    VALOR_POSICAO_VERTICAL_TRANSPORTES = 'VALOR_POSICAO_VERTICAL_TRANSPORTES'
    VALOR_TIPO_LINHA_FERREA = 'VALOR_TIPO_LINHA_FERREA'
    VALOR_TIPO_TROCO_VIA_FERREA = 'VALOR_TIPO_TROCO_VIA_FERREA'
    ELETRIFIC = 'ELETRIFIC'

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

        self.vcb_keys, self.vcb_values = get_lista_codigos('valorCategoriaBitola')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_CATEGORIA_BITOLA,
                self.tr('Valor Categoria Bitola'),
                self.vcb_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.velf_keys, self.velf_values = get_lista_codigos('valorEstadoLinhaFerrea')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ESTADO_LINHA_FERREA,
                self.tr('Valor Estado Linha Ferrea'),
                self.velf_keys,
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
                defaultValue=0,
                optional=False,
            )
        )


        self.vtlf_keys, self.vtlf_values = get_lista_codigos('valorTipoLinhaFerrea')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_LINHA_FERREA,
                self.tr('Valor Tipo Linha Ferrea'),
                self.vtlf_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.vttvf_keys, self.vttvf_values = get_lista_codigos('valorTipoTrocoViaFerrea')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_TIPO_TROCO_VIA_FERREA,
                self.tr('Valor Tipo Troco Via Ferrea'),
                self.vttvf_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterBoolean(
                self.ELETRIFIC,
                self.tr('Eletrific'),
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
        valor_categoria_bitola = self.vcb_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_CATEGORIA_BITOLA,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_estado_linha_ferrea = self.velf_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ESTADO_LINHA_FERREA,
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
        valor_tipo_linha_ferrea = self.vtlf_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_TIPO_LINHA_FERREA,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_tipo_troco_via_ferrea = self.vttvf_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_TIPO_TROCO_VIA_FERREA,
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
                'expression': valor_categoria_bitola,
                'length': 255,
                'name': 'valor_categoria_bitola',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_estado_linha_ferrea,
                'length': 255,
                'name': 'valor_estado_linha_ferrea',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_posicao_vertical_transportes,
                'length': 255,
                'name': 'valor_posicao_vertical_transportes',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_tipo_linha_ferrea,
                'length': 255,
                'name': 'valor_tipo_linha_ferrea',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_tipo_troco_via_ferrea,
                'length': 255,
                'name': 'valor_tipo_troco_via_ferrea',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['ELETRIFIC']}\'",
                'length': 255,
                'name': 'eletrific',
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
            'TABLE': 'seg_via_ferrea',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_seg_via_ferrea'

    def displayName(self):
        return '07. Exportar Seg Via Ferrea'

    def group(self):
        return '05 - Transportes (Transporte Ferroviário)'

    def groupId(self):
        return '05TransporteFerroviario'

    def createInstance(self):
        return ExportarSegViaFerrea()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Seg Via Ferrea para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo linha 3D."
        )