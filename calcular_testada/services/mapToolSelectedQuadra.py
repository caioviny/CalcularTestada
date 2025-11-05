"""
MapToolSelectQuadra - Versão Simplificada
Seleção de quadras com clique simples (sem polígono, sem CTRL)
"""
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsFeatureRequest
from qgis.gui import QgsMapTool, QgsMapToolIdentify


class MapToolSelectQuadra(QgsMapTool):
    """Ferramenta de seleção de quadras com clique simples"""

    def __init__(self, canvas, layer, callback, parent):
        super().__init__(canvas)
        self.canvas = canvas
        self.layer = layer
        self.callback_atualizar = callback
        self.parent_plugin = parent
        self.setCursor(Qt.CrossCursor)
        self._mostrar_instrucoes_iniciais()

    def _mostrar_instrucoes_iniciais(self):
        """Mostra instruções na barra de mensagens"""
        self.parent_plugin.iface.messageBar().clearWidgets()
        self.parent_plugin.iface.messageBar().pushMessage(
            "Modo de Seleção",
            "🖱️ Clique na quadra para selecionar | ⏎ ENTER para confirmar | ESC para cancelar",
            level=0,
            duration=0
        )

    def _atualizar_barra_status(self):
        """Atualiza a barra de status com o número de quadras selecionadas"""
        num = self.layer.selectedFeatureCount()
        self.parent_plugin.iface.messageBar().clearWidgets()
        
        if num > 0:
            self.parent_plugin.iface.messageBar().pushMessage(
                "Seleção Ativa",
                f"✅ {num} quadra(s) selecionada(s) | 🖱️ Clique para alterar | ⏎ ENTER para confirmar",
                level=3,  # Success (verde)
                duration=0
            )
        else:
            self.parent_plugin.iface.messageBar().pushMessage(
                "Modo de Seleção",
                "🖱️ Clique na quadra para selecionar | ⏎ ENTER para confirmar | ESC para cancelar",
                level=0,
                duration=0
            )

    def canvasPressEvent(self, event):
        """Evento de clique no canvas"""
        if event.button() == Qt.LeftButton:
            self.selecionar_quadra(event)

    def selecionar_quadra(self, event):
        """Seleciona ou deseleciona a quadra clicada"""
        # Identifica a feição no ponto clicado
        results = QgsMapToolIdentify(self.canvas).identify(
            event.x(), 
            event.y(), 
            [self.layer], 
            QgsMapToolIdentify.TopDownStopAtFirst
        )
        
        if results:
            feature = results[0].mFeature
            feature_id = feature.id()
            
            # Verifica se a feição já está selecionada
            if feature_id in self.layer.selectedFeatureIds():
                # Se já estava selecionada, deseleciona
                self.layer.deselect(feature_id)
                self._mostrar_notificacao_remocao()
            else:
                # Se não estava selecionada, limpa seleção anterior e seleciona nova
                self.layer.removeSelection()
                self.layer.select(feature_id)
                self._mostrar_notificacao_selecao()
            
            # Atualiza a interface
            self._atualizar_barra_status()
            if self.callback_atualizar:
                self.callback_atualizar()
        else:
            # Clicou fora de qualquer quadra
            self._mostrar_notificacao_erro()

    def _mostrar_notificacao_selecao(self):
        """Mostra notificação de quadra selecionada"""
        self.parent_plugin.iface.messageBar().pushMessage(
            "Quadra Selecionada",
            "✅ Quadra selecionada com sucesso. Pressione ENTER para confirmar.",
            level=3,  # Success
            duration=2
        )

    def _mostrar_notificacao_remocao(self):
        """Mostra notificação de quadra removida"""
        self.parent_plugin.iface.messageBar().pushMessage(
            "Seleção Removida",
            "❌ Quadra deselecionada. Clique em outra quadra para selecionar.",
            level=1,  # Warning
            duration=2
        )

    def _mostrar_notificacao_erro(self):
        """Mostra notificação de erro (clique fora)"""
        self.parent_plugin.iface.messageBar().pushMessage(
            "Nenhuma Quadra",
            "⚠️ Nenhuma quadra encontrada neste ponto. Clique sobre uma quadra.",
            level=1,  # Warning
            duration=2
        )

    def keyPressEvent(self, event):
        """Evento de tecla pressionada"""
        if event.key() == Qt.Key_Escape:
            # ESC: Cancela seleção e fecha ferramenta
            if self.layer:
                self.layer.removeSelection()
            
            self.parent_plugin.iface.messageBar().clearWidgets()
            self.parent_plugin.iface.messageBar().pushMessage(
                "Cancelado",
                "❌ Seleção cancelada",
                level=1,
                duration=2
            )
            
            # Fecha o modo de seleção
            self.canvas.unsetMapTool(self)
            
            # Atualiza o dialog se houver callback
            if self.callback_atualizar:
                self.callback_atualizar()
                
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # ENTER: Confirma seleção e reabre diálogo
            num_selecionadas = self.layer.selectedFeatureCount()
            
            if num_selecionadas > 0:
                self.parent_plugin.iface.messageBar().clearWidgets()
                self.parent_plugin.iface.messageBar().pushMessage(
                    "Confirmado",
                    f"✅ {num_selecionadas} quadra(s) confirmada(s)",
                    level=3,
                    duration=3
                )
                
                # Desativa a ferramenta e reabre o diálogo
                self.canvas.unsetMapTool(self)
                self.parent_plugin.confirmar_selecao_e_reabrir_dialogo()
            else:
                self.parent_plugin.iface.messageBar().pushMessage(
                    "Aviso",
                    "⚠️ Selecione pelo menos uma quadra antes de confirmar",
                    level=1,
                    duration=2
                )
        else:
            event.ignore()

    def deactivate(self):
        """Desativa a ferramenta"""
        # Limpa a barra de mensagens
        if self.parent_plugin and self.parent_plugin.iface:
            self.parent_plugin.iface.messageBar().clearWidgets()
        
        super().deactivate()

    def activate(self):
        """Ativa a ferramenta"""
        super().activate()
        self._mostrar_instrucoes_iniciais()