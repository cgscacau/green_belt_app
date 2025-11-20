"""
Utilitários para formatação de valores em padrão brasileiro
"""
from datetime import datetime
from typing import Union, Optional

def format_currency(value: Union[float, int], symbol: str = "R$") -> str:
    """
    Formata valor monetário no padrão brasileiro
    
    Args:
        value: Valor numérico a ser formatado
        symbol: Símbolo da moeda (padrão: R$)
    
    Returns:
        String formatada no padrão BR (ex: R$ 1.234,56)
    
    Examples:
        >>> format_currency(1234.56)
        'R$ 1.234,56'
        >>> format_currency(1000000)
        'R$ 1.000.000,00'
    """
    try:
        # Formata com separadores brasileiros
        formatted = f"{float(value):,.2f}"
        # Inverte: ponto↔vírgula
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return f"{symbol} {formatted}"
    except (ValueError, TypeError):
        return f"{symbol} 0,00"


def format_date_br(date_value: Union[str, datetime], format_input: str = "iso") -> str:
    """
    Converte data para formato brasileiro DD/MM/YYYY
    
    Args:
        date_value: Data em string ISO, datetime ou timestamp
        format_input: Tipo do input ('iso', 'datetime', 'timestamp')
    
    Returns:
        String formatada DD/MM/YYYY
    
    Examples:
        >>> format_date_br("2024-03-15")
        '15/03/2024'
        >>> format_date_br("2024-03-15T10:30:00")
        '15/03/2024'
    """
    try:
        if isinstance(date_value, datetime):
            return date_value.strftime('%d/%m/%Y')
        
        if isinstance(date_value, str):
            # Remove timezone e microsegundos se presentes
            date_str = date_value.split('T')[0] if 'T' in date_value else date_value
            date_str = date_str.split('+')[0].split('Z')[0]
            
            # Tenta parsear ISO format (YYYY-MM-DD)
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%d/%m/%Y')
        
        return "Data inválida"
    
    except (ValueError, AttributeError, TypeError):
        return "Data inválida"


def format_number_br(value: Union[float, int], decimals: int = 2) -> str:
    """
    Formata número com separadores brasileiros
    
    Args:
        value: Número a ser formatado
        decimals: Casas decimais (padrão: 2)
    
    Returns:
        String formatada (ex: 1.234,56)
    
    Examples:
        >>> format_number_br(1234.567)
        '1.234,57'
        >>> format_number_br(1000000, decimals=0)
        '1.000.000'
    """
    try:
        formatted = f"{float(value):,.{decimals}f}"
        # Inverte separadores
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
        return formatted
    except (ValueError, TypeError):
        return "0" + (",00" if decimals > 0 else "")


def parse_currency_input(value_str: str) -> float:
    """
    Converte entrada de texto BR para float
    
    Args:
        value_str: String com valor (ex: "R$ 1.234,56" ou "1.234,56")
    
    Returns:
        Float do valor
    
    Examples:
        >>> parse_currency_input("R$ 1.234,56")
        1234.56
        >>> parse_currency_input("1.234,56")
        1234.56
    """
    try:
        # Remove símbolos de moeda e espaços
        cleaned = value_str.replace('R$', '').replace(' ', '').strip()
        # Remove pontos (milhares) e substitui vírgula por ponto (decimal)
        cleaned = cleaned.replace('.', '').replace(',', '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0

def validate_currency_input(value_str):
    """
    Valida e retorna feedback visual para input de moeda.
    Retorna: (value_float, is_valid, error_message)
    """
    if not value_str or value_str.strip() == "":
        return 0.0, True, ""
    
    try:
        value = parse_currency_input(value_str)
        return value, True, ""
    except ValueError as e:
        return 0.0, False, f"❌ Formato inválido. Use: 1.234,56 ou 1234,56"

def format_date_input(date_obj):
    """
    Formata objeto date para string DD/MM/YYYY para exibição em text_input.
    """
    if date_obj is None:
        return ""
    if isinstance(date_obj, str):
        # Se já é string, tentar converter
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except:
            return date_obj
    return date_obj.strftime("%d/%m/%Y")

def parse_date_input(date_str):
    """
    Converte string DD/MM/YYYY para objeto date.
    Retorna: (date_obj, is_valid, error_message)
    """
    if not date_str or date_str.strip() == "":
        return None, True, ""
    
    try:
        # Remove espaços
        date_str = date_str.strip()
        
        # Tenta formato DD/MM/YYYY
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        
        # Validação básica de data
        if date_obj.year < 2000 or date_obj.year > 2100:
            return None, False, "❌ Ano deve estar entre 2000 e 2100"
        
        return date_obj, True, ""
    
    except ValueError:
        return None, False, "❌ Formato inválido. Use: DD/MM/AAAA (ex: 20/11/2025)"

