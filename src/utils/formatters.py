# src/utils/formatters.py
from datetime import datetime
from typing import Union
import locale

# Tentar configurar locale brasileiro
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except:
        pass  # Fallback para formatação manual

def format_currency(value: Union[int, float], symbol: str = "R$") -> str:
    """
    Formata valor monetário no padrão brasileiro
    Exemplo: 1234.56 -> "R$ 1.234,56"
    """
    if value is None:
        return f"{symbol} 0,00"
    
    # Formatar com ponto como separador de milhar e vírgula como decimal
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{symbol} {formatted}"

def format_date_br(date_value: Union[datetime, str], format_type: str = "short") -> str:
    """
    Formata data no padrão brasileiro
    
    Args:
        date_value: datetime object ou string ISO
        format_type: 
            - "short": DD/MM/YYYY
            - "long": DD de Mês de YYYY
            - "datetime": DD/MM/YYYY HH:MM
    
    Exemplo: 2025-11-20 -> "20/11/2025"
    """
    if date_value is None:
        return "N/A"
    
    # Converter string ISO para datetime se necessário
    if isinstance(date_value, str):
        try:
            # Remover timezone se houver
            date_str = date_value.replace('Z', '+00:00')
            if 'T' in date_str:
                date_value = datetime.fromisoformat(date_str)
            else:
                date_value = datetime.fromisoformat(date_str)
        except:
            return date_value  # Retornar original se falhar
    
    # Formatação baseada no tipo
    if format_type == "short":
        return date_value.strftime('%d/%m/%Y')
    elif format_type == "long":
        meses = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        return f"{date_value.day} de {meses[date_value.month]} de {date_value.year}"
    elif format_type == "datetime":
        return date_value.strftime('%d/%m/%Y %H:%M')
    else:
        return date_value.strftime('%d/%m/%Y')

def format_number_br(value: Union[int, float], decimals: int = 2) -> str:
    """
    Formata número no padrão brasileiro
    Exemplo: 1234.56 -> "1.234,56"
    """
    if value is None:
        return "0" + (",00" if decimals > 0 else "")
    
    # Formatar com separadores brasileiros
    if decimals > 0:
        formatted = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    else:
        formatted = f"{int(value):,}".replace(",", ".")
    
    return formatted

def parse_currency_input(value_str: str) -> float:
    """
    Converte string em formato brasileiro para float
    Exemplo: "R$ 1.234,56" -> 1234.56
    """
    if not value_str:
        return 0.0
    
    # Remover símbolo de moeda e espaços
    cleaned = value_str.replace("R$", "").replace(" ", "").strip()
    
    # Substituir separadores brasileiros
    cleaned = cleaned.replace(".", "").replace(",", ".")
    
    try:
        return float(cleaned)
    except:
        return 0.0
