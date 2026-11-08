# G-GÁS — Segurança

Controles que o código já aplica, e o que precisa mudar antes de sair da máquina local.

## O que já vale

- Senha com hash do Django. Não aparece em auditoria nem no histórico do model.
- Sessão opaca no cookie `ggas_sessao`, HttpOnly e `SameSite=Lax`. O login recusa usuário inativo e colaborador inativo.
- `POST`, `PATCH` e `DELETE` exigem o cabeçalho `X-CSRFToken`. O cookie `csrftoken` sai de `GET /auth/csrf/` e não é HttpOnly, para o painel ler o valor. As origens de `CORS_ALLOWED_ORIGINS` também valem como origem confiável do CSRF.
- A sessão dura no máximo 8 horas. Ficar sem usar o painel não encerra a sessão antes disso.
- Troca de senha e desativação da conta revogam as sessões daquele usuário. O logout revoga a sessão do cookie na hora.
- Cinco falhas de login na mesma chave de IP e identificador bloqueiam por 15 minutos. A contagem trava a linha, então tentativas paralelas não passam de cinco. Login aceito, recusado, bloqueio e senha alterada entram na auditoria com usuário e IP. Senha, hash e cookie ficam de fora. Senha nova tem no mínimo 12 caracteres; o hash que já existe continua até a troca.
- O IP do cliente vem de uma função só. Com o debug ligado, ela usa `REMOTE_ADDR` e ignora `X-Forwarded-For`. Publicado, lê o último endereço de `X-Forwarded-For`, o salto que o proxy da plataforma acrescenta.
- Cada rota de escrita declara um código de permissão, conferido pelo perfil. A leitura de cliente, produto, fornecedor, movimentação e pedido também. A leitura de pedido usa `PedidoLeituraMixin`: entregador vê só a própria entrega e o pedido de outro responde 404. A troca de status continua na regra, que escolhe `confirmar_entrega`, `reabrir_pedido` ou `cancelar_venda`. Administrador e superusuário passam em qualquer código.
- Custo, CPF e conta do colaborador saem do JSON quando o perfil não pode vê-los. Estoquista não lista cliente nem pedido. Entregador não lista cliente nem produto.
- O gerente não cria nem altera administrador ou gerente. A senha dessas contas também fica com o administrador.
- Entregador não confirma pedido de outro entregador, mesmo tendo `confirmar_entrega`.
- Cancelamento e reabertura não estão no atendente nem no estoquista.
- Fechamento financeiro não está no atendente, no estoquista nem no entregador.
- Auditoria, schema, Swagger e Redoc só são lidos pelo administrador. `GET /api/health/` continua público.
- Com `DJANGO_DEBUG` desligado, o processo recusa a `SECRET_KEY` de desenvolvimento e a `DJANGO_DB_KEY` vazia ou igual à do `.env.example`. O seed do administrador `GgasLocal@2026` só roda com o debug ligado e não escreve a senha quando o debug está desligado. Uma base que já tinha o `admin` criado com `Ggas@123` continua nessa senha até alguém trocá-la.
- Fora do debug, a API redireciona para HTTPS quando o proxy envia `X-Forwarded-Proto: https`, e responde HSTS por um ano. O painel publica `Content-Security-Policy`: script só do próprio host e página fora de frame.
- CORS restringe a origem. O middleware de CSRF permanece para o admin, e a API confere o token nas mutações.
- Cliente, produto e fornecedor usam `PROTECT` onde a operação já os citou, então um cadastro usado não some e leva o histórico junto.

## Antes de um ambiente compartilhado

- Gerar `DJANGO_SECRET_KEY` e `DJANGO_DB_KEY` novas antes de desligar `DJANGO_DEBUG`. O processo recusa o exemplo, mas a chave nova precisa existir no ambiente.
- Trocar a senha do `admin` se o seed já rodou nessa base. `Ggas@123` e `GgasLocal@2026` são só locais.
- Definir `ALLOWED_HOSTS` com o domínio real. O redirecionamento HTTPS e o HSTS já ligam com o debug desligado.
- Restringir o admin do Django a quem é `is_staff`. O seed marca o administrador inicial como staff e superusuário.
- Não versionar `.env` nem `db.sqlite3`. Os dois estão fora do git pelo `.gitignore`.
- Incluir a origem real do painel em `CORS_ALLOWED_ORIGINS`. O CSRF usa essa lista. Sem ela o navegador recusa a mutação.

## Limites conscientes

- No ambiente publicado, o último salto de `X-Forwarded-For` pode ser o proxy da plataforma, não o navegador. Se a hospedagem escrever outro cabeçalho, a função do IP é o único lugar para trocar.
- O painel operacional é visível a qualquer colaborador ativo, com fila e depósito. Faturamento acumulado e ticket médio só saem para administrador e gerente. O fechamento por forma de pagamento também.
- SQLite no disco da máquina é o dado da distribuidora. Quem copia o arquivo leva o banco.
