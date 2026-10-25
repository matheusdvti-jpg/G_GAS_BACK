# G-GÁS — Integração do painel com a API

O painel em `G_GAS_FRONT` ainda grava em `localStorage`. Esta página diz o que muda na hora de ligá-lo à API e o que permanece no back-end.

A regra de negócio continua em [fundamentos/05-modelo-de-dominio-e-regras.md](../fundamentos/05-modelo-de-dominio-e-regras.md). As rotas continuam em [12-catalogo-de-api.md](12-catalogo-de-api.md). Documento antigo do front, inclusive status de kanban, não redefine a API.

## Diretriz

O cliente HTTP traduz. A view React permanece. O back-end não ganha campo, status, permissão nem página padrão para imitar o `localStorage`.

| Fica no back-end | Fica no cliente do front |
| --- | --- |
| Nome de campo em português | Entidade em inglês (`Product`, `Order`) |
| `Decimal` como texto com duas casas (`230.00`) | Conversão para número na exibição e soma em centavos |
| Lista com `limit` e `offset`, página padrão 20 | `pageSize` visual (4, 6 ou 8) e o loop em `next` |
| `403` de perfil | Esconder o botão de quem não tem o código |
| Saldo só por movimentação depois do cadastro | Edição de produto sem reenviar cheio e seco |
| `PENDENTE`, `ENTREGUE`, `CANCELADO` | Ignorar `NOVO`, `EM_SEPARACAO`, `PRONTO_ENTREGA`, `SAIU_ENTREGA` |
| Login por token | Sem `switchUser` |

## Onde implementar

Troque os repositórios de `G_GAS_FRONT/src/infrastructure/repositories`. Casos de uso e views continuam chamando o mesmo repositório de domínio.

- Base: `http://127.0.0.1:8000`. O CORS local já aceita as portas 3000 e 5173.
- Rotas privadas: `Authorization: Bearer <access>`.
- Sucesso de negócio: `status`, `message`, `data`. Lista também traz `count`, `next` e `previous`.
- Erro de negócio: `status` `error` e `detail`. `400` é regra, `403` é perfil, `404` é ausência, `401` é sessão.
- `POST /auth/token_jwt/` não usa envelope. O corpo de sucesso traz `access`, `refresh` e `usuario`. Renove com `POST /auth/token_jwt/refresh/`. A sessão corrente é `GET /auth/eu/`.
- `id` da API é inteiro. A entidade do front guarda string. A conversão acontece na borda do cliente.

## Ajustes do painel

### Sessão

Grave `access` e `refresh`. Monte o usuário logado com `usuario` do token e com `/auth/eu/`. A tela de equipe deixa de trocar o usuário no clique: cada pessoa entra com a própria conta. Não crie rota de troca de usuário.

### Dinheiro

Some em centavos inteiros e formate na hora de mostrar. `"230.00" + 0` vira texto e quebra o `toFixed`. Campos de pedido, produto e cliente vêm como texto. O painel e o período já vêm formatados (`faturamento_total`, `ticket_medio`, `percentual`); exiba esse texto.

### Data

`created_at` sai no fuso `America/Sao_Paulo`, com offset. O dia de calendário é o prefixo `AAAA-MM-DD` desse valor. Filtro `de` e `ate` usa esse dia. `toISOString()` é UTC e desloca o pedido da noite para o dia seguinte.

### Listas

A página padrão tem 20 linhas. O `pageSize` da tela só fatia o que o cliente já recebeu.

- Cadastro pequeno (cliente, produto, fornecedor, colaborador): siga `next` até esgotar, ou mande o filtro que a rota já tem (`q`, `categoria`, `ativo`, `perfil`).
- Pedido e movimentação: mande o filtro da tela (`status`, `cliente`, `de`, `ate`, `produto`, `tipo`) e use `limit` e `offset` do tamanho visual.
- Números do início e do relatório vêm de `/relatorios/painel/` e `/relatorios/periodo/`. Não some a página de pedidos para refazer esse fechamento.

Não remova `PAGE_SIZE` nem devolva a tabela inteira por omissão de `limit`.

### Produto

`POST /produtos/` pode gravar `saldo_cheio` e `saldo_seco` de abertura. No `PATCH`, omita os dois. Se o valor enviado divergir do saldo atual, a API responde `400` e o nome e o preço também não salvam. Na edição, cheio e seco ficam somente leitura. Entrada, saída, conferência, venda e cancelamento continuam na tela de estoque.

### Pedido

Corpo da venda: `cliente_id`, `entregador_id`, `itens` (`produto_id`, `quantidade`, `vazios_recebidos`), `forma_pagamento`, `valor_recebido`, `tipo_desconto`, `valor_desconto`, `observacoes`.

Gás manda o vazio igual à quantidade. Água exige a mesma quantidade de galão vazio. Acessório manda zero. Cancelar exige `observacao` com ao menos 3 caracteres. O mesmo status de novo é inócuo. Cancelado não volta.

O rótulo "Entregues hoje" do painel atual conta todo `ENTREGUE` ainda nesse status. Na API, esse número é `pedidos_entregues`. `pedidos_entregues_hoje` conta quem recebeu `ENTREGUE` no histórico de hoje, mesmo reaberto depois. Use o campo que o rótulo da tela nomeia.

### Entregador

`POST /colaboradores/` aceita a pessoa sem `conta`. Ela já pode ser `entregador_id`. Para entrar no sistema, `POST /colaboradores/<id>/conta/` com `username`, `email` e `password`. A tela que não pede senha cria a pessoa e deixa a conta para um segundo passo. Não invente login sem senha.

### Perfil

Esconda confirmar, cancelar, reabrir, estoque e fechamento de quem não tem o código. A matriz está em [05-modelo-de-dominio-e-regras.md](../fundamentos/05-modelo-de-dominio-e-regras.md). O `403` permanece.

### Telefone e documento

Cliente e fornecedor: a API reduz a máscara para 10 ou 11 dígitos. Colaborador: o telefone fica como texto, com pelo menos 8 caracteres. CPF e CNPJ precisam dos dígitos verificadores.

## Mapa de campos

Leitura. O cliente monta a entidade do front a partir destas chaves.

| Front | API |
| --- | --- |
| `Customer.name`, `phone`, `secondaryPhone` | `nome`, `telefone`, `telefone_secundario` |
| `street`, `number`, `complement`, `neighborhood`, `city`, `referencePoint`, `notes` | `logradouro`, `numero`, `complemento`, `bairro`, `cidade`, `ponto_referencia`, `observacoes` |
| `totalOrdersCount`, `totalSpent` | `total_pedidos`, `total_gasto` |
| `Product.code`, `name`, `brand`, `salePrice`, `costPrice` | `codigo`, `nome`, `marca`, `preco_venda`, `preco_custo` |
| `currentStock`, `emptyStock`, `minimumStock` | `saldo_cheio`, `saldo_seco`, `estoque_minimo` |
| `Supplier.tradeName`, `corporateName`, `suppliedProducts` | `nome_fantasia`, `razao_social`, `produtos_fornecidos` |
| `Collaborator.role`, `vehiclePlate` | `perfil`, `placa_veiculo` |
| `User.username`, `email`, `collaboratorId` | `conta.username`, `conta.email`, `conta.colaborador_id` |
| `Order.code`, `subtotal`, `discountAmount`, `total`, `changeDue` | `codigo`, `subtotal`, `valor_desconto`, `total`, `troco` |
| `discountType`, `paymentMethod`, `amountReceived`, `notes` | `tipo_desconto`, `forma_pagamento`, `valor_recebido`, `observacoes` |
| `customerName`, `deliveryPersonName`, `createdByUserName` | `nome_cliente`, `nome_entregador`, `nome_criado_por` |
| `deliveryAddress.*` | `logradouro`, `numero`, `complemento`, `bairro`, `cidade`, `ponto_referencia` |
| `items[].unitPrice`, `emptiesReturned`, `emptyContainerName` | `preco_unitario`, `vazios_recebidos`, `nome_vazio` |
| `statusHistory[].userName`, `note`, `timestamp` | `nome_usuario`, `observacao`, `created_at` |
| `StockMovement.balanceKind`, `previousStock`, `newStock` | `tipo_saldo`, `saldo_anterior`, `saldo_novo` |
| `orderId`, `orderCode`, `performedByUserName` | `pedido_id`, `codigo_pedido`, `nome_usuario` |

`tipo_saldo` é `CHEIO` ou `SECO`. `produtos_fornecidos` é lista de nomes, sem id de produto.

## O que não mudar na API para encaixar a tela

- Não aceite `saldo_cheio` ou `saldo_seco` diferentes no `PATCH` do produto.
- Não serialice dinheiro como número JSON.
- Não tire a paginação padrão de 20.
- Não crie `switchUser`, status de kanban, cupom ou rota de impressão. O cupom usa o `GET` do pedido.
- Não alargue permissão de atendente, estoquista ou entregador.
- Não estorne `total_pedidos` nem `total_gasto` no cancelamento.

## Conferir no navegador

Com a API em `127.0.0.1:8000` e o painel em `localhost:3000`, no usuário `admin` / `Ggas@123`:

1. Login, sessão em `/auth/eu/` e renovação do access.
2. Venda de gás com vazio, dinheiro e troco. O cheio baixa e o seco sobe.
3. Edição de produto que muda o preço e não manda saldo. O saldo da venda permanece.
4. Cancelamento com motivo. O segundo cancelamento não estorna de novo.
5. Painel e período com o dia de São Paulo, inclusive pedido feito depois das 21h.
6. Atendente vê `403` ao confirmar, cancelar e lançar estoque, e a tela não oferece essas ações.
