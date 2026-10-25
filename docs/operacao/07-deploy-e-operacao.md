# G-GÁS — Deploy e operação

O ambiente suportado hoje é uma máquina de desenvolvimento ou de balcão, com um processo `runserver` ou equivalente e o arquivo SQLite.

## Subir

```powershell
cd G_GAS_BACK
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py seed_inicial
python manage.py runserver
```

`migrate` aplica colaboradores, clientes, produtos, fornecedores, auditoria, estoque e pedidos. Relatórios não têm tabela.

## Configuração

| Variável | Papel | Padrão local |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Assinatura de sessão e JWT. Mínimo de 32 bytes | Chave só de desenvolvimento |
| `DJANGO_DEBUG` | Páginas de erro e detalhes | `True` |
| `ALLOWED_HOSTS` | Hosts aceitos, separados por vírgula | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Origem do front | portas 3000 e 5173 em localhost |

Não há variável de banco além do modo da transação. O arquivo é `db.sqlite3` na raiz do back-end. `OPTIONS.transaction_mode` está `IMMEDIATE` para uma escrita esperar a outra. Não troque para `DEFERRED`: o SQLite não honra `select_for_update`.

## Backup

Copie `db.sqlite3` com o processo parado, para não pegar escrita pela metade. O histórico do simple-history está no mesmo arquivo. Não há rotina agendada de backup.

## PostgreSQL

Quando dois processos precisarem gravar, ou a máquina deixar de ser a única, troque `DATABASES` para PostgreSQL e rode `migrate` numa base vazia. As migrations atuais servem. Não mantenha os dois bancos configurados ao mesmo tempo sem um plano de carga.

## O que esta operação não inclui

Não há Procfile, container, worker, beat nem volume de mídia. Avatar é URL, não arquivo enviado. Estático do Django só atende admin e Swagger.
