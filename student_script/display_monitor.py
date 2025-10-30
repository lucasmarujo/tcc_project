"""
Módulo para verificação de múltiplos monitores.
"""
import logging
from screeninfo import get_monitors

logger = logging.getLogger(__name__)


def check_multiple_monitors() -> tuple[bool, int, list]:
    """
    Verifica se o computador está conectado a múltiplos monitores.
    
    Returns:
        tuple: (tem_multiplos_monitores: bool, numero_monitores: int, lista_monitores: list)
    """
    try:
        monitors = get_monitors()
        num_monitors = len(monitors)
        
        monitor_info = []
        for i, monitor in enumerate(monitors, 1):
            info = {
                'index': i,
                'name': monitor.name,
                'width': monitor.width,
                'height': monitor.height,
                'x': monitor.x,
                'y': monitor.y,
                'is_primary': getattr(monitor, 'is_primary', None)
            }
            monitor_info.append(info)
            logger.info(f"Monitor {i}: {monitor.width}x{monitor.height} @ ({monitor.x}, {monitor.y}) - {monitor.name}")
        
        has_multiple = num_monitors > 1
        
        if has_multiple:
            logger.warning(f"ATENÇÃO: {num_monitors} monitores detectados!")
        else:
            logger.info(f"OK: Apenas 1 monitor detectado")
        
        return has_multiple, num_monitors, monitor_info
    
    except Exception as e:
        logger.error(f"Erro ao verificar monitores: {e}", exc_info=True)
        # Em caso de erro, assume que há apenas 1 monitor
        return False, 1, []


def get_monitor_info_text(monitor_info: list) -> str:
    """
    Retorna uma string formatada com as informações dos monitores.
    
    Args:
        monitor_info: Lista com informações dos monitores
    
    Returns:
        str: Texto formatado
    """
    if not monitor_info:
        return "Nenhuma informação de monitor disponível"
    
    lines = []
    for monitor in monitor_info:
        line = (f"Monitor {monitor['index']}: "
                f"{monitor['width']}x{monitor['height']} "
                f"@ ({monitor['x']}, {monitor['y']})")
        if monitor.get('name'):
            line += f" - {monitor['name']}"
        if monitor.get('is_primary'):
            line += " [PRINCIPAL]"
        lines.append(line)
    
    return "\n".join(lines)

