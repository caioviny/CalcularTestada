"""
Plugin Calcular Testada para QGIS
"""

def classFactory(iface):
    """Carrega a classe CalcularTestada do arquivo Calcular_Testada.py
    
    :param iface: Uma instância da interface do QGIS (QgsInterface)
    :type iface: QgsInterface
    """
    from .Calcular_Testada import CalcularTestada
    return CalcularTestada(iface)