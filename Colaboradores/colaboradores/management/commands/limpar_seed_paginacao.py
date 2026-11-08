from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.deletion import ProtectedError
from django.db.models.functions import Coalesce

from Auditoria.auditoria.models import RegistroAuditoria
from Catalogo.fornecedores.models import Fornecedor
from Catalogo.produtos.models import Produto
from Clientes.clientes.models import Cliente
from Colaboradores.colaboradores.models import Colaborador, User
from Estoque.estoque.choices import SALDO_CHEIO
from Estoque.estoque.models import MovimentacaoEstoque
from Pedidos.pedidos.models import Pedido

from .seed_inicial import CPF_ADMIN, EMAIL_ADMIN, USERNAME_ADMIN
from .seed_paginacao import (
    CLIENTES,
    ENTREGADORES,
    FORNECEDORES,
    PRODUTOS_ACESSORIO,
    PRODUTOS_AGUA,
    PRODUTOS_GAS,
    _cnpj,
    _cpf,
)

OBSERVACAO_SEED = 'Seed de paginação'
MOTIVO_CARGA = 'Carga inicial do seed de paginação'
MARCA_DESCRICAO = 'Lote de teste'


class Command(BaseCommand):
    help = (
        'Remove o seed de paginação e também o que foi alterado ou lançado em cima dele: '
        'pedidos, estoque, auditoria e fichas editadas durante o teste. '
        'Preserva o administrador e o cadastro que não usa esses registros. '
        'Sem --confirmar, apenas lista.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Apaga o seed e o uso de teste feito em cima dele. Sem esta opção, só mostra a contagem.',
        )

    def handle(self, *args, **options):
        plano = _plano()
        self._resumo(plano)
        if _vazio(plano):
            self.stdout.write('Nenhum dado do seed de paginação foi encontrado.')
            return
        if not options['confirmar']:
            self.stdout.write(
                'Nada foi apagado. Pare o servidor, copie o banco e rode de novo com --confirmar.'
            )
            return
        try:
            with transaction.atomic():
                _apagar(plano)
        except ProtectedError as erro:
            raise CommandError(
                'Nada foi apagado. Ainda há cadastro protegido ligado ao seed de paginação. '
                f'Detalhe: {erro}'
            ) from erro
        self.stdout.write(
            self.style.SUCCESS(
                'Seed de paginação e o uso de teste feito em cima dele foram removidos. '
                'O administrador foi preservado.'
            )
        )

    def _resumo(self, plano):
        self.stdout.write('Seed e uso de teste em cima dele:')
        for rotulo, chave in (
            ('Clientes', 'clientes'),
            ('Pedidos', 'pedidos'),
            ('Produtos', 'produtos'),
            ('Fornecedores', 'fornecedores'),
            ('Entregadores', 'entregadores'),
            ('Movimentações', 'movimentos'),
            ('Auditoria', 'auditorias'),
            ('Contas de entregador', 'contas'),
        ):
            self.stdout.write(f'  {rotulo}: {len(plano[chave])}')
        admin = _administrador()
        if admin is None:
            self.stdout.write('Administrador do seed_inicial não está na base e não será criado.')
        else:
            self.stdout.write(
                f'Administrador preservado: {admin.username} ({admin.email}), '
                f'colaborador {admin.colaborador.nome}.'
            )


def _plano():
    produtos = _produtos()
    fornecedores = _fornecedores()
    entregadores = _sem_admin(_unir(_entregadores(), _entregadores_pelo_pedido()))
    clientes = _unir(_clientes(), _clientes_pelo_pedido())
    pedidos = _pedidos(produtos, clientes, entregadores)
    movimentos = _movimentos(produtos, fornecedores, clientes, pedidos)
    return {
        'produtos': produtos,
        'clientes': clientes,
        'fornecedores': fornecedores,
        'entregadores': entregadores,
        'pedidos': pedidos,
        'movimentos': movimentos,
        'auditorias': _auditorias(produtos, clientes, fornecedores, entregadores, pedidos),
        'contas': _contas(entregadores),
    }


def _produtos():
    return _ids(
        Produto.objects.filter(
            Q(codigo__in=_codigos_produto())
            | Q(nome__in=_nomes_produto())
            | Q(nome__contains='Paginação')
            | Q(descricao__contains=MARCA_DESCRICAO)
        )
    )


def _clientes():
    return _ids(
        Cliente.objects.filter(
            Q(nome__in=_nomes('Cliente Paginação', CLIENTES))
            | Q(nome__startswith='Cliente Paginação')
            | Q(observacoes=OBSERVACAO_SEED)
            | Q(telefone__in=_telefones_cliente())
        )
    )


def _fornecedores():
    nomes = _nomes('Distribuidora Paginação', FORNECEDORES)
    return _ids(
        Fornecedor.objects.filter(
            Q(cnpj__in=[_cnpj(90000000 + indice) for indice in range(1, FORNECEDORES + 1)])
            | Q(nome_fantasia__in=nomes)
            | Q(razao_social__in=[f'{nome} Ltda' for nome in nomes])
            | Q(nome_fantasia__contains='Paginação')
            | Q(razao_social__contains='Paginação')
        )
    )


def _entregadores():
    return _ids(
        Colaborador.objects.filter(
            Q(cpf__in=[_cpf(200 + indice) for indice in range(1, ENTREGADORES + 1)])
            | Q(nome__in=_nomes('Entregador Paginação', ENTREGADORES))
            | Q(nome__startswith='Entregador Paginação')
            | Q(placa_veiculo__in=[f'PAG{indice:02d}A1' for indice in range(1, ENTREGADORES + 1)])
        ).exclude(cpf=CPF_ADMIN)
    )


def _clientes_pelo_pedido():
    return _ids(
        Pedido.objects.filter(
            Q(nome_cliente__in=_nomes('Cliente Paginação', CLIENTES))
            | Q(nome_cliente__startswith='Cliente Paginação')
        ),
        'cliente_id',
    )


def _entregadores_pelo_pedido():
    return _ids(
        Pedido.objects.filter(
            Q(nome_entregador__in=_nomes('Entregador Paginação', ENTREGADORES))
            | Q(nome_entregador__startswith='Entregador Paginação')
        ),
        'entregador_id',
    )


def _pedidos(produtos, clientes, entregadores):
    return _ids(
        Pedido.objects.filter(
            Q(observacoes=OBSERVACAO_SEED)
            | _q_em('cliente_id', clientes)
            | _q_em('entregador_id', entregadores)
            | _q_em('itens__produto_id', produtos)
            | Q(nome_cliente__startswith='Cliente Paginação')
            | Q(nome_entregador__startswith='Entregador Paginação')
        ).distinct()
    )


def _movimentos(produtos, fornecedores, clientes, pedidos):
    return _ids(
        MovimentacaoEstoque.objects.filter(
            Q(motivo=MOTIVO_CARGA)
            | Q(motivo__icontains='seed de paginação')
            | _q_em('pedido_id', pedidos)
            | _q_em('produto_id', produtos)
            | _q_em('fornecedor_id', fornecedores)
            | _q_em('cliente_id', clientes)
            | Q(nome_produto__contains='Paginação')
            | Q(nome_fornecedor__contains='Paginação')
            | Q(nome_cliente__startswith='Cliente Paginação')
        ).distinct()
    )


def _contas(entregadores):
    if not entregadores:
        return []
    return _ids(
        User.objects.filter(colaborador_id__in=entregadores).exclude(id__in=_ids_admin() or [0])
    )


def _auditorias(produtos, clientes, fornecedores, entregadores, pedidos):
    partes = [
        Q(descricao__contains='Paginação'),
        Q(descricao__contains='Seed de paginação'),
        Q(descricao__contains=MARCA_DESCRICAO),
    ]
    for tipo, ids in (
        ('CLIENTE', clientes),
        ('PRODUTO', produtos),
        ('FORNECEDOR', fornecedores),
        ('COLABORADOR', entregadores),
        ('ESTOQUE', produtos),
        ('PEDIDO', pedidos),
    ):
        if ids:
            partes.append(Q(tipo_entidade=tipo, entidade_id__in=[str(identificador) for identificador in ids]))
    filtro = partes[0]
    for parte in partes[1:]:
        filtro |= parte
    return _ids(RegistroAuditoria.objects.filter(filtro))


def _apagar(plano):
    admin = _administrador()
    admin_id = None if admin is None else admin.id
    colaborador_admin_id = None if admin is None else admin.colaborador_id
    clientes_reais_afetados = list(
        Pedido.objects.filter(id__in=plano['pedidos'] or [0])
        .exclude(cliente_id__in=plano['clientes'] or [0])
        .values_list('cliente_id', flat=True)
        .distinct()
    )
    _repor_saldo(plano['movimentos'], plano['produtos'])
    MovimentacaoEstoque.objects.filter(id__in=plano['movimentos'] or [0]).delete()
    Pedido.objects.filter(id__in=plano['pedidos'] or [0]).delete()
    _recompor_totais(clientes_reais_afetados)
    RegistroAuditoria.objects.filter(id__in=plano['auditorias'] or [0]).delete()
    User.objects.filter(id__in=plano['contas'] or [0]).delete()
    Cliente.objects.filter(id__in=plano['clientes'] or [0]).delete()
    Produto.objects.filter(id__in=plano['produtos'] or [0]).delete()
    Fornecedor.objects.filter(id__in=plano['fornecedores'] or [0]).delete()
    Colaborador.objects.filter(id__in=plano['entregadores'] or [0]).delete()
    if admin_id is not None and not User.objects.filter(id=admin_id, colaborador_id=colaborador_admin_id).exists():
        raise CommandError('A limpeza removeria o administrador. A transação foi desfeita.')
    _apagar_historico(
        (
            (MovimentacaoEstoque, plano['movimentos']),
            (Pedido, plano['pedidos']),
            (RegistroAuditoria, plano['auditorias']),
            (User, plano['contas']),
            (Cliente, plano['clientes']),
            (Produto, plano['produtos']),
            (Fornecedor, plano['fornecedores']),
            (Colaborador, plano['entregadores']),
        )
    )


def _repor_saldo(movimentos, produtos_apagados):
    ajustes = {}
    consulta = MovimentacaoEstoque.objects.filter(id__in=movimentos or [0]).exclude(
        produto_id__in=produtos_apagados or [0]
    )
    for movimento in consulta:
        cheio, seco = ajustes.setdefault(movimento.produto_id, [0, 0])
        if movimento.tipo_saldo == SALDO_CHEIO:
            ajustes[movimento.produto_id] = [cheio + movimento.quantidade, seco]
        else:
            ajustes[movimento.produto_id] = [cheio, seco + movimento.quantidade]
    for produto_id, (cheio, seco) in ajustes.items():
        produto = Produto.objects.get(pk=produto_id)
        produto.saldo_cheio = max(0, produto.saldo_cheio - cheio)
        produto.saldo_seco = max(0, produto.saldo_seco - seco)
        produto.save(update_fields=['saldo_cheio', 'saldo_seco', 'updated_at'])


def _recompor_totais(clientes_ids):
    if not clientes_ids:
        return
    agregados = {
        linha['cliente_id']: linha
        for linha in Pedido.objects.filter(cliente_id__in=clientes_ids)
        .values('cliente_id')
        .annotate(
            quantidade=Count('id'),
            gasto=Coalesce(
                Sum('total'),
                Value(Decimal('0.00')),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
    }
    for cliente in Cliente.objects.filter(id__in=clientes_ids):
        linha = agregados.get(cliente.id)
        cliente.total_pedidos = 0 if linha is None else linha['quantidade']
        cliente.total_gasto = Decimal('0.00') if linha is None else linha['gasto']
        cliente.save(update_fields=['total_pedidos', 'total_gasto', 'updated_at'])


def _apagar_historico(pares):
    for modelo, ids in pares:
        if not ids or not hasattr(modelo, 'history'):
            continue
        modelo.history.model.objects.filter(id__in=ids).delete()


def _administrador():
    return (
        User.objects.filter(Q(username=USERNAME_ADMIN) | Q(email=EMAIL_ADMIN) | Q(colaborador__cpf=CPF_ADMIN))
        .select_related('colaborador')
        .order_by('id')
        .first()
    )


def _ids_admin():
    return list(
        User.objects.filter(
            Q(username=USERNAME_ADMIN) | Q(email=EMAIL_ADMIN) | Q(colaborador__cpf=CPF_ADMIN)
        ).values_list('id', flat=True)
    )


def _ids_colaborador_admin():
    return list(
        User.objects.filter(
            Q(username=USERNAME_ADMIN) | Q(email=EMAIL_ADMIN) | Q(colaborador__cpf=CPF_ADMIN)
        ).values_list('colaborador_id', flat=True)
    )


def _sem_admin(ids):
    protegidos = set(_ids_colaborador_admin())
    return [identificador for identificador in ids if identificador not in protegidos]


def _codigos_produto():
    total = PRODUTOS_GAS + PRODUTOS_AGUA + PRODUTOS_ACESSORIO
    return [f'PG-{indice:02d}' for indice in range(1, total + 1)]


def _nomes_produto():
    bases = (
        ['Botijão P13'] * PRODUTOS_GAS
        + ['Galão 20L'] * PRODUTOS_AGUA
        + ['Registro de gás'] * PRODUTOS_ACESSORIO
    )
    return [f'{base} Paginação {indice:02d}' for indice, base in enumerate(bases, start=1)]


def _telefones_cliente():
    return [f'1199{indice:07d}' for indice in range(1, CLIENTES + 1)]


def _nomes(prefixo, quantidade):
    return [f'{prefixo} {indice:02d}' for indice in range(1, quantidade + 1)]


def _ids(consulta, campo='id'):
    return list(dict.fromkeys(consulta.values_list(campo, flat=True)))


def _unir(base, extras):
    return list(dict.fromkeys([*base, *extras]))


def _q_em(campo, ids):
    if not ids:
        return Q(pk__in=[])
    return Q(**{f'{campo}__in': ids})


def _vazio(plano):
    return not any(
        plano[chave]
        for chave in (
            'produtos',
            'clientes',
            'fornecedores',
            'entregadores',
            'pedidos',
            'movimentos',
            'auditorias',
            'contas',
        )
    )
