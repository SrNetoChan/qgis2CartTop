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


class ExportarEdificio(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_ELEMENTO_EDIFICIO_XY = 'VALOR_ELEMENTO_EDIFICIO_XY'
    VALOR_ELEMENTO_EDIFICIO_Z = 'VALOR_ELEMENTO_EDIFICIO_Z'
    ALTURA_EDIFICIO = 'ALTURA_EDIFICIO'

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
                self.tr(' Camada de ponto ou polígono de entrada'),
                types=[QgsProcessing.TypeVectorPoint, QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )

        self.veex_keys, self.veex_values = get_lista_codigos('valorElementoEdificioXY')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ELEMENTO_EDIFICIO_XY,
                self.tr('Valor Elemento Edificio Xy'),
                self.veex_keys,
                defaultValue=3,
                optional=False,
            )
        )


        self.veez_keys, self.veez_values = get_lista_codigos('valorElementoEdificioZ')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ELEMENTO_EDIFICIO_Z,
                self.tr('Valor Elemento Edificio Z'),
                self.veez_keys,
                defaultValue=13,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterNumber(
                self.ALTURA_EDIFICIO,
                self.tr('Altura Edificio'),
                type=1,
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
        valor_elemento_edificio_xy = self.veex_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ELEMENTO_EDIFICIO_XY,
                context
                )
            ]
        # Convert enumerator to actual value
        valor_elemento_edificio_z = self.veez_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ELEMENTO_EDIFICIO_Z,
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
                'expression': valor_elemento_edificio_xy,
                'length': 255,
                'name': 'valor_elemento_edificio_xy',
                'precision': -1,
                'type': 10   
            },{
                'expression': valor_elemento_edificio_z,
                'length': 255,
                'name': 'valor_elemento_edificio_z',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['ALTURA_EDIFICIO']}\'",
                'length': 255,
                'name': 'altura_edificio',
                'precision': -1,
                'type': 6
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
            'TABLE': 'edificio',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_edificio'

    def displayName(self):
        return '03. Exportar Edifício'

    def group(self):
        return '06 - Construções'

    def groupId(self):
        return '06Construcoes'

    def createInstance(self):
        return ExportarEdificio()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Edifício para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto ou polígono 2D."
        )