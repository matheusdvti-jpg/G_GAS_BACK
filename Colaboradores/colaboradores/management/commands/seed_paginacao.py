from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from Catalogo.fornecedores.business import FornecedorBusiness
from Catalogo.produtos.business import ProdutoBusiness
from Catalogo.produtos.choices import CATEGORIA_AGUA, CATEGORIA_GAS
from Catalogo.produtos.models import Produto
from Clientes.clientes.business import ClienteBusiness
from Colaboradores.colaboradores.business import ColaboradorBusiness
from Colaboradores.colaboradores.choices import PERFIL_ENTREGADOR
from Colaboradores.colaboradores.models import User
from Estoque.estoque.business import MovimentacaoBusiness
from Pedidos.pedidos.business import PedidoBusiness
from Pedidos.pedidos.choices import (
    PAGAMENTO_CREDITO,
    PAGAMENTO_DEBITO,
    PAGAMENTO_DINHEIRO,
    PAGAMENTO_PIX,
    STATUS_CANCELADO,
    STATUS_ENTREGUE,
    STATUS_PENDENTE,
)

from .seed_inicial import EMAIL_ADMIN, USERNAME_ADMIN

MARCA = 'PG-01'
CLIENTES = 25
ENTREGADORES = 25
FORNECEDORES = 15
PRODUTOS_GAS = 15
PRODUTOS_AGUA = 5
PRODUTOS_ACESSORIO = 5
PEDIDOS = 35
PEDIDOS_DO_PRIMEIRO_CLIENTE = 12
CARGA = 40

# 12 do primeiro cliente (histórico passa de 10) e 23 dos demais.
# Totais: 22 pendentes, 8 entregues, 5 cancelados.
STATUS = (
    [STATUS_PENDENTE] * 4
    + [STATUS_ENTREGUE] * 5
    + [STATUS_CANCELADO] * 3
    + [STATUS_PENDENTE] * 18
    + [STATUS_ENTREGUE] * 3
    + [STATUS_CANCELADO] * 2
)
PAGAMENTOS = (PAGAMENTO_PIX, PAGAMENTO_DINHEIRO, PAGAMENTO_DEBITO, PAGAMENTO_CREDITO)
MARCAS = ('Nacional', 'Liquigás', 'Copagaz', 'Consigaz', 'Supergasbras')


class Command(BaseCommand):
    help = (
        'Cria clientes, pedidos, produtos, fornecedores e entregadores '
        'para testar a paginação. Não duplica se o produto PG-01 já existir.'
    )

    def handle(self, *args, **options):
        if Produto.objects.filter(codigo=MARCA).exists():
            self.stdout.write('Seed de paginação já existe (produto PG-01). Nada foi alterado.')
            return

        call_command('seed_inicial')
        usuario = User.objects.get(username=USERNAME_ADMIN)
        with transaction.atomic():
            entregadores = self._entregadores(usuario)
            fornecedores = self._fornecedores(usuario)
            produtos = self._produtos(usuario)
            self._carga(produtos, fornecedores[0], usuario)
            clientes = self._clientes(usuario)
            self._pedidos(clientes, entregadores, produtos, usuario)

        self.stdout.write(
            self.style.SUCCESS(
                'Seed de paginação criado. '
                f'Clientes: {CLIENTES} (página de 10; o primeiro tem {PEDIDOS_DO_PRIMEIRO_CLIENTE} pedidos). '
                f'Pedidos: {PEDIDOS} (22 pendentes, 8 entregues, 5 cancelados; página de 10). '
                f'Produtos: {PRODUTOS_GAS + PRODUTOS_AGUA + PRODUTOS_ACESSORIO} (página de 20). '
                f'Fornecedores: {FORNECEDORES} (página de 10). '
                f'Entregadores: {ENTREGADORES} (página de 20). '
                'Busca: Paginação.'
            )
        )
        self.stdout.write(f'Entre com {USERNAME_ADMIN} ou {EMAIL_ADMIN}.')

    def _entregadores(self, usuario):
        criados = []
        for indice in range(1, ENTREGADORES + 1):
            criados.append(
                ColaboradorBusiness().criar(
                    {
                        'nome': f'Entregador Paginação {indice:02d}',
                        'cpf': _cpf(200 + indice),
                        'telefone': f'1198{indice:07d}',
                        'perfil': PERFIL_ENTREGADOR,
                        'ativo': True,
                        'placa_veiculo': f'PAG{indice:02d}A1',
                    },
                    usuario,
                )
            )
        return criados

    def _fornecedores(self, usuario):
        criados = []
        for indice in range(1, FORNECEDORES + 1):
            criados.append(
                FornecedorBusiness().criar(
                    {
                        'nome_fantasia': f'Distribuidora Paginação {indice:02d}',
                        'razao_social': f'Distribuidora Paginação {indice:02d} Ltda',
                        'cnpj': _cnpj(90000000 + indice),
                        'telefone': f'1133{indice:07d}',
                        'nome_contato': f'Contato Paginação {indice:02d}',
                        'endereco': f'Avenida Industrial, {indice * 10}',
                        'cidade': 'São Paulo',
                        'produtos_fornecidos': ['Botijão P13', 'Galão 20L'],
                        'ativo': True,
                    },
                    usuario,
                )
            )
        return criados

    def _produtos(self, usuario):
        criados = []
        especificacoes = (
            [(CATEGORIA_GAS, 'Botijão P13', 'Botijão de gás de 13 kg', 'un')] * PRODUTOS_GAS
            + [(CATEGORIA_AGUA, 'Galão 20L', 'Galão de água mineral de 20 litros', 'un')] * PRODUTOS_AGUA
            + [('ACESSORIO', 'Registro de gás', 'Registro metálico para instalação', 'un')] * PRODUTOS_ACESSORIO
        )
        for indice, (categoria, nome, descricao, unidade) in enumerate(especificacoes, start=1):
            criados.append(
                ProdutoBusiness().criar(
                    {
                        'codigo': f'PG-{indice:02d}',
                        'nome': f'{nome} Paginação {indice:02d}',
                        'descricao': f'{descricao}. Lote de teste {indice:02d}.',
                        'marca': MARCAS[(indice - 1) % len(MARCAS)],
                        'categoria': categoria,
                        'preco_venda': Decimal('90.00') + indice,
                        'preco_custo': Decimal('60.00') + indice,
                        'saldo_cheio': 0,
                        'saldo_seco': 0,
                        'estoque_minimo': 4,
                        'unidade': unidade,
                        'ativo': True,
                    },
                    usuario,
                )
            )
        return criados

    def _carga(self, produtos, fornecedor, usuario):
        movimento = MovimentacaoBusiness()
        for produto in produtos:
            movimento.registrar_entrada(
                produto.id,
                fornecedor.id,
                CARGA,
                produto.preco_custo,
                usuario,
                'Carga inicial do seed de paginação',
            )

    def _clientes(self, usuario):
        criados = []
        for indice in range(1, CLIENTES + 1):
            bairro = 'Centro' if indice <= 13 else 'Vila Nova'
            criados.append(
                ClienteBusiness().criar(
                    {
                        'nome': f'Cliente Paginação {indice:02d}',
                        'telefone': f'1199{indice:07d}',
                        'telefone_secundario': '',
                        'logradouro': 'Rua das Flores',
                        'numero': str(100 + indice),
                        'complemento': '',
                        'bairro': bairro,
                        'cidade': 'São Paulo',
                        'ponto_referencia': f'Perto da praça {indice:02d}',
                        'observacoes': 'Seed de paginação',
                    },
                    usuario,
                )
            )
        return criados

    def _pedidos(self, clientes, entregadores, produtos, usuario):
        gases = [produto for produto in produtos if produto.categoria == CATEGORIA_GAS]
        aguas = [produto for produto in produtos if produto.categoria == CATEGORIA_AGUA]
        agua_usada = 0
        for indice in range(PEDIDOS):
            if indice % 7 == 0:
                produto = aguas[agua_usada % len(aguas)]
                agua_usada += 1
                vazios = 1
            else:
                produto = gases[indice % len(gases)]
                vazios = None
            cliente = clientes[0] if indice < PEDIDOS_DO_PRIMEIRO_CLIENTE else clientes[(indice % (CLIENTES - 1)) + 1]
            pedido = PedidoBusiness().criar(
                {
                    'cliente_id': cliente.id,
                    'entregador_id': entregadores[indice % len(entregadores)].id,
                    'forma_pagamento': PAGAMENTOS[indice % len(PAGAMENTOS)],
                    'itens': [
                        {
                            'produto_id': produto.id,
                            'quantidade': 1,
                            'vazios_recebidos': vazios,
                        }
                    ],
                    'observacoes': 'Seed de paginação',
                },
                usuario,
            )
            status = STATUS[indice]
            if status == STATUS_PENDENTE:
                continue
            pedido.business.alterar_status(
                status,
                usuario,
                'Cancelado no seed de paginação' if status == STATUS_CANCELADO else '',
            )


def _cpf(numero):
    base = f'{numero:09d}'
    primeiro = _digito(base)
    return base + primeiro + _digito(base + primeiro)


def _cnpj(numero):
    base = f'{numero:08d}0001'
    primeiro = _digito(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return base + primeiro + _digito(base + primeiro, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])


def _digito(base, pesos=None):
    if pesos is None:
        pesos = range(len(base) + 1, 1, -1)
    total = sum(int(digito) * peso for digito, peso in zip(base, pesos))
    resto = total % 11
    return '0' if resto < 2 else str(11 - resto)
