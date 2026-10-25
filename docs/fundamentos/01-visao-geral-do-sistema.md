# G-GÁS — Visão geral do sistema

## Contexto

G-GÁS é o sistema de gestão de uma distribuidora de gás (GLP) e água mineral. O balcão registra a venda, o depósito controla botijão cheio e vazio, e o entregador confirma a entrega na rua.

O back-end é um monólito modular em Django, na pasta `G_GAS_BACK`. O front, em `G_GAS_FRONT`, é um painel React com Vite. Hoje o front ainda persiste no navegador. A API já cobre o mesmo fluxo para substituir esse armazenamento.

A operação prevista no início cabe em uma máquina. Por isso o banco é SQLite. PostgreSQL fica para quando houver mais de um processo gravando ao mesmo tempo.

## Proposta

O sistema transforma o controle de papel e planilha em um fluxo com saldo, troca de vasilhame e permissão por função:

- saber quem pode vender, quem mexe no depósito e quem só confirma a própria entrega;
- baixar o cheio e receber o seco na mesma venda;
- desfazer a baixa se a venda for cancelada, sem apagar o histórico;
- fechar o dia com faturamento, desconto, forma de pagamento e entregador.

## Atores

| Perfil | Papel |
| --- | --- |
| Administrador | Tudo, inclusive auditoria e o último administrador que não pode ser desligado |
| Gerente | Cadastros, estoque, venda, desconto, cancelamento, reabertura e relatórios |
| Atendente | Cliente, venda e desconto. Não cancela, não confirma entrega e não vê o fechamento financeiro |
| Estoquista | Entrada, saída manual, empréstimo e conferência |
| Entregador | Confirma somente a entrega atribuída a ele |

A matriz está em `Colaboradores/colaboradores/permissoes.py`. Administrador e superusuário passam em qualquer código.

O atalho de trocar de usuário que existe no protótipo do front não é endpoint.

## Fluxos centrais

### Entrar

`POST /auth/token_jwt/` com usuário ou e-mail. A conta e o colaborador precisam estar ativos. `GET /auth/eu/` devolve nome, perfil e colaborador.

O comando `python manage.py seed_inicial` cria o administrador local `admin` / `Ggas@123`.

### Cadastrar

Cliente (atendente), produto e fornecedor (gerente). Produto, cliente e fornecedor não dependem uns dos outros. O saldo inicial do produto pode nascer no cadastro. Dali em diante só a movimentação altera cheio e seco.

### Abastecer

O estoquista lança carga de fornecedor, saída por perda, avaria, consumo ou empréstimo, e a contagem do depósito. Cada lançamento grava movimentação e auditoria.

### Vender e entregar

O atendente abre o pedido `PENDENTE`, com código `PED-000001`. A venda trava o produto, baixa o cheio, recebe o vazio quando a categoria exige e soma o total no cliente. O entregador designado marca `ENTREGUE`. Gerente reabre ou cancela. O cancelamento estorna o depósito e exige motivo.

### Ler

Qualquer usuário ativo vê o painel: faturamento, fila e depósito. Administrador e gerente fecham o período: bruto, desconto, líquido, pagamento, entregador e produtos vendidos.

## O que o back-end ainda não faz

- Não serve o front. As telas React continuam locais até o cliente HTTP entrar.
- Não calcula rota, não imprime cupom e não envia WhatsApp. O cupom é responsabilidade da tela.
- Não agenda tarefa, não publica evento em tempo real e não tem fila.
