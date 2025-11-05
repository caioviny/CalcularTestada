"""
Dialog UI Moderna para Calcular Testada
Interface criada com PyQt5 para QGIS
"""
from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QGroupBox, QFrame
from qgis.PyQt.QtGui import QFont, QIcon, QColor, QPalette


class CalcularTestadaDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.carregar_conexoes()
    
    def setupUi(self):
        """Configura a interface moderna"""
        self.setObjectName("CalcularTestadaDialog")
        self.resize(500, 400)
        self.setWindowTitle("Calcular Testada - UMC GEO")
        
        # Aplica estilo moderno
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
                font-size: 11pt;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2196F3;
            }
            QLabel {
                color: #424242;
                font-size: 10pt;
            }
            QComboBox {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                min-height: 25px;
            }
            QComboBox:hover {
                border: 2px solid #2196F3;
            }
            QComboBox:focus {
                border: 2px solid #1976D2;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #757575;
                margin-right: 8px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
            QPushButton#btnSelecionar {
                background-color: #4CAF50;
            }
            QPushButton#btnSelecionar:hover {
                background-color: #388E3C;
            }
            QPushButton#btnCancelar {
                background-color: #757575;
            }
            QPushButton#btnCancelar:hover {
                background-color: #616161;
            }
            QLabel#lblStatus {
                background-color: #E3F2FD;
                border-left: 4px solid #2196F3;
                padding: 10px;
                border-radius: 4px;
                color: #1565C0;
                font-weight: bold;
            }
        """)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("🗺️ Calcular Testada dos Lotes")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Linha separadora
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e0e0e0;")
        main_layout.addWidget(line)
        
        # === GRUPO: Seleção de Quadra ===
        group_quadra = QGroupBox("1️⃣ Seleção de Quadra")
        layout_quadra = QVBoxLayout()
        layout_quadra.setSpacing(10)
        
        # Label informativa
        info_label = QLabel("Clique no botão abaixo e depois clique na quadra desejada no mapa")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #616161; font-size: 9pt; margin-bottom: 5px;")
        layout_quadra.addWidget(info_label)
        
        # Botão selecionar quadra
        self.btnSelecionar = QPushButton("🎯 Selecionar Quadra no Mapa")
        self.btnSelecionar.setObjectName("btnSelecionar")
        self.btnSelecionar.setCursor(Qt.PointingHandCursor)
        layout_quadra.addWidget(self.btnSelecionar)
        
        # Label de status da seleção
        self.lblStatus = QLabel("Nenhuma quadra selecionada")
        self.lblStatus.setObjectName("lblStatus")
        self.lblStatus.setAlignment(Qt.AlignCenter)
        layout_quadra.addWidget(self.lblStatus)
        
        group_quadra.setLayout(layout_quadra)
        main_layout.addWidget(group_quadra)
        
        # === GRUPO: Configurações ===
        group_config = QGroupBox("2️⃣ Configurações")
        layout_config = QVBoxLayout()
        layout_config.setSpacing(12)
        
        # Conexão com banco
        label_conexao = QLabel("Conexão com Banco de Dados:")
        label_conexao.setStyleSheet("font-weight: bold;")
        layout_config.addWidget(label_conexao)
        
        self.comboConexao = QComboBox()
        self.comboConexao.setMinimumHeight(35)
        layout_config.addWidget(self.comboConexao)
        
        # Ponto Cardeal
        label_cardeal = QLabel("Ponto Cardeal de Referência:")
        label_cardeal.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout_config.addWidget(label_cardeal)
        
        self.comboPontoCardeal = QComboBox()
        self.comboPontoCardeal.setMinimumHeight(35)
        self.comboPontoCardeal.addItems([
            "Norte", "Nordeste", "Leste", "Sudeste",
            "Sul", "Sudoeste", "Oeste", "Noroeste"
        ])
        layout_config.addWidget(self.comboPontoCardeal)
        
        group_config.setLayout(layout_config)
        main_layout.addWidget(group_config)
        
        # Espaçador
        main_layout.addStretch()
        
        # === BOTÕES DE AÇÃO ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.btnCancelar = QPushButton("✖ Cancelar")
        self.btnCancelar.setObjectName("btnCancelar")
        self.btnCancelar.setCursor(Qt.PointingHandCursor)
        self.btnCancelar.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btnCancelar)
        
        self.btnExecutar = QPushButton("▶ Executar Processamento")
        self.btnExecutar.setCursor(Qt.PointingHandCursor)
        self.btnExecutar.setEnabled(False)
        buttons_layout.addWidget(self.btnExecutar)
        
        main_layout.addLayout(buttons_layout)
        
    def carregar_conexoes(self):
        """Carrega as conexões disponíveis do PostgreSQL"""
        from qgis.core import QgsProviderRegistry
        
        try:
            # Obtém metadados do provider PostgreSQL
            md = QgsProviderRegistry.instance().providerMetadata('postgres')
            
            if md:
                conexoes = md.connections()
                
                if conexoes:
                    for nome_conexao in conexoes.keys():
                        self.comboConexao.addItem(nome_conexao)
                else:
                    self.comboConexao.addItem("Nenhuma conexão disponível")
            else:
                self.comboConexao.addItem("Erro ao acessar conexões")
                
        except Exception as e:
            self.comboConexao.addItem(f"Erro: {str(e)}")
    
    def atualizar_status_selecao(self, num_quadras):
        """Atualiza o label de status com o número de quadras selecionadas"""
        if num_quadras > 0:
            self.lblStatus.setText(f"✅ {num_quadras} quadra(s) selecionada(s)")
            self.lblStatus.setStyleSheet("""
                background-color: #E8F5E9;
                border-left: 4px solid #4CAF50;
                padding: 10px;
                border-radius: 4px;
                color: #2E7D32;
                font-weight: bold;
            """)
            self.btnExecutar.setEnabled(True)
        else:
            self.lblStatus.setText("⚠️ Nenhuma quadra selecionada")
            self.lblStatus.setStyleSheet("""
                background-color: #FFF3E0;
                border-left: 4px solid #FF9800;
                padding: 10px;
                border-radius: 4px;
                color: #E65100;
                font-weight: bold;
            """)
            self.btnExecutar.setEnabled(False)