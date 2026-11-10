from django.conf import settings


def ip_do_cliente(request) -> str:
    """Usa o endereço que o proxy da hospedagem acrescenta. Fora dele, ignora o cabeçalho do cliente."""
    remoto = (request.META.get('REMOTE_ADDR') or '').strip() or '0.0.0.0'
    cabecalho = getattr(settings, 'IP_CABECALHO_PROXY', '') or ''
    if not cabecalho:
        return remoto[:45]
    bruto = request.META.get(cabecalho) or ''
    partes = [parte.strip() for parte in bruto.split(',') if parte.strip()]
    if not partes:
        return remoto[:45]
    return partes[-1][:45]
