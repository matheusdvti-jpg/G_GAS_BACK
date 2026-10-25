# G-GÁS — Guia da Documentação

## Objetivo

Esta pasta é o ponto de entrada do back-end da distribuidora. Ela descreve o domínio, as regras que o código aplica, a arquitetura em camadas, como desenvolver e como operar o ambiente local.

O painel React em `G_GAS_FRONT` ainda grava em `localStorage`. O contrato que vale para o back-end é o comportamento das views e dos casos de uso desse front. Quando um documento antigo do front divergir do código montado, prevalece o código montado e, no back-end, o que está em `docs/` e em `G_GAS_BACK`.

**Agentes de IA:** leia primeiro [AGENTS.md](AGENTS.md).

## Estrutura

### Fundamentos

- [fundamentos/01-visao-geral-do-sistema.md](fundamentos/01-visao-geral-do-sistema.md): o que o G-GÁS faz, quem usa e quais fluxos já existem.
- [fundamentos/02-linguagem-ubiqua.md](fundamentos/02-linguagem-ubiqua.md): vocabulário do balcão, do depósito e da entrega.
- [fundamentos/03-bounded-contexts.md](fundamentos/03-bounded-contexts.md): pacotes, fronteiras e o que cada um pode importar.
- [fundamentos/05-modelo-de-dominio-e-regras.md](fundamentos/05-modelo-de-dominio-e-regras.md): entidades, permissões e regras de negócio.

### Arquitetura

- [arquitetura/04-arquitetura-da-solucao.md](arquitetura/04-arquitetura-da-solucao.md): monólito modular, stack e o que ficou de fora de propósito.
- [arquitetura/06-arquitetura-de-dados.md](arquitetura/06-arquitetura-de-dados.md): models, vínculos, concorrência e histórico.
- [arquitetura/10-appcore-framework.md](arquitetura/10-appcore-framework.md): views base, envelope, exceções e permissões.

### Desenvolvimento

- [desenvolvimento/00-setup-local.md](desenvolvimento/00-setup-local.md): ambiente, migrate, seed e servidor.
- [desenvolvimento/11-testes.md](desenvolvimento/11-testes.md): onde estão os testes e o que eles cobrem.
- [desenvolvimento/12-catalogo-de-api.md](desenvolvimento/12-catalogo-de-api.md): rotas HTTP atuais.
- [desenvolvimento/13-integracao-front.md](desenvolvimento/13-integracao-front.md): como ligar o painel sem afrouxar a API.

### Operação

- [operacao/07-deploy-e-operacao.md](operacao/07-deploy-e-operacao.md): SQLite local, variáveis e o caminho até PostgreSQL.
- [operacao/08-seguranca.md](operacao/08-seguranca.md): autenticação, perfis e cuidados antes de sair da máquina local.
- [operacao/09-observabilidade.md](operacao/09-observabilidade.md): saúde da API, logs e o que ainda não há.

## Leitura por objetivo

### Entender o negócio

1. [fundamentos/01-visao-geral-do-sistema.md](fundamentos/01-visao-geral-do-sistema.md)
2. [fundamentos/02-linguagem-ubiqua.md](fundamentos/02-linguagem-ubiqua.md)
3. [fundamentos/05-modelo-de-dominio-e-regras.md](fundamentos/05-modelo-de-dominio-e-regras.md)

### Desenvolver no back-end

1. [AGENTS.md](AGENTS.md)
2. [desenvolvimento/00-setup-local.md](desenvolvimento/00-setup-local.md)
3. [arquitetura/10-appcore-framework.md](arquitetura/10-appcore-framework.md)
4. [desenvolvimento/12-catalogo-de-api.md](desenvolvimento/12-catalogo-de-api.md)
5. [fundamentos/05-modelo-de-dominio-e-regras.md](fundamentos/05-modelo-de-dominio-e-regras.md)
6. [arquitetura/06-arquitetura-de-dados.md](arquitetura/06-arquitetura-de-dados.md)
7. [desenvolvimento/11-testes.md](desenvolvimento/11-testes.md)

### Ligar o painel

1. [desenvolvimento/13-integracao-front.md](desenvolvimento/13-integracao-front.md)
2. [desenvolvimento/12-catalogo-de-api.md](desenvolvimento/12-catalogo-de-api.md)
3. [fundamentos/05-modelo-de-dominio-e-regras.md](fundamentos/05-modelo-de-dominio-e-regras.md)

### Operar

1. [operacao/07-deploy-e-operacao.md](operacao/07-deploy-e-operacao.md)
2. [operacao/08-seguranca.md](operacao/08-seguranca.md)
3. [operacao/09-observabilidade.md](operacao/09-observabilidade.md)

## O que já está pronto e o que falta

Pronto no back-end: identidade, clientes, produtos, fornecedores, auditoria, estoque, pedidos e leituras (painel e período). Banco atual: SQLite.

Ainda fora deste repositório de API:

- o front continua em `localStorage`; o contrato da ligação está em [desenvolvimento/13-integracao-front.md](desenvolvimento/13-integracao-front.md);
- PostgreSQL entra quando a operação sair de uma máquina só;
- não há Celery, Redis, WebSocket nem fila.

Mantenha [AGENTS.md](AGENTS.md) e [desenvolvimento/12-catalogo-de-api.md](desenvolvimento/12-catalogo-de-api.md) no mesmo passo de qualquer rota ou regra nova.
