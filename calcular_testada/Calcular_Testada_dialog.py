"""
Dialog do plugin Calcular Testada
"""

import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsProviderRegistry

# Carrega o arquivo UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'Calcular_Testada_dialog_base.ui'))


class CalcularTestadaDialog(QDialog, FORM_CLASS):
    """Dialog para configuração do cálculo de testada"""
    
    def __init__(self, parent=None):
        """Construtor"""
        super(CalcularTestadaDialog, self).__init__(parent)
        self.setupUi(self)
        
        # Carregar conexões PostgreSQL
        self.carregar_conexoes()
        
        # Configurar combo box de pontos cardeais
        self.comboPontoCardeal.addItems([
            'NORTE',
            'NORDESTE',
            'LESTE',
            'SUDESTE',
            'SUL',
            'SUDOESTE',
            'OESTE',
            'NOROESTE'
        ])
        
        # Definir valor padrão como SUDESTE (índice 3)
        self.comboPontoCardeal.setCurrentIndex(3)
    
    def carregar_conexoes(self):
        """Carrega as conexões PostgreSQL disponíveis"""
        self.comboConexao.clear()
        
        try:
            # Obter metadata do provider PostgreSQL
            md = QgsProviderRegistry.instance().providerMetadata('postgres')
            
            if md:
                # Listar todas as conexões
                connections = md.connections()
                
                # Adicionar ao combo box
                for conn_name in connections.keys():
                    self.comboConexao.addItem(conn_name)
                
                if self.comboConexao.count() == 0:
                    self.comboConexao.addItem("Nenhuma conexão disponível")
        except Exception as e:
            self.comboConexao.addItem(f"Erro ao carregar conexões: {str(e)}")