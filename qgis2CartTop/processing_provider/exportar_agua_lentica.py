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


class ExportarAguaLentica(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    INPUT = 'INPUT'
    VALOR_AGUA_LENTICA = 'VALOR_AGUA_LENTICA'
    COTA_PLENO_ARMAZENAMENTO = 'COTA_PLENO_ARMAZENAMENTO'
    MARE = 'MARE'

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
                self.tr('Camada de Linhas de Entrada'),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )

        self.val_keys, self.val_values = get_lista_codigos('valorAguaLentica')
        self.addParameter(
            QgsProcessingParameterEnum(
                self.VALOR_AGUA_LENTICA,
                self.tr('Valor Agua Lentica'),
                self.val_keys,
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterBoolean(
                self.COTA_PLENO_ARMAZENAMENTO,
                self.tr('Cota Pleno Armazenamento'),
                defaultValue=0,
                optional=False,
            )
        )


        self.addParameter(
            QgsProcessingParameterBoolean(
                self.MARE,
                self.tr('Mare'),
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
        valor_agua_lentica = self.val_values[
            self.parameterAsEnum(
                parameters,
                self.VALOR_AGUA_LENTICA,
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
                'expression': valor_agua_lentica,
                'length': 255,
                'name': 'valor_agua_lentica',
                'precision': -1,
                'type': 10   
            },{
                'expression': f"\'{parameters['COTA_PLENO_ARMAZENAMENTO']}\'",
                'length': 255,
                'name': 'cota_plena_armazenamento',
                'precision': -1,
                'type': 1   
            },{
                'expression': f"{parameters['MARE']}",
                'length': 255,
                'name': 'mare',
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
            'TABLE': 'agua_lentica',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'exportar_agua_lentica'

    def displayName(self):
        return '01. Exportar Água Lêntica'

    def group(self):
        return '04 - Hidrografia'

    def groupId(self):
        return '04Hidrografia'

    def createInstance(self):
        return ExportarAguaLentica()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr("Exporta elementos do tipo Agua Lentica para a base " \
                       "de dados RECART usando uma ligação PostgreSQL/PostGIS " \
                       "já configurada.\n\n" \
                       "A camada vectorial de input deve ser do tipo polígono 3D."
        )