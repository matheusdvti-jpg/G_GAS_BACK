# G-GÁS — Segurança

Controles que o código já aplica, e o que precisa mudar antes de sair da máquina local.

## O que já vale

- Senha com hash do Django. Não aparece em auditoria nem no histórico do model.
- JWT de access e refresh. O login recusa usuário inativo e colaborador inativo.
- Cada rota de escrita declara um código de permissão, conferido pelo perfil. A troca de status do pedido é a exceção: a view fica autenticada e a regra escolhe `confirmar_entrega`, `reabrir_pedido` ou `cancelar_venda`. Administrador e superusuário passam em qualquer código.
- Entregador não confirma pedido de outro entregador, mesmo tendo `confirmar_entrega`.
- Cancelamento e reabertura não estão no atendente nem no estoquista.
- Fechamento financeiro não está no atendente, no estoquista nem no entregador.
- Auditoria só é lida pelo administrador.
- CORS restringe a origem. CSRF permanece no middleware para o admin.
- Cliente, produto e fornecedor usam `PROTECT` onde a operação já os citou, então um cadastro usado não some e leva o histórico junto.

## Antes de um ambiente compartilhado

- Trocar `DJANGO_SECRET_KEY` e desligar `DJANGO_DEBUG`.
- Trocar a senha do `admin` criada pelo seed. `Ggas@123` é só local.
- Servir por HTTPS e definir `ALLOWED_HOSTS` com o domínio real.
- Restringir o admin do Django a quem é `is_staff`. O seed marca o administrador inicial como staff e superusuário.
- Não versionar `.env` nem `db.sqlite3`. Os dois estão fora do git pelo `.gitignore`.

## Limites conscientes

- Não há revogação de access antes do vencimento. O refresh gira o access.
- Não há trava de tentativas de login.
- O painel operacional é visível a qualquer colaborador ativo, inclusive faturamento acumulado. O fechamento por forma de pagamento não é.
- SQLite no disco da máquina é o dado da distribuidora. Quem copia o arquivo leva o banco.
