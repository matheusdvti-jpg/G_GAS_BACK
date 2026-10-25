# G-GÁS — Modelo de domínio e regras

Este documento é a referência de regra. Se o código divergir daqui, corrija o código ou atualize este arquivo no mesmo trabalho.

## Identidade

- Login aceita `username` ou e-mail no campo `username`.
- Conta inativa ou colaborador inativo não autentica e não passa em `UsuarioAtivoPermission`.
- O último administrador ativo não pode ser inativado nem perder o perfil de administrador.
- Senha fica só no hash do Django. Auditoria de conta pode dizer que a senha mudou. Não grava a senha.
- CPF tem 11 dígitos e dígitos verificadores. CNPJ tem 14.
- Telefone de cliente e de fornecedor tem 10 ou 11 dígitos. O telefone do colaborador exige ao menos 8 caracteres.

## Permissões

| Código | Perfis |
| --- | --- |
| `nova_venda`, `conceder_desconto` | Administrador, gerente, atendente |
| `cancelar_venda`, `reabrir_pedido` | Administrador, gerente |
| `confirmar_entrega` | Administrador, gerente, entregador |
| `entrada_estoque`, `saida_manual_estoque`, `conferencia_inventario` | Administrador, gerente, estoquista |
| `cadastrar_cliente` | Administrador, gerente, atendente |
| `gerir_produto`, `gerir_fornecedor`, `gestao_colaboradores`, `relatorios_financeiros` | Administrador, gerente |
| `auditoria_sistema` | Administrador |

O painel (`/relatorios/painel/`) é de qualquer usuário ativo. O fechamento por período exige `relatorios_financeiros`.

`gestao_cadastros` existe na matriz com o mesmo rótulo do painel (cadastros em geral) e não protege nenhuma rota. Cliente, produto e fornecedor usam os códigos específicos.

## Produto

- Categorias `GAS`, `AGUA` e `ACESSORIO`.
- O cadastro pode definir `saldo_cheio` e `saldo_seco` de abertura.
- Atualizar o produto recusa mudança desses dois campos: "O saldo do produto só muda por movimentação de estoque."
- Produto inativo não entra em venda.

## Estoque

Toda mudança operacional gera `MovimentacaoEstoque` com saldo anterior, quantidade (com sinal) e saldo novo. A identidade do lançamento é `saldo_anterior + quantidade = saldo_novo`.

| Ação | Saldo | Quantidade | Auditoria |
| --- | --- | --- | --- |
| Entrada de fornecedor | Cheio | Positiva. Custo unitário ≥ 0. Fornecedor ativo | `ESTOQUE` |
| Perda, avaria, consumo | Cheio | Negativa. Motivo com 4 caracteres ou mais | `ESTOQUE` |
| Empréstimo | Cheio | Negativa. Exige cliente. Sem motivo, o texto padrão é "Empréstimo para {nome}" | `ESTOQUE` |
| Conferência | Cheio | Diferença até a contagem, inclusive zero. Motivo com 4 caracteres ou mais | `ESTOQUE` |
| Venda | Cheio | Negativa | Não. O pedido audita |
| Troca na venda | Seco | Positiva, se houver vazio | Não |
| Estorno de cancelamento | Cheio | Positiva | Não |
| Devolução do vazio no cancelamento | Seco | Negativa, limitada ao seco disponível | Não |

Cheio insuficiente recusa a operação. Seco insuficiente no cancelamento desce até zero e ajusta a quantidade lançada para a identidade do saldo continuar válida.

## Pedido

- Nasce `PENDENTE`, com código `PED-000001` em diante. A sequência incrementa dentro da transação da view. No SQLite quem serializa essa transação é o modo `IMMEDIATE`, não o `select_for_update`.
- Endereço, nome do cliente, nome do entregador e nome do produto ficam copiados no pedido.
- O mesmo produto não se repete em duas linhas.
- Preço unitário é o `preco_venda` do produto no momento, com arredondamento half up.
- Desconto `NONE` zera. `VALUE` não passa do subtotal. `PERCENT` vai de 0 a 100 e vira reais. Desconto maior que zero exige `conceder_desconto`.
- Dinheiro: se `valor_recebido` vier vazio, assume o total. Se vier menor que o total, recusa. Troco é recebido menos total. Outras formas: `valor_recebido` nulo e troco zero.
- Entregador precisa existir, estar ativo e ter perfil `ENTREGADOR`.
- Gás: `vazios_recebidos` vira a quantidade vendida e o nome do vazio é "botijão seco", mesmo que o cliente informe outro número.
- Água: `vazios_recebidos` tem de ser igual à quantidade. O nome do vazio é "galão vazio".
- Acessório: vazio zero.
- A venda soma `total_pedidos` e `total_gasto` do cliente. O cancelamento não reverte esses totais.

### Status

| De | Para | Quem | Condição |
| --- | --- | --- | --- |
| o mesmo | o mesmo | quem chama | Nada muda |
| `PENDENTE` | `ENTREGUE` | quem tem `confirmar_entrega` | Entregador só se for o designado |
| `ENTREGUE` | `PENDENTE` | `reabrir_pedido` | Reabre para nova saída |
| qualquer um fora de cancelado | `CANCELADO` | `cancelar_venda` | Motivo com 3 caracteres ou mais |
| `CANCELADO` | outro | ninguém | Recusado |

Cancelar devolve o cheio e retira o seco. A leitura do status que autoriza o estorno acontece de novo dentro da transação. Se o pedido já foi cancelado por outra requisição, o segundo estorno não ocorre. Se o produto sumiu, o estorno daquele item é ignorado. O histórico de status guarda cada transição.

## Leituras

Datas são inclusivas no fuso `America/Sao_Paulo`, pelo `created_at` do pedido. Sem `de` e `ate`, o período é o histórico inteiro. Uma data só, ou data inicial depois da final, volta erro.

Pedido cancelado sai do faturamento, do ticket, da forma de pagamento e dos produtos vendidos. Continua na contagem de cancelados e na lista de pedidos.

- **Painel.** Faturamento é a soma de `total` dos não cancelados. Ticket médio só aparece quando existe ao menos um `ENTREGUE`; a divisão é faturamento dividido pela quantidade de não cancelados. Sem entrega concluída, o ticket é zero. `pedidos_entregues` conta todos os `ENTREGUE`. `pedidos_entregues_hoje` conta pedidos distintos que receberam status `ENTREGUE` hoje no histórico, mesmo que depois tenham sido reabertos. A fila lista os `PENDENTE` do mais antigo ao mais novo. Estoque de gás e de água soma o cheio dos produtos ativos. Alerta e posição do depósito também ignoram produto inativo. Alerta: cheio menor ou igual ao mínimo.
- **Período.** Bruto é a soma dos subtotais não cancelados. Desconto é a soma de `valor_desconto`. Líquido é a soma de `total`. Ticket do período é líquido dividido pelos não cancelados, inclusive quando ninguém foi entregue. Formas de pagamento saem sempre as quatro, na ordem Pix, dinheiro, débito e crédito, com percentual sobre o líquido. Entregadores listam todo colaborador com esse perfil, ativo ou não. Produtos mais vendidos ordenam pela quantidade.

A grade de pedidos do relatório não vem neste payload. Ela é `GET /pedidos/listar/` com `de` e `ate`.

## Auditoria

Tipos: `CLIENTE`, `PRODUTO`, `FORNECEDOR`, `COLABORADOR`, `CONTA`, `ESTOQUE`, `PEDIDO`.

A consulta é do administrador. O seed inicial não grava auditoria porque não há usuário autor.
