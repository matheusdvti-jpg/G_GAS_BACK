# G-GÁS — Bounded contexts

Cada pasta na raiz de `G_GAS_BACK` é um contexto. A app Django mora um nível abaixo (`Estoque/estoque`, `Pedidos/pedidos`) para o pacote Python não colidir com o nome do model.

`AppCore` não é domínio. É o framework interno.

## Mapa

| Contexto | Responsabilidade | Depende de |
| --- | --- | --- |
| Auth | Emitir e renovar JWT, responder quem está logado | Colaboradores |
| Colaboradores | Pessoa, conta, perfil e a matriz `usuario_pode` | AppCore |
| Clientes | Cadastro e busca do comprador, totais acumulados | AppCore, Auditoria |
| Catalogo | Produto e fornecedor, sem chave entre eles | AppCore, Auditoria |
| Estoque | Movimentação e saldo | Catalogo, Clientes, Colaboradores, Auditoria |
| Pedidos | Venda, itens, status e sequência | Clientes, Catalogo, Colaboradores, Estoque, Auditoria |
| Relatorios | Leitura agregada. Não grava model próprio | Pedidos, Catalogo, Colaboradores |
| Auditoria | Trilha append-only de ações | Colaboradores |

## Fronteiras que devem permanecer

- Cliente, produto e fornecedor nascem e mudam sem importar um ao outro. O fornecedor lista produtos pelo nome.
- Estoque aponta o pedido por `pedido_id` inteiro e `codigo_pedido` texto. Não há `ForeignKey` para `Pedido`. Quem chama o estoque na venda é o business de Pedidos.
- Relatórios só leem. Não criam movimentação, não mudam status e não auditam a consulta. A agregação mora em `LeituraHelpers`.
- Auditoria guarda `entidade_id` como texto e `tipo_entidade`. Não aponta chave estrangeira para o registro auditado, então o log sobrevive se a modelagem de um cadastro mudar.

## O que um contexto novo precisa ter

`apps.py`, `models.py` quando houver tabela, `business.py`, `rules.py`, `helpers.py`, `serializers.py`, `views.py`, `urls.py`, admin quando houver model, e teste. A rota entra em `ggas/urls.py` e a app em `INSTALLED_APPS`.

Relatórios é o caso sem tabela: business, rules, helpers, views e urls bastam.
