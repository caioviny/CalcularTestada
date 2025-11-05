"""
Plugin Calcular Testada - Versão Moderna Integrada
Calcula as linhas de testada dos lotes em relação às quadras
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolBar
from qgis.core import (
    QgsProject, QgsProcessing, QgsProcessingAlgorithm,
    QgsProcessingMultiStepFeedback, QgsCoordinateReferenceSystem,
    QgsExpression, QgsProcessingFeatureSourceDefinition,
    QgsFeatureRequest, QgsGeometry, QgsFeature, QgsField,
    QgsFields, QgsWkbTypes, QgsVectorLayer, QgsPointXY
)
import processing
import os.path

# Importa os novos módulos
from .Calcular_Testada_dialog import CalcularTestadaDialog
from .services.mapToolSelectedQuadra import MapToolSelectQuadra


class CalcularTestada:
    """Plugin principal"""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.toolbar = None
        self.map_tool = None  # Armazena a ferramenta de seleção

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CalcularTestada_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        
        self.actions = []
        self.menu = self.tr(u'&Calcular Testada')
        self.first_start = None
        self.dlg = None

    def tr(self, message):
        return QCoreApplication.translate('CalcularTestada', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.toolbar.addAction(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        
        self.actions.append(action)
        return action

    def initGui(self):
        """Inicializa a interface gráfica"""
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        
        # Procurar pelo toolbar UMCGEO existente
        self.toolbar = None
        for toolbar in self.iface.mainWindow().findChildren(QToolBar):
            if toolbar.objectName() == 'UMCGEO' or toolbar.windowTitle() == 'UMCGEO':
                self.toolbar = toolbar
                break
        
        # Se não encontrar, criar um novo toolbar
        if self.toolbar is None:
            self.toolbar = self.iface.addToolBar('UMCGEO')
            self.toolbar.setObjectName('UMCGEO')

        self.add_action(
            icon_path,
            text=self.tr(u'Calcular Testada'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )
        
        self.first_start = True

    def unload(self):
        """Remove o plugin e limpa recursos"""
        for action in self.actions:
            self.iface.removePluginVectorMenu(self.menu, action)
            if self.toolbar:
                self.toolbar.removeAction(action)
        
        # Desativa a ferramenta de seleção se estiver ativa
        if self.map_tool:
            self.iface.mapCanvas().unsetMapTool(self.map_tool)
            self.map_tool = None

    def run(self):
        """Executa o plugin"""
        if self.first_start:
            self.first_start = False
            self.dlg = CalcularTestadaDialog()
            
            # Conecta os botões
            self.dlg.btnExecutar.clicked.connect(self.executar_processamento)
            self.dlg.btnSelecionar.clicked.connect(self.ativar_selecao_quadra)
        
        # Atualiza o status da seleção ao abrir o diálogo
        self.atualizar_status_selecao()
        
        self.dlg.show()
        result = self.dlg.exec_()

    def ativar_selecao_quadra(self):
        """Ativa a ferramenta de seleção de quadras no mapa"""
        # Verifica se a camada Quadra existe
        quadra_layers = QgsProject.instance().mapLayersByName('Quadra')
        
        if not quadra_layers:
            QMessageBox.warning(
                self.dlg,
                "Aviso",
                "Camada 'Quadra' não encontrada no projeto!\n\n"
                "Certifique-se de que a camada 'Quadra' está carregada."
            )
            return
        
        quadra_layer = quadra_layers[0]
        
        # Fecha o diálogo temporariamente
        self.dlg.hide()
        
        # Cria e ativa a ferramenta de seleção
        self.map_tool = MapToolSelectQuadra(
            self.iface.mapCanvas(),
            quadra_layer,
            self.atualizar_status_selecao,
            self
        )
        
        self.iface.mapCanvas().setMapTool(self.map_tool)
        
        # Mensagem informativa
        self.iface.messageBar().pushMessage(
            "Modo de Seleção Ativado",
            "🎯 Clique na quadra desejada no mapa. Pressione ENTER para confirmar ou ESC para cancelar.",
            level=0,
            duration=5
        )

    def confirmar_selecao_e_reabrir_dialogo(self):
        """Confirma a seleção e reabre o diálogo"""
        # Desativa a ferramenta
        if self.map_tool:
            self.iface.mapCanvas().unsetMapTool(self.map_tool)
        
        # Atualiza o status
        self.atualizar_status_selecao()
        
        # Reabre o diálogo
        self.dlg.show()

    def atualizar_status_selecao(self):
        """Atualiza o status da seleção no diálogo"""
        if not self.dlg:
            return
        
        quadra_layers = QgsProject.instance().mapLayersByName('Quadra')
        
        if quadra_layers:
            num_selecionadas = quadra_layers[0].selectedFeatureCount()
            self.dlg.atualizar_status_selecao(num_selecionadas)
        else:
            self.dlg.atualizar_status_selecao(0)

    def executar_processamento(self):
        """Executa o processamento principal"""
        try:
            # Validações
            conexao = self.dlg.comboConexao.currentText()

            if not conexao or conexao == "Nenhuma conexão disponível" or "Erro" in conexao:
                QMessageBox.warning(
                    self.dlg,
                    "Aviso",
                    "Selecione uma conexão válida com o banco de dados!"
                )
                return

            # Verificar se há quadra selecionada
            quadra_layer = QgsProject.instance().mapLayersByName('Quadra')
            if not quadra_layer or quadra_layer[0].selectedFeatureCount() == 0:
                QMessageBox.warning(
                    self.dlg,
                    "Aviso",
                    "Selecione uma quadra antes de executar!\n\n"
                    "Use o botão 'Selecionar Quadra no Mapa'."
                )
                return

            # Obter parâmetros
            ponto_cardeal = self.dlg.comboPontoCardeal.currentIndex()

            # Confirma execução
            resposta = QMessageBox.question(
                self.dlg,
                "Confirmar Processamento",
                f"Deseja processar {quadra_layer[0].selectedFeatureCount()} quadra(s) selecionada(s)?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if resposta == QMessageBox.Yes:
                # Executa o processamento
                self.processar_testada(conexao, ponto_cardeal)

        except Exception as e:
            QMessageBox.critical(
                self.dlg,
                "Erro",
                f"Erro ao executar processamento:\n{str(e)}"
            )

    def processar_testada(self, conexao, ponto_cardeal):
        """Executa o algoritmo de cálculo de testada"""

        feedback = QgsProcessingMultiStepFeedback(17, None)
        results = {}
        outputs = {}

        try:
            # Step 1: Extrair feições selecionadas quadra
            feedback.pushInfo("Extraindo quadra selecionada...")
            alg_params = {
                'INPUT': 'Quadra',
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ExtrairQuadra'] = processing.run(
                'native:saveselectedfeatures',
                alg_params,
                feedback=feedback
            )
            feedback.setCurrentStep(1)
            if feedback.isCanceled():
                return {}

            # Step 2: Extrair lotes por localização
            feedback.pushInfo("Extraindo lotes da quadra...")
            alg_params = {
                'INPUT': 'Lote',
                'INTERSECT': outputs['ExtrairQuadra']['OUTPUT'],
                'PREDICATE': [0, 5],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['ExtrairLotes'] = processing.run(
                'native:extractbylocation',
                alg_params,
                feedback=feedback
            )
            feedback.setCurrentStep(2)

            # Step 3: Centroides
            feedback.pushInfo("Calculando centroides...")
            alg_params = {
                'ALL_PARTS': False,
                'INPUT': outputs['ExtrairQuadra']['OUTPUT'],
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['Centroides'] = processing.run(
                'native:centroids',
                alg_params,
                feedback=feedback
            )
            feedback.setCurrentStep(3)

            # Step 4-11: Processamento geométrico
            feedback.pushInfo("Simplificando geometrias...")
            outputs = self.processar_geometrias(outputs, feedback)
            if feedback.isCanceled():
                return {}

            # Step 12: Editar campos do lote
            feedback.pushInfo("Editando campos do lote...")
            outputs['EditarCamposLote'] = self.editar_campos_lote(outputs, feedback)
            feedback.setCurrentStep(12)

            # Step 13: Rotacionar lote
            feedback.pushInfo("Rotacionando lotes...")
            angulo_lote = self.calcular_angulo_rotacao(ponto_cardeal, inverter=True)

            # Obter a geometria do centroide
            centroide_layer = outputs['Centroides']['OUTPUT']
            features = centroide_layer.getFeatures()
            centroide_geom = next(features).geometry()

            alg_params = {
                'INPUT': outputs['EditarCamposLote']['OUTPUT'],
                'ANGLE': angulo_lote,
                'ANCHOR': centroide_geom,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['RotacionarLote'] = processing.run(
                'native:rotatefeatures',
                alg_params,
                feedback=feedback
            )
            feedback.setCurrentStep(13)

            # Step 14: Linhas de testada (AGORA INTEGRADO)
            feedback.pushInfo("Gerando linhas de testada...")
            outputs['LinhasTestada'] = self.gerar_linhas_testada_integrado(
                outputs['RotacionarLote']['OUTPUT'],
                tolerance=0.01,
                feedback=feedback
            )
            feedback.setCurrentStep(14)

            # Step 15: Rotacionar linhas
            feedback.pushInfo("Rotacionando linhas de testada...")
            angulo_linha = self.calcular_angulo_rotacao(ponto_cardeal, inverter=False)

            alg_params = {
                'INPUT': outputs['LinhasTestada']['OUTPUT'],
                'ANGLE': angulo_linha,
                'ANCHOR': centroide_geom,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs['RotacionarLinhas'] = processing.run(
                'native:rotatefeatures',
                alg_params,
                feedback=feedback
            )
            feedback.setCurrentStep(15)

            # Step 16: Editar campos das linhas
            feedback.pushInfo("Editando campos das linhas...")
            outputs['EditarCamposLinhas'] = self.editar_campos_linhas(outputs, feedback)
            feedback.setCurrentStep(16)

            # Step 17: Exportar para PostgreSQL
            feedback.pushInfo("Exportando para PostgreSQL...")
            alg_params = {
                'ADDFIELDS': False,
                'APPEND': True,
                'A_SRS': QgsCoordinateReferenceSystem('EPSG:31984'),
                'CLIP': False,
                'DATABASE': conexao,
                'DIM': 0,
                'GEOCOLUMN': 'geom',
                'GT': None,
                'GTYPE': 9,
                'INDEX': False,
                'INPUT': outputs['EditarCamposLinhas']['OUTPUT'],
                'LAUNDER': False,
                'MAKEVALID': False,
                'OPTIONS': None,
                'OVERWRITE': False,
                'PK': 'id',
                'PRECISION': True,
                'PRIMARY_KEY': None,
                'PROMOTETOMULTI': False,
                'SCHEMA': 'comercial_umc',
                'SEGMENTIZE': None,
                'SHAPE_ENCODING': None,
                'SIMPLIFY': None,
                'SKIPFAILURES': False,
                'SPAT': None,
                'S_SRS': None,
                'TABLE': 'calcular_testada',
                'T_SRS': None,
                'WHERE': None
            }
            processing.run(
                'gdal:importvectorintopostgisdatabaseavailableconnections',
                alg_params,
                feedback=feedback
            )
            QMessageBox.information(
                self.dlg,
                "Sucesso",
                "Processamento concluído com sucesso!"
            )

        except Exception as e:
            QMessageBox.critical(
                self.dlg,
                "Erro",
                f"Erro durante o processamento:\n{str(e)}"
            )
    # ... (Resto dos métodos auxiliares como processar_geometrias, 
    # editar_campos_lote, etc - mantidos do código original)
    def conectar_feicoes_integrado(self, input_layer, tolerance=0.01, feedback=None):
        """
        Conecta feições adjacentes garantindo perfeita conectividade topológica
        (implementação integrada do lftools:connectfeatures)
        """
        if feedback is None:
            feedback = QgsProcessingMultiStepFeedback(1, None)

        feedback.pushInfo("Verificando e corrigindo conectividade...")

        # Obter feições da camada de entrada
        feicoes = []
        for feat in input_layer.getFeatures():
            if feat.geometry().isMultipart():
                feedback.reportError(f'Feição de id {feat.id()} é multiparte!')
                return {'OUTPUT': input_layer}
            feicoes.append(feat)

        # Verificar se é geográfico para ajustar tolerância
        tol = tolerance
        if input_layer.crs().isGeographic():
            tol /= 111000  # transforma de graus para metros

        # Verificar e corrigir conectividade
        tam = len(feicoes)
        for i in range(tam):
            for j in range(tam):
                if i != j:
                    feat_a = feicoes[i]
                    geom_a = feat_a.geometry()
                    feat_b = feicoes[j]
                    geom_b = feat_b.geometry()
                    
                    if geom_a.intersects(geom_b):
                        # Verificar se algum ponto de A que intercepta o segmento de B não tem vértice correspondente
                        coord_a = geom_a.asPolygon()[0]
                        coord_b = geom_b.asPolygon()[0]
                        new_coord_b = []
                        
                        for k in range(len(coord_b) - 1):
                            p1 = coord_b[k]
                            p2 = coord_b[k + 1]
                            segm = QgsGeometry.fromPolylineXY([p1, p2])
                            sentinela = False
                            
                            for pnt_a in coord_a:
                                pnt = QgsGeometry.fromPointXY(pnt_a).buffer(tol, 1)
                                if pnt_a not in coord_b and pnt.intersects(segm):
                                    new_coord_b += [p1, pnt_a]
                                    sentinela = True
                                    break
                            
                            if not sentinela:
                                new_coord_b += [p1]
                        
                        new_coord_b += [coord_b[-1]]
                        feat_b.setGeometry(QgsGeometry.fromPolygonXY([new_coord_b]))
                        feicoes[j] = feat_b

        # Criar camada de saída
        Fields = input_layer.fields()
        output_layer = QgsVectorLayer(
            f"Polygon?crs={input_layer.crs().authid()}",
            "conectadas_temp",
            "memory"
        )
        output_layer.startEditing()
        output_layer.dataProvider().addAttributes(Fields)
        output_layer.updateFields()

        # Adicionar feições corrigidas
        for feat in feicoes:
            output_layer.addFeature(feat)

        output_layer.commitChanges()
        
        feedback.pushInfo('Conectividade corrigida com sucesso!')
        
        return {'OUTPUT': output_layer}
    
    def gerar_linhas_testada_integrado(self, input_layer, tolerance=0.01, feedback=None):
        """
        Gera linhas de testada dos lotes (implementação integrada do lftools:frontlotline)
        """
        if feedback is None:
            feedback = QgsProcessingMultiStepFeedback(1, None)

        feedback.pushInfo("Orientando polígonos (sentido horário)...")
        
        # Obter feições da camada de entrada
        feicoes = []
        for feat in input_layer.getFeatures():
            if feat.geometry().isMultipart():
                feedback.reportError(f'Feição de id {feat.id()} é multiparte! Convertendo...')
                # Converter multipart para singlepart
                geom = feat.geometry()
                if geom.isMultipart():
                    parts = geom.asMultiPolygon()
                    for part in parts:
                        new_feat = QgsFeature(feat)
                        new_feat.setGeometry(QgsGeometry.fromPolygonXY(part))
                        feicoes.append(new_feat)
                else:
                    feicoes.append(feat)
            else:
                feicoes.append(feat)

        # Pegar geometrias para mesclar
        feedback.pushInfo('Definindo conjunto de parcelas (quadras)...')
        geometrias = [feat.geometry() for feat in feicoes]

        # Separar por quadras (Mesclar lotes)
        quadras = []
        while len(geometrias) > 1:
            tam = len(geometrias)
            for i in range(0, tam - 1):
                mergeou = False
                geom_A = geometrias[i]
                for j in range(i + 1, tam):
                    geom_B = geometrias[j]
                    if geom_A.intersects(geom_B):
                        mergeou = True
                        new_geom = geom_A.combine(geom_B)
                        break
                if mergeou:
                    del geometrias[i], geometrias[j - 1]
                    geometrias = [new_geom] + geometrias
                    break
                else:
                    quadras.append(geom_A)
                    del geometrias[i]
                    break
        if geometrias:
            quadras += geometrias

        # Orientar polígonos
        feedback.pushInfo('Orientando polígonos (sentido horário)...')
        for k in range(len(feicoes)):
            feat = feicoes[k]
            coords = feat.geometry().asPolygon()[0]
            coords = coords[:-1]
            coords = self.orientar_poligono(coords, primeiro=1, sentido=0)  # mais ao norte e sentido horário
            new_geom = QgsGeometry.fromPolygonXY([coords])
            feat.setGeometry(new_geom)
            feicoes[k] = feat

        # Separar feições por quadra
        qd_dic = {}
        testada_dic = {}
        for qd in quadras:
            qd_dic[qd] = []
            testada_dic[qd] = []

        for feat in feicoes:
            geom = feat.geometry()
            for qd in quadras:
                if geom.intersects(qd):
                    qd_dic[qd].append(feat)

        # Calcular testadas por quadras
        feedback.pushInfo('Calculando linhas de testada...')
        
        for qd in quadras:
            linhas = []
            atributos = []
            for feat in qd_dic[qd]:
                geom = feat.geometry()
                att = feat.attributes()
                atributos.append(att)
                linhas.append(geom.asPolygon()[0])

            TAM = len(linhas)

            # Calculando a diferença para cada linha
            for i in range(TAM):
                geom1 = QgsGeometry.fromPolylineXY(linhas[i])
                for j in range(TAM):
                    if i != j:
                        geom2 = QgsGeometry.fromPolylineXY(linhas[j])
                        if geom1.intersects(geom2):
                            differ = geom1.difference(geom2)
                            geom1 = differ
                
                if geom1.length() > 0:
                    if geom1.isMultipart():
                        partes = geom1.asMultiPolyline()
                        partes_novas = []
                        
                        while len(partes) > 1:
                            tam = len(partes)
                            for r in range(0, tam - 1):
                                mergeou = False
                                parte_A = partes[r]
                                for s in range(r + 1, tam):
                                    parte_B = partes[s]
                                    if (parte_A[0] == parte_B[0] or parte_A[0] == parte_B[-1] or 
                                        parte_A[-1] == parte_B[0] or parte_A[-1] == parte_B[-1]):
                                        mergeou = True
                                        if parte_A[0] == parte_B[0]:
                                            parte_nova = parte_B[1:][::-1] + parte_A
                                        elif parte_A[0] == parte_B[-1]:
                                            parte_nova = parte_B + parte_A[1:]
                                        elif parte_A[-1] == parte_B[0]:
                                            parte_nova = parte_A + parte_B[1:]
                                        elif parte_A[-1] == parte_B[-1]:
                                            parte_nova = parte_A + parte_B[::-1][1:]
                                        break
                                if mergeou:
                                    del partes[r], partes[s - 1]
                                    partes = [parte_nova] + partes
                                    break
                                else:
                                    partes_novas.append(parte_A)
                                    del partes[r]
                                    break
                        
                        if partes:
                            partes_novas += partes
                        
                        for parte in partes_novas:
                            geom = QgsGeometry.fromPolylineXY(parte)
                            feature = QgsFeature()
                            feature.setGeometry(geom)
                            feature.setAttributes(atributos[i])
                            testada_dic[qd].append(feature)
                    else:
                        feature = QgsFeature()
                        feature.setGeometry(geom1)
                        feature.setAttributes(atributos[i])
                        testada_dic[qd].append(feature)

        # Criar camada de saída
        feedback.pushInfo('Sequenciando e salvando linhas de testada...')
        
        Fields = input_layer.fields()
        Fields.append(QgsField('sequencia', QVariant.Int))
        Fields.append(QgsField('comprimento', QVariant.Double))
        Fields.append(QgsField('valor_testada', QVariant.Double))

        output_layer = QgsVectorLayer(
            f"LineString?crs={input_layer.crs().authid()}",
            "testadas_temp",
            "memory"
        )
        output_layer.startEditing()
        output_layer.dataProvider().addAttributes(Fields)
        output_layer.updateFields()

        for qd in testada_dic:
            testadas = testada_dic[qd]
            if not testadas:
                continue

            # Pegar ponto mais ao norte da Quadra
            coords = qd.asPolygon()[0]
            pnt = self.orientar_poligono(coords[:-1], primeiro=1, sentido=2)[0]
            pnt = QgsGeometry.fromPointXY(pnt)
            
            if len(testadas) == 1:
                testadas_seq = [testadas[0]]
            else:
                # Verificar qual testada intercepta e não é último ponto
                testadas_seq = []
                for feat in testadas:
                    lin = feat.geometry()
                    ultimo_pnt = QgsGeometry.fromPointXY(lin.asPolyline()[-1])
                    if pnt.intersects(lin) and not pnt.intersects(ultimo_pnt):
                        testadas_seq = [feat]
                        break
                
                # Criar rede para cada quadra
                for k in range(1, len(testadas)):
                    if k > len(testadas_seq):
                        break
                    ultima_testada = testadas_seq[k - 1].geometry()
                    ultimo_pnt = QgsGeometry.fromPointXY(ultima_testada.asPolyline()[-1])
                    for feat in testadas:
                        if feat in testadas_seq:
                            continue
                        primeiro_pnt = QgsGeometry.fromPointXY(feat.geometry().asPolyline()[0])
                        if ultimo_pnt.intersects(primeiro_pnt):
                            testadas_seq.append(feat)
                            break

            # Preencher atributos: ordem, comprimento e comprimento acumulado
            soma = 0
            for k, feat in enumerate(testadas_seq):
                comprimento = feat.geometry().length()
                soma += comprimento
                feature = QgsFeature(Fields)
                feature.setGeometry(feat.geometry())
                feature.setAttributes(feat.attributes() + [k + 1, comprimento, soma])
                output_layer.addFeature(feature)

        output_layer.commitChanges()
        
        feedback.pushInfo('Linhas de testada geradas com sucesso!')
        
        return {'OUTPUT': output_layer}
    
    def orientar_poligono(self, coords, primeiro=1, sentido=0):
        """
        Orienta o polígono baseado no ponto cardeal e sentido
        primeiro: 1=Norte, 2=Sul, 3=Leste, 4=Oeste
        sentido: 0=horário, 1=anti-horário, 2=apenas retorna primeiro ponto
        """
        if not coords:
            return coords

        # Encontrar ponto inicial baseado no parâmetro 'primeiro'
        if primeiro == 1:  # Mais ao Norte (maior Y)
            idx = max(range(len(coords)), key=lambda i: coords[i].y())
        elif primeiro == 2:  # Mais ao Sul (menor Y)
            idx = min(range(len(coords)), key=lambda i: coords[i].y())
        elif primeiro == 3:  # Mais ao Leste (maior X)
            idx = max(range(len(coords)), key=lambda i: coords[i].x())
        elif primeiro == 4:  # Mais ao Oeste (menor X)
            idx = min(range(len(coords)), key=lambda i: coords[i].x())
        else:
            idx = 0

        if sentido == 2:  # Apenas retornar primeiro ponto
            return [coords[idx]]

        # Reorganizar coordenadas
        coords_reorg = coords[idx:] + coords[:idx]

        # Verificar sentido e inverter se necessário
        area = self.calcular_area_sinalizada(coords_reorg)
        
        if sentido == 0:  # Horário (área negativa)
            if area > 0:
                coords_reorg = coords_reorg[:1] + coords_reorg[1:][::-1]
        else:  # Anti-horário (área positiva)
            if area < 0:
                coords_reorg = coords_reorg[:1] + coords_reorg[1:][::-1]

        return coords_reorg

    def calcular_area_sinalizada(self, coords):
        """Calcula área sinalizada do polígono (Shoelace formula)"""
        n = len(coords)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += coords[i].x() * coords[j].y()
            area -= coords[j].x() * coords[i].y()
        return area / 2.0


    def processar_geometrias(self, outputs, feedback):
        """Processa as geometrias (simplificação, correção, etc)"""

        # Simplificar
        alg_params = {
            'INPUT': outputs['ExtrairLotes']['OUTPUT'],
            'METHOD': 0,
            'TOLERANCE': 0.001,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Simplificar'] = processing.run(
            'native:simplifygeometries',
            alg_params,
            feedback=feedback
        )
        feedback.setCurrentStep(4)

        # Remover vértices duplicados 1
        alg_params = {
            'INPUT': outputs['Simplificar']['OUTPUT'],
            'TOLERANCE': 1e-06,
            'USE_Z_VALUE': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RemoverDuplicados1'] = processing.run(
            'native:removeduplicatevertices',
            alg_params,
            feedback=feedback
        )
        feedback.setCurrentStep(5)

        # Corrigir geometrias
        alg_params = {
            'INPUT': outputs['RemoverDuplicados1']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CorrigirGeom'] = processing.run(
            'native:fixgeometries',
            alg_params,
            feedback=feedback
        )
        feedback.setCurrentStep(6)

        # Multipartes para partes simples
        alg_params = {
            'INPUT': outputs['CorrigirGeom']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['ParteSimples'] = processing.run(
            'native:multiparttosingleparts',
            alg_params,
            feedback=feedback
        )
        feedback.setCurrentStep(7)

        # Conectar feições - INTEGRADO
        feedback.pushInfo("Conectando feições...")
        outputs['Conectar'] = self.conectar_feicoes_integrado(
            outputs['ParteSimples']['OUTPUT'],
            tolerance=0.01,
            feedback=feedback
        )
        feedback.setCurrentStep(8)

        # Remover duplicados 2 e 3
        for i, step in enumerate([9, 10], start=2):
            prev_key = 'Conectar' if i == 2 else f'RemoverDuplicados{i-1}'
            alg_params = {
                'INPUT': outputs[prev_key]['OUTPUT'],
                'TOLERANCE': 1e-06,
                'USE_Z_VALUE': False,
                'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
            }
            outputs[f'RemoverDuplicados{i}'] = processing.run(
                'native:removeduplicatevertices',
                alg_params,
                feedback=feedback
            )
            feedback.setCurrentStep(step)

        # Ajustar geometrias
        alg_params = {
            'BEHAVIOR': 0,
            'INPUT': outputs['RemoverDuplicados3']['OUTPUT'],
            'REFERENCE_LAYER': outputs['RemoverDuplicados3']['OUTPUT'],
            'TOLERANCE': 0.0001,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['AjustarGeom'] = processing.run(
            'native:snapgeometries',
            alg_params,
            feedback=feedback
        )
        feedback.setCurrentStep(11)

        return outputs
    
    def editar_campos_lote(self, outputs, feedback):
        """Edita os campos da camada de lotes"""

        fields_mapping = [
            {'expression': '"id"', 'length': -1, 'name': 'id', 'precision': 0, 'type': 2},
            {'expression': '"id_localidade"', 'length': -1, 'name': 'id_localidade', 'precision': 0, 'type': 4},
            {'expression': '"id_setor"', 'length': -1, 'name': 'id_setor', 'precision': 0, 'type': 4},
            {'expression': '"id_bairro"', 'length': -1, 'name': 'id_bairro', 'precision': 0, 'type': 4},
            {'expression': '"id_quadra"', 'length': -1, 'name': 'id_quadra', 'precision': 0, 'type': 4},
            {'expression': '"matricula"', 'length': -1, 'name': 'matricula', 'precision': 0, 'type': 4},
            {'expression': '"sit_imovel"', 'length': -1, 'name': 'sit_imovel', 'precision': 0, 'type': 10},
            {'expression': '"data_atual"', 'length': -1, 'name': 'data_atual', 'precision': 0, 'type': 14},
            {'expression': '"usuario"', 'length': -1, 'name': 'usuario', 'precision': 0, 'type': 10},
            {'expression': '"poco"', 'length': 5, 'name': 'poco', 'precision': 0, 'type': 10},
            {'expression': '"piscina"', 'length': 5, 'name': 'piscina', 'precision': 0, 'type': 10},
            {'expression': '"clandestina"', 'length': 5, 'name': 'clandestina', 'precision': 0, 'type': 10},
            {'expression': '"abast_vizinho"', 'length': 5, 'name': 'abast_vizinho', 'precision': 0, 'type': 10},
            {'expression': '"transversal"', 'length': 5, 'name': 'transversal', 'precision': 0, 'type': 10},
            {'expression': '"numero"', 'length': -1, 'name': 'numero', 'precision': 0, 'type': 10},
            {'expression': '"ins_quadra"', 'length': -1, 'name': 'ins_quadra', 'precision': 0, 'type': 4},
            {'expression': '"sit_ligacao"', 'length': -1, 'name': 'sit_ligacao', 'precision': 0, 'type': 10},
            {'expression': '"matricula_aux"', 'length': -1, 'name': 'matricula_aux', 'precision': 0, 'type': 4},
            {'expression': '"acesso"', 'length': 30, 'name': 'acesso', 'precision': 0, 'type': 10},
            {'expression': '"quantidade_slote"', 'length': -1, 'name': 'quantidade_slote', 'precision': 0, 'type': 4},
            {'expression': '"inscricao"', 'length': -1, 'name': 'inscricao', 'precision': 0, 'type': 10},
            {'expression': '"lote_novo"', 'length': -1, 'name': 'lote_novo', 'precision': 0, 'type': 6},
            {'expression': '"observ"', 'length': -1, 'name': 'observ', 'precision': 0, 'type': 10},
            {'expression': '"ordem"', 'length': -1, 'name': 'ordem', 'precision': 0, 'type': 4}
        ]
        alg_params = {
            'FIELDS_MAPPING': fields_mapping,
            'INPUT': outputs['AjustarGeom']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        return processing.run('native:refactorfields', alg_params, feedback=feedback)
    
    def editar_campos_linhas(self, outputs, feedback):
        """Edita os campos da camada de linhas de testada"""

        fields_mapping = [
            {'expression': 'aggregate(layer:=\'Lote\', aggregate:=\'max\', expression:="id", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05)))',
             'length': 10, 'name': 'id_lote', 'precision': 0, 'type': 4},
            {'expression': 'id_quadra', 'length': 20, 'name': 'id_quadra', 'precision': 0, 'type': 4},
            {'expression': '"ins_quadra"', 'length': -1, 'name': 'ins_quadra', 'precision': 0, 'type': 4},
            {'expression': '"id_localidade"', 'length': 20, 'name': 'localidade', 'precision': 0, 'type': 4},
            {'expression': 'aggregate(layer:=\'Setor\', aggregate:=\'max\', expression:="setor", filter:=intersects($geometry, buffer(centroid(geometry(@parent)), 0.8)))',
             'length': 20, 'name': 'setor', 'precision': 0, 'type': 4},
            {'expression': 'aggregate(layer:=\'Quadra\', aggregate:=\'max\', expression:="quadra", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05)))',
             'length': 20, 'name': 'quadra', 'precision': 0, 'type': 4},
            {'expression': 'aggregate(layer:=\'Lote\', aggregate:=\'max\', expression:="transversal", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05)))',
             'length': 5, 'name': 'transversal', 'precision': 0, 'type': 10},
            {'expression': '"sequencia"', 'length': -1, 'name': 'sequencia', 'precision': 0, 'type': 2},
            {'expression': 'round("comprimento",2)', 'length': 5, 'name': 'testada', 'precision': 2, 'type': 6},
            {'expression': 'CASE WHEN aggregate(layer:=\'Lote\', aggregate:=\'max\', expression:="transversal", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05))) = \'true\' THEN \'false\' ELSE \'true\' END',
             'length': 5, 'name': 'mostrar', 'precision': 0, 'type': 1},
            {'expression': 'CASE WHEN aggregate(layer:=\'Lote\', aggregate:=\'max\', expression:="clandestina", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05))) = \'true\' or aggregate(layer:=\'Lote\', aggregate:=\'max\', expression:="abast_vizinho", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05)))= \'true\' or aggregate(layer:=\'Lote\', aggregate:=\'max\', expression:="sit_imovel", filter:=intersects($geometry, buffer(line_substring(geometry(@parent),0.25,0.25), 0.05))) = \'Terreno\' THEN \'false\' ELSE \'true\' END',
             'length': 5, 'name': 'mt', 'precision': 0, 'type': 10}
        ]
        alg_params = {
            'FIELDS_MAPPING': fields_mapping,
            'INPUT': outputs['RotacionarLinhas']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }

        return processing.run('native:refactorfields', alg_params, feedback=feedback)


    def calcular_angulo_rotacao(self, ponto_cardeal, inverter=False):
        """Calcula o ângulo de rotação baseado no ponto cardeal"""

        angulos = {
            0: 0,      # NORTE
            1: 315,    # NORDESTE
            2: 270,    # LESTE
            3: 225,    # SUDESTE
            4: 180,    # SUL
            5: 135,    # SUDOESTE
            6: 90,     # OESTE
            7: 45      # NOROESTE
        }

        angulos_inversos = {
            0: 0,      # NORTE
            1: 45,     # NORDESTE
            2: 90,     # LESTE
            3: 135,    # SUDESTE
            4: 180,    # SUL
            5: 225,    # SUDOESTE
            6: 270,    # OESTE
            7: 315     # NOROESTE
        }

        if inverter:
            return angulos.get(ponto_cardeal, 0)
        else:
            return angulos_inversos.get(ponto_cardeal, 0)
           