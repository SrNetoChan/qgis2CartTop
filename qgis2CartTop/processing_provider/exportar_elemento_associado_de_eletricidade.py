from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProperty,
                       QgsProcessingParameterBoolean,
                       QgsProcessingUtils,
                       QgsProcessingParameterProviderConnection)
import processing
from .utils import get_lista_codigos


class Exportar_elemento_associado_de_eletricidade(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_ELEMENTO_ASSOCIADO_ELECTRICIDADE = 'VALOR_ELEMENTO_ASSOCIADO_ELECTRICIDADE'

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
                self.tr('Input point or polygon layer (2D)'),
                types=[QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )

        self.veae_keys, self.veae_values = get_lista_codigos('valorElementoAssociadoElectricidade')

        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_ELEMENTO_ASSOCIADO_ELECTRICIDADE,
                self.tr('valorElementoAssociadoElectricidade'),
                self.veae_keys,
                defaultValue=0,
                optional=False,
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # Convert enumerator to actual value
        valor_associado_eletricidade = self.veae_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_ELEMENTO_ASSOCIADO_ELECTRICIDADE,
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
                'expression': str(valor_associado_eletricidade),
                'length': 255,
                'name': 'valor_elemento_associado_electricidade',
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

        # Sanitize Z and M values from 3D Layers
        # Input table only accepts 2D
        alg_params = {
            'DROP_M_VALUES': True,
            'DROP_Z_VALUES': True,
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DropMzValues'] = processing.run('native:dropmzvalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Export to PostgreSQL (available connections)

        # Because the target layer is of the geometry type, one needs to make
        # sure to use the correct option when importing into PostGIS
        layer = QgsProcessingUtils.mapLayerFromString(outputs['DropMzValues']['OUTPUT'], context)
        if layer.geometryType() == 0:
            gtype = 3
        elif layer.geometryType() == 2:
            gtype = 5

        alg_params = {
            'ADDFIELDS': True,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters[self.LIGACAO_RECART],
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': gtype,
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
            'TABLE': 'elem_assoc_eletricidade',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_elemento_associado_de_eletricidade'

    def displayName(self):
        return '05. Exportar elemento associado de eletricidade'

    def group(self):
        return '08 - Infraestruturas e serviços'

    def groupId(self):
        return '08infraestruturas'

    def createInstance(self):
        return Exportar_elemento_associado_de_eletricidade()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo elemento associado de eletricidade para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo ponto ou polígono 2D ."
        )