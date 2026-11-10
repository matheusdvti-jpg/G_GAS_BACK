def registrar_acesso(acao, identificador, ip, usuario=None):
    from Auditoria.auditoria.business import RegistroAuditoriaBusiness

    colaborador = getattr(usuario, 'colaborador', None) if usuario is not None else None
    if colaborador is not None:
        nome = colaborador.nome
        entidade = str(usuario.pk)
    else:
        nome = (identificador or '').strip() or 'desconhecido'
        entidade = nome
    RegistroAuditoriaBusiness().registrar(
        acao=acao,
        tipo_entidade='CONTA',
        entidade_id=entidade[:64],
        descricao=f'{acao} a partir de {ip}.',
        usuario=usuario,
        nome_usuario=nome[:150],
        alteracoes={'ip': ip, 'identificador': nome[:150]},
    )
