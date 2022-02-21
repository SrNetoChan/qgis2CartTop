from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProperty,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterProviderConnection)
import processing, os


class homogenizar_z_aguas_lenticas(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LIGACAO_RECART = 'LIGACAO_RECART'
    SUBSTITUIR_BACKUP = 'SUBSTITUIR_BACKUP'

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
            QgsProcessingParameterBoolean(
                self.SUBSTITUIR_BACKUP,
                'Substituir backup existente'
            )
        )


    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        ligacao_recart = parameters[self.LIGACAO_RECART]
        substituir_backup = parameters[self.SUBSTITUIR_BACKUP]

        script_path = os.path.dirname(os.path.realpath(__file__))
        sql_path = os.path.join(script_path, 'homogenizar_z_aguas_lenticas.sql')

        with open(sql_path) as f:
            base_sql = f.read()

        sql_command = base_sql

        # Delete backup table
        if substituir_backup:
            # PostgreSQL execute SQL
            alg_params = {
                'DATABASE': ligacao_recart,
                'SQL': 'DROP TABLE IF EXISTS backup.agua_lentica_bk;'
            }
            outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)


        # PostgreSQL execute SQL
        alg_params = {
            'DATABASE': ligacao_recart,
            'SQL': sql_command
        }
        outputs['PostgresqlExecuteSql'] = processing.run('qgis:postgisexecutesql', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        return results

    def name(self):
        return 'homogenizar_z_aguas_lenticas'

    def displayName(self):
        return 'Homogenizar_z_aguas_lenticas'

    def group(self):
        return '04 - Hidrografia'

    def groupId(self):
        return '04hidrografia'

    def createInstance(self):
        return homogenizar_z_aguas_lenticas()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr(
            """<p>Garante um valor Z constante em todos os vértices da geometria da tabela agua_lentica.
            Em cada elemento, o valor de Z usado representa a moda dos valores Z de todos os seus vertices originais.<\p>
            <p><b>ATENÇÃO: Altera directamente a tabela agua_lentica<\b><\p>
            <p><b>CUIDADO!:</b> Se a opção Substituir backup existente for usada, não existe forma de recuperar os dados originais!<\p>"""
                       )git s
