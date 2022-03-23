from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.PyQt.QtCore import QCoreApplication
import processing


class CriarNosHidrograficos(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('readetrabalho', 'Área de trabalho', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('cursoaguaeixo', 'Curso de água - eixo', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('barreira', 'Barreira', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('zonahumida', 'Zona húmida', defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('quedadeagua', 'Queda de água', defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('noshidrograficos', 'Nós hidrográficos', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
        results = {}
        outputs = {}

        alg_params = {
            'EXPRESSION': 'CASE WHEN\nz(start_point($geometry)) <= z(end_point($geometry)) THEN\nreverse($geometry)\nELSE\n$geometry\nEND',
            'INPUT': parameters['cursoaguaeixo'],
            'OUTPUT_GEOMETRY': 1,
            'WITH_M': False,
            'WITH_Z': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['GeometryByExpression'] = processing.run('native:geometrybyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '$id','length': 0,'name': 'id','precision': 0,'type': 4}],
            'INPUT': outputs['GeometryByExpression']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Extrair vértices específicos
        alg_params = {
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'VERTICES': '0, -1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairVrticesEspecficos'] = processing.run('native:extractspecificvertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Eliminar geometrias duplicadas
        alg_params = {
            'INPUT': outputs['ExtrairVrticesEspecficos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EliminarGeometriasDuplicadas'] = processing.run('qgis:deleteduplicategeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Unir atributos pela localização (sumário)
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['EliminarGeometriasDuplicadas']['OUTPUT'],
            'JOIN': outputs['RefactorFields']['OUTPUT'],
            'JOIN_FIELDS': ['id'],
            'PREDICATE': [0],
            'SUMMARIES': [0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['UnirAtributosPelaLocalizaoSumrio'] = processing.run('qgis:joinbylocationsummary', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': outputs['UnirAtributosPelaLocalizaoSumrio']['OUTPUT'],
            'OVERLAY': parameters['readetrabalho'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Multipart to single part
        alg_params = {
            'INPUT': outputs['Clip']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MultipartToSingleparts'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Join attributes by location barreira
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['MultipartToSingleparts']['OUTPUT'],
            'JOIN': parameters['barreira'],
            'JOIN_FIELDS': ['identificador'],
            'METHOD': 1,
            'PREDICATE': [0,3],
            'PREFIX': 'barreira_',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByLocationBarreira'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Join attributes by location queda de agua
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['JoinAttributesByLocationBarreira']['OUTPUT'],
            'JOIN': parameters['quedadeagua'],
            'JOIN_FIELDS': ['identificador'],
            'METHOD': 1,
            'PREDICATE': [0,3],
            'PREFIX': 'queda_de_agua_',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByLocationQuedaDeAgua'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Join attributes by location zona humida
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['JoinAttributesByLocationQuedaDeAgua']['OUTPUT'],
            'JOIN': parameters['zonahumida'],
            'JOIN_FIELDS': ['identificador'],
            'METHOD': 0,
            'PREDICATE': [0,3],
            'PREFIX': 'zona_humida_',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['JoinAttributesByLocationZonaHumida'] = processing.run('native:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        # Refactor fields

        expression = """
        CASE WHEN id_count = 1 THEN
			CASE WHEN "vertex_pos" = 0 THEN
				'1' -- inicio
			ELSE
				'2' -- fim
			END
        WHEN id_count = 2 THEN
			CASE WHEN  "barreira_identificador" is not NULL THEN
				'6' -- regulacao de fluxo
			WHEN  "queda_de_agua_identificador" is not NULL  or  "zona_humida_identificador" is not NULL THEN
				'5' -- variacao de fluxo
			ELSE
				'4' -- pseudo-no
			END
        WHEN id_count > 2 THEN
        '3' -- juncao
        END
        """
        alg_params = {
            'FIELDS_MAPPING': [{'expression': expression ,'length': 10,'name': 'valor_tipo_no_hidrografico','precision': 0,'type': 10}],
            'INPUT': outputs['JoinAttributesByLocationZonaHumida']['OUTPUT'],
            'OUTPUT': parameters['noshidrograficos']
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['noshidrograficos'] = outputs['RefactorFields']['OUTPUT']

        context.layerToLoadOnCompletionDetails(results['noshidrograficos']).name = "Nós hidrográficos"

        return results

    def name(self):
        return 'criar_nos_hidrograficos'

    def displayName(self):
        return '08. Criar nós higrográficos'

    def group(self):
        return '04 - Hidrografia'

    def groupId(self):
        return '04Hidrografia'

    def createInstance(self):
        return CriarNosHidrograficos()
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr(
            """Cria camada de nós hidrográficos com base numa camada de Curso de água - eixos. 
            Usando o número de ligações que o nó estabelece e sobreposição com outras camadas tenta classificar o tipo" de nó."""
        )
