from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingMultiStepFeedback,
                       QgsProperty,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterProviderConnection)
import processing, os


class Consolidar_quebra_de_linha(QgsProcessingAlgorithm):

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
        sql_path = os.path.join(script_path, 'consolidar_linha_de_quebra.sql')

        with open(sql_path) as f:
            base_sql = f.read()

        sql_command = base_sql

        # Delete backup table
        if substituir_backup:
            # PostgreSQL execute SQL
            alg_params = {
                'DATABASE': ligacao_recart,
                'SQL': 'DROP TABLE IF EXISTS backup.linha_de_quebra_bk;'
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
        return 'consolidar_quebra_de_linha'

    def displayName(self):
        return 'Consolidar linhas de quebra'

    def group(self):
        return '01 - Altimetria'

    def groupId(self):
        return '01altimetria'

    def createInstance(self):
        return Consolidar_quebra_de_linha()

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        return self.tr(
            "Agrega todas as linestrings adjacentes (em Z, Y e Z) com atributos comuns\n\n"
            "<b>ATENÇÃO: Altera directamente a tabela linha_de_quebra<\b>"
                       )
