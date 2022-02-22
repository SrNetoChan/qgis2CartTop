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
        self.addParameter(QgsProcessingParameterFeatureSink('NosHidrograficos', 'Nós hidrográficos', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(7, model_feedback)
        results = {}
        outputs = {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': '$id','length': 0,'name': 'id','precision': 0,'type': 4}],
            'INPUT': parameters['cursoaguaeixo'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Extrair vértices específicos
        alg_params = {
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'VERTICES': '0, -1',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtrairVrticesEspecficos'] = processing.run('native:extractspecificvertices', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Eliminar geometrias duplicadas
        alg_params = {
            'INPUT': outputs['ExtrairVrticesEspecficos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['EliminarGeometriasDuplicadas'] = processing.run('qgis:deleteduplicategeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
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

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': outputs['UnirAtributosPelaLocalizaoSumrio']['OUTPUT'],
            'OVERLAY': parameters['readetrabalho'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Multipart to single part
        alg_params = {
            'INPUT': outputs['Clip']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['MultipartToSingleparts'] = processing.run('native:multiparttosingleparts', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{'expression': 'CASE WHEN id_count = 1 THEN \n\t\'1\' -- inicio\nWHEN id_count = 2 THEN\n\'4\' --pseudo-no\nWHEN id_count > 2 THEN\n\'3\' -- juncao\nEND','length': 10,'name': 'valor_tipo_no_hidrografico','precision': 0,'type': 10}],
            'INPUT': outputs['MultipartToSingleparts']['OUTPUT'],
            'OUTPUT': parameters['NosHidrograficos']
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['NosHidrograficos'] = outputs['RefactorFields']['OUTPUT']
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
        return self.tr("Cria camada de nós hidrográficos com base " \
                        "numa camada de Curso de água - eixos. \n\n Usando o número de " \
                        "ligações que o nó estabelece, tenta adivinhar o tipo" \
                        "de nó (2 ou mais ligações: junção; 1 ligação: pseudo-no " \
                        "; nenhuma ligação: Inicio). \n\n" \
                        "Nós fora da área de trabalho são eliminados."
        )
