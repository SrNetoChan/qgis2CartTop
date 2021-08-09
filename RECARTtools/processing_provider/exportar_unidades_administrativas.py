from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterProviderConnection
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterBoolean
import processing

class ExportarUnidadesAdministrativas(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterProviderConnection(
                'LigaoBasedeDadosRECART',
                'Ligação PostgreSQL',
                'postgres',
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'CAOP', 
                'CAOP', 
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                'Datadepublicacao', 
                'Data de publicação',
                multiLine=False, 
                defaultValue='2021-02-05'
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'AreadeTrabalho', 
                'Area de Trabalho', 
                types=[QgsProcessing.TypeVectorPolygon], 
                defaultValue=None
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                'VERBOSE_LOG', 
                'Verbose logging',
                optional=True,
                defaultValue=False
            )
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(13, model_feedback)
        results = {}
        outputs = {}

        # Extract by location
        alg_params = {
            'INPUT': parameters['CAOP'],
            'INTERSECT': parameters['AreadeTrabalho'],
            'PREDICATE': [0],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # List unique concelhos
        alg_params = {
            'FIELDS': ['Concelho'],
            'INPUT': outputs['ExtractByLocation']['OUTPUT']
        }
        outputs['ListUniqueConcelhos'] = processing.run('qgis:listuniquevalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # List unique distritos
        alg_params = {
            'FIELDS': ['Distrito'],
            'INPUT': outputs['ExtractByLocation']['OUTPUT']
        }
        outputs['ListUniqueDistritos'] = processing.run('qgis:listuniquevalues', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': -1,
                'name': 'inicio_objeto',
                'precision': 0,
                'type': 16
            },{
                'expression': f"\'{parameters['Datadepublicacao']}\'",
                'length': -1,
                'name': 'data_publicacao',
                'precision': 0,
                'type': 14
            },{
                'expression': '\"dicofre\"',
                'length': 255,
                'name': 'dicofre',
                'precision': 0,
                'type': 10
            },{
                'expression': '\"Freguesia\"',
                'length': 255,
                'name': 'nome',
                'precision': 0,
                'type': 10
            }],
            'INPUT': outputs['ExtractByLocation']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Extract by expression
        alg_params = {
            'EXPRESSION': f"array_contains( string_to_array('{outputs['ListUniqueConcelhos']['UNIQUE_VALUES']}',';'), \"Concelho\")",
            'INPUT': parameters['CAOP'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByExpression_concelhos'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Extract by expression
        alg_params = {
            'EXPRESSION': f"array_contains( string_to_array('{outputs['ListUniqueDistritos']['UNIQUE_VALUES']}',';'), \"Distrito\")",
            'INPUT': parameters['CAOP'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ExtractByExpression_distritos'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Export to PostgreSQL (available connections)
        alg_params = {
            'ADDFIELDS': False,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters['LigaoBasedeDadosRECART'],
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 8,
            'INDEX': False,
            'INPUT': outputs['RefactorFields']['OUTPUT'],
            'LAUNDER': False,
            'OPTIONS': '',
            'OVERWRITE': False,
            'PK': '',
            'PRECISION': False,
            'PRIMARY_KEY': 'identificador',
            'PROMOTETOMULTI': True,
            'SCHEMA': 'public',
            'SEGMENTIZE': '',
            'SHAPE_ENCODING': '',
            'SIMPLIFY': '',
            'SKIPFAILURES': False,
            'SPAT': None,
            'S_SRS': None,
            'TABLE': 'freguesia',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': 0,
                'name': 'inicio_objeto',
                'precision': 0,
                'type': 16
            },{
                'expression': ' left(\"Dicofre\",2)',
                'length': 255,
                'name': 'di',
                'precision': 0,
                'type': 10
            },{
                'expression': '\"Distrito\"',
                'length': 255,
                'name': 'nome',
                'precision': 0,
                'type': 10
            },{
                'expression': f"\'{parameters['Datadepublicacao']}\'",
                'length': 0,
                'name': 'data_publicacao',
                'precision': 0,
                'type': 14
            }],
            'INPUT': outputs['ExtractByExpression_distritos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields_distritos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Dissolve
        alg_params = {
            'FIELD': ['di'],
            'INPUT': outputs['RefactorFields_distritos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolve_distritos'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Refactor fields
        alg_params = {
            'FIELDS_MAPPING': [{
                'expression': 'now()',
                'length': 0,
                'name': 'inicio_objeto',
                'precision': 0,
                'type': 16
            },{
                'expression': ' left(\"Dicofre\",4)',
                'length': 255,
                'name': 'dico',
                'precision': 0,
                'type': 10
            },{
                'expression': '\"Concelho\"',
                'length': 255,
                'name': 'nome',
                'precision': 0,
                'type': 10
            },{
                'expression': f"\'{parameters['Datadepublicacao']}\'",
                'length': 0,
                'name': 'data_publicacao',
                'precision': 0,
                'type': 14
            }],
            'INPUT': outputs['ExtractByExpression_concelhos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RefactorFields_concelhos'] = processing.run('native:refactorfields', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Dissolve
        alg_params = {
            'FIELD': ['dico'],
            'INPUT': outputs['RefactorFields_concelhos']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Dissolve_concelhos'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Export to PostgreSQL (available connections)
        alg_params = {
            'ADDFIELDS': False,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters['LigaoBasedeDadosRECART'],
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 8,
            'INDEX': False,
            'INPUT': outputs['Dissolve_distritos']['OUTPUT'],
            'LAUNDER': False,
            'OPTIONS': '',
            'OVERWRITE': False,
            'PK': '',
            'PRECISION': False,
            'PRIMARY_KEY': 'identificador',
            'PROMOTETOMULTI': True,
            'SCHEMA': 'public',
            'SEGMENTIZE': '',
            'SHAPE_ENCODING': '',
            'SIMPLIFY': '',
            'SKIPFAILURES': False,
            'SPAT': None,
            'S_SRS': None,
            'TABLE': 'distrito',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Export to PostgreSQL (available connections)
        alg_params = {
            'ADDFIELDS': False,
            'APPEND': True,
            'A_SRS': None,
            'CLIP': False,
            'DATABASE': parameters['LigaoBasedeDadosRECART'],
            'DIM': 0,
            'GEOCOLUMN': 'geometria',
            'GT': '',
            'GTYPE': 8,
            'INDEX': False,
            'INPUT': outputs['Dissolve_concelhos']['OUTPUT'],
            'LAUNDER': False,
            'OPTIONS': '',
            'OVERWRITE': False,
            'PK': '',
            'PRECISION': False,
            'PRIMARY_KEY': 'identificador',
            'PROMOTETOMULTI': True,
            'SCHEMA': 'public',
            'SEGMENTIZE': '',
            'SHAPE_ENCODING': '',
            'SIMPLIFY': '',
            'SKIPFAILURES': False,
            'SPAT': None,
            'S_SRS': None,
            'TABLE': 'concelho',
            'T_SRS': None,
            'WHERE': ''
        }
        outputs['ExportToPostgresqlAvailableConnections'] = processing.run('gdal:importvectorintopostgisdatabaseavailableconnections', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'Exportar Unidades Administrativas de Ficheiro CAOP'

    def displayName(self):
        return '01_03 Exportar Unidades Administrativas de Ficheiro CAOP'

    def group(self):
        return '01 - Unidades Administrativas'

    def groupId(self):
        return '01UnidadesAdministrativas'

    def createInstance(self):
        return ExportarUnidadesAdministrativas()
