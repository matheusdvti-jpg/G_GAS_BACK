# G-GÁS — AppCore

Framework interno em `AppCore/`. Todo contexto novo usa estas peças. O desenho acompanha o Hoopi no que o G-GÁS precisa: views base, exceções, permissão e model. Não há utilitário de tempo real nem task.

## Camadas

| Arquivo | Papel |
| --- | --- |
| `business.py` | Orquestra a operação |
| `rules.py` | Valida e lança erro de negócio ou de autorização |
| `helpers.py` | Consulta e monta estrutura |

No model:

```python
class Pedido(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    helper_class = PedidoHelpers
    business_class = PedidoBusiness
    rules_class = PedidoRules
```

Com instância: `pedido.business` e `pedido.rules`. Sem instância, na criação: `PedidoBusiness().criar(...)`.

Leitura sem model, como relatórios, instancia `LeituraBusiness`, que ainda herda `ModelInstanceBusiness` e guarda `helpers` e `rules` próprios.

Função auxiliar fica como método da classe. Não deixe `def` solta no módulo para um fluxo só.

O model aponta `business_class`, `rules_class` e `helper_class` no corpo da classe. Nesse app, `business.py`, `rules.py` e `helpers.py` importam o próprio model **dentro do método**: o import no topo fecha um ciclo. Relatórios não tem model e pode importar os models que lê no topo do helper.

A busca, o `select_related` da listagem e o `select_for_update` ficam no helper. `QuerySet.get` da trava ainda lança `DoesNotExist`. `PedidoHelpers.bloquear_cliente` e `MovimentacaoHelpers.bloquear_produto` traduzem isso em `NotFoundException`. A busca por `objects.get` do manager já nasce como `NotFoundException`. No pedido, `exigir` troca essa ausência por regra de negócio (`400`). No estoque, `obter` mantém `404` e só troca a mensagem.

O serializer só descreve o corpo HTTP e a presença dos campos. Regra de negócio, data de período e busca de login não ficam nele. A view de período repassa `de` e `ate` como texto. `LeituraRules` interpreta o formato e recusa o intervalo. O login JWT precisa do `validate` do SimpleJWT: ele chama `UserHelpers.buscar_por_identificador` e `usuario.rules.pode_autenticar`.

## Views

| Classe | Uso |
| --- | --- |
| `BasicPostAPIView` | Cria. `do_action_post` corre dentro de `atomic` |
| `BasicUpdateAPIView` | Atualiza. `do_action_patch` corre dentro de `atomic` |
| `BasicListAPIView` | Lista com filtro, ordem e paginação |
| `BasicGetAPIView` | Detalhe. `Http404` vira `NotFoundException` |

Consulta que não é CRUD de model, como saúde e relatórios, usa `APIView` com `@handle_exceptions` e devolve o mesmo envelope.

Não envolva outro `atomic()` no business chamado por post ou update.

`get_object` roda antes do `atomic`. Status de pedido, saldo e a checagem do último administrador releem a linha dentro do `do_action`. A mudança de status trava o pedido de novo. A atualização de produto e de colaborador também. O `save` grava só os campos enviados, para um saldo baixado pela venda não voltar com o valor antigo que a view carregou.

No SQLite, `select_for_update` não gera `FOR UPDATE`. A espera entre escritas vem de `OPTIONS.transaction_mode = IMMEDIATE` em `DATABASES`: a transação da view pega o banco antes de ler. O `select_for_update` permanece para quando o banco for PostgreSQL.

## Envelope

Sucesso:

```json
{"status": "success", "message": "...", "data": {}}
```

Lista também traz `count`, `next` e `previous`.

Erro:

| Exceção | HTTP |
| --- | --- |
| `BusinessRuleException`, `ValidationException` | 400 `detail` |
| `AuthorizationException` | 403 |
| `NotFoundException` | 404 |
| Qualquer outra | 500 genérico, com log |

O token JWT é a exceção: devolve `access`, `refresh` e `usuario` sem esse envelope.

## Permissão

| Mixin | Quem passa |
| --- | --- |
| `AllowAnyMixin` | Público. Usado na saúde e no token |
| `AutenticadoMixin` | Usuário ativo com colaborador ativo |
| `PermissaoMixin` | O anterior, mais `usuario_pode(usuario, view.permissao)` |

A view declara `permissao = 'nova_venda'`. Não declare `permission_classes`.

Quando uma rota serve mais de uma decisão, como a troca de status do pedido, a view fica autenticada e o `rules` escolhe o código (`confirmar_entrega`, `reabrir_pedido` ou `cancelar_venda`).

## Histórico e manager

`BasicModel.history` grava revisão e exclui `password`. `objects.get` ausente levanta `NotFoundException` com o nome do model. Trava com `select_for_update().get` precisa capturar `DoesNotExist` do model.
