# G-GÁS — Arquitetura da solução

## Forma

Monólito modular em camadas. Um processo Django atende HTTP. Cada contexto é um pacote. O estado mora no banco.

Não há serviço separado de leitura, fila nem gateway. Relatórios são views no mesmo processo, agregando as tabelas de pedido, item, produto e colaborador.

## Stack

| Peça | Uso |
| --- | --- |
| Python 3.12 | Runtime |
| Django 5.2 | Projeto, ORM, admin |
| Django REST Framework 3.16 | HTTP |
| Simple JWT 5.5 | Access e refresh |
| django-filter 25.1 | Filtros de listagem |
| drf-spectacular 0.29 | OpenAPI, Swagger e Redoc |
| django-simple-history 3.11 | Histórico de model |
| django-cors-headers 4.9 | Front local nas portas 3000 e 5173 |
| python-dotenv | Variáveis de ambiente |
| SQLite | Banco do arquivo `db.sqlite3` |

Fora de propósito neste momento: Celery, Redis, Django Channels, Daphne e PostgreSQL.

## Camadas de um contexto

```
view  →  business  →  rules
                 →  helpers
                 →  models de outro contexto, quando a fronteira permite
```

A view traduz status HTTP e o envelope. O business monta a operação. O rules decide se ela pode ocorrer. O helpers consulta e formata.

`BasicPostAPIView` e `BasicUpdateAPIView` envolvem `do_action_*` em `transaction.atomic()`. A venda, a baixa e o estorno correm nessa transação. No SQLite a fila entre escritas é o `transaction_mode=IMMEDIATE`. O `select_for_update` não trava a linha nesse banco e permanece para o PostgreSQL.

## Projeto `ggas`

- `settings.py` liga as apps e o SQLite.
- `urls.py` publica os contextos.
- `rest_framework_settings.py` configura DRF, JWT e paginação.
- `spectacular_settings.py` nomeia os enums para o schema não colidir.
- `views.py` responde `GET /api/health/`.

## Front

O painel React é a referência de regra e de rótulo. Ele ainda não chama esta API. Quando chamar, as views permanecem; só os repositórios de `localStorage` saem.

CORS libera `localhost` e `127.0.0.1` nas portas 3000 e 5173. O README do front cita a porta 3000. O Vite pode subir na 5173.

## Riscos conhecidos

- SQLite serializa escrita. Serve a uma operação e a um processo. Vários workers de escrita pedem PostgreSQL.
- `select_for_update` no SQLite não emite `FOR UPDATE`. Sem `transaction_mode=IMMEDIATE`, duas vendas do último botijão, ou dois cancelamentos do mesmo pedido, leem o estado antigo e a segunda escrita repete a baixa ou o estorno. O modo imediato faz a transação de escrita esperar a anterior. A trava de linha fica para o PostgreSQL.
- O histórico do simple-history cresce em toda alteração de model que herda `BasicModel`.
- Relatórios varrem pedidos do período no processo da requisição. O volume atual de uma distribuidora cabe. Um recorte muito longo não tem cache.
