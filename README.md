# G-GÁS — Back-end

API do painel da distribuidora de gás e água mineral. Monólito modular no mesmo desenho do Hoopi: pacotes de domínio, `AppCore` compartilhado e, em cada app, `models`, `business`, `rules`, `helpers`, `serializers` e `views`.

O banco inicial é **SQLite** (`db.sqlite3` na raiz deste projeto).

## O que já responde

- Saúde da API e do SQLite: `GET /api/health/`
- Login por usuário ou e-mail, renovação e verificação de JWT
- Sessão do usuário autenticado: `GET /auth/eu/`
- Cadastro, busca e atualização de clientes
- Catálogo de produtos e cadastro de fornecedores, independentes entre si
- Estoque: entrada, saída manual, empréstimo, conferência e histórico
- Pedidos: venda com baixa e troca de vazio, despacho e cancelamento com estorno
- Leituras: painel operacional e fechamento financeiro por período
- Auditoria das criações e alterações, visível para o administrador
- Matriz de permissão por perfil
- Administrador inicial: `python manage.py seed_inicial`

Documentação interativa: `http://127.0.0.1:8000/api/schema/swagger/`

## Rodar localmente

Na pasta `G_GAS_BACK`, com Python 3.12:

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_inicial
python manage.py runserver
```

O seed cria o usuário `admin` com a senha `Ggas@123` e o e-mail `admin@ggas.com.br`. Essa senha vale só para o SQLite local.

Login:

```http
POST /auth/token_jwt/
{"username": "admin", "password": "Ggas@123"}
```

O corpo também aceita o e-mail no campo `username`. A resposta traz `access`, `refresh` e `usuario` (nome, perfil e colaborador).

## Arquitetura

```
ggas/                  projeto Django, settings e rotas
AppCore/               views base, exceções, envelope JSON, permissões
Auth/                  JWT
Colaboradores/         pessoa, conta e perfil
Clientes/              cadastro e busca do cliente
Catalogo/              produtos e fornecedores, sem vínculo obrigatório
Estoque/               saldo cheio, saldo seco e movimentação
Pedidos/               venda, despacho e cancelamento com estorno
Relatorios/            painel operacional e fechamento por período
Auditoria/             trilha de quem executou cada ação
```

Uma view recebe o HTTP e delega. O `business` orquestra, o `rules` aceita ou lança erro de negócio, o `helpers` consulta e monta resumo. O model herda `BasicModel` (`created_at`, `updated_at` e histórico).

Respostas de negócio usam o envelope `status`, `message` e `data`. Erro de regra volta `400` com `detail`.

### Rotas de colaborador

| Método | Rota | Quem acessa |
| --- | --- | --- |
| POST | `/colaboradores/` | Administrador e gerente |
| GET | `/colaboradores/listar/` | Qualquer usuário ativo |
| GET | `/colaboradores/<id>/` | Qualquer usuário ativo |
| PATCH | `/colaboradores/<id>/atualizar/` | Administrador e gerente |
| POST | `/colaboradores/<id>/conta/` | Administrador e gerente |
| PATCH | `/colaboradores/<id>/conta/atualizar/` | Administrador e gerente |

Filtros da listagem: `perfil`, `ativo`, `nome__icontains`, `ordering`.

Perfis: `ADMINISTRADOR`, `GERENTE`, `ATENDENTE`, `ESTOQUISTA`, `ENTREGADOR`. A matriz está em `Colaboradores/colaboradores/permissoes.py`.

### Rotas de cliente, catálogo e auditoria

| Método | Rota | Quem grava | Quem consulta |
| --- | --- | --- | --- |
| POST / PATCH | `/clientes/` e `/clientes/<id>/atualizar/` | Administrador, gerente e atendente | Qualquer usuário ativo |
| POST / PATCH | `/produtos/` e `/produtos/<id>/atualizar/` | Administrador e gerente | Qualquer usuário ativo |
| POST / PATCH | `/fornecedores/` e `/fornecedores/<id>/atualizar/` | Administrador e gerente | Qualquer usuário ativo |
| GET | `/auditoria/listar/` e `/auditoria/<id>/` | O próprio cadastro grava o log | Administrador |

A busca usa `q`. Em clientes, vale nome ou telefone. Em produtos, nome, marca ou código. Em fornecedores, fantasia, razão social ou CNPJ. O fornecedor guarda os produtos que atende como nomes, sem chave para o catálogo.

### Rotas de estoque e pedidos

| Método | Rota | Quem grava |
| --- | --- | --- |
| POST | `/estoque/entradas/` | Administrador, gerente e estoquista |
| POST | `/estoque/saidas/` | Administrador, gerente e estoquista |
| POST | `/estoque/conferencias/` | Administrador, gerente e estoquista |
| GET | `/estoque/movimentacoes/` | Qualquer usuário ativo |
| POST | `/pedidos/` | Administrador, gerente e atendente |
| GET | `/pedidos/listar/` e `/pedidos/<id>/` | Qualquer usuário ativo |
| PATCH | `/pedidos/<id>/status/` | Depende do destino: entrega, reabertura ou cancelamento |

O entregador confirma só a entrega atribuída a ele. Reabrir um pedido entregue fica com administrador e gerente. Cancelar exige motivo e também fica com administrador e gerente. A consulta de pedidos é de qualquer usuário ativo, com filtro `status`, `cliente`, `entregador`, `q`, `de` e `ate`.

### Rotas de leitura

| Método | Rota | Quem consulta |
| --- | --- | --- |
| GET | `/relatorios/painel/` | Qualquer usuário ativo |
| GET | `/relatorios/periodo/?de=AAAA-MM-DD&ate=AAAA-MM-DD` | Administrador e gerente |

O painel reúne faturamento, ticket, fila de despacho e posição do depósito. O período reúne bruto, desconto, líquido, forma de pagamento, entregador e produtos vendidos. Sem `de` e `ate`, o período considera todo o histórico. A tabela de pedidos do relatório continua em `GET /pedidos/listar/`, com as mesmas datas.

A documentação de domínio, arquitetura, operação e as diretrizes para agentes estão em [docs/README.md](docs/README.md).

## Próximos passos

1. **Front.** Trocar os repositórios de `localStorage` por cliente HTTP, mantendo as views React. O contrato está em [docs/desenvolvimento/13-integracao-front.md](docs/desenvolvimento/13-integracao-front.md). O painel e os relatórios passam a ler `/relatorios/painel/` e `/relatorios/periodo/`.
2. **Banco.** Quando a operação sair de uma máquina só, apontar o Django para PostgreSQL. Até lá, o SQLite permanece.

O saldo do produto já não muda pelo cadastro. Entrada, saída, conferência, venda e cancelamento passam pela movimentação. O total de pedidos do cliente permanece depois do cancelamento, como no painel.
