# G-GÁS — Testes

Os testes são de API, com `APITestCase`. Cada classe chama `seed_inicial` e cria os perfis pela `ColaboradorBusiness`, com CPF de dígito verificador válido.

| Módulo | Arquivo | O que garante |
| --- | --- | --- |
| Colaboradores | `colaboradores/tests/test_acesso.py` | Login, inativo, perfil, último administrador, telefone e senha fora da auditoria e do histórico |
| Auditoria | `auditoria/tests/test_cadastros.py` | Cliente, produto, fornecedor, telefone de 10 ou 11 dígitos e a trilha |
| Pedidos | `pedidos/tests/test_operacao.py` | Estoque, venda, vazio, cancelamento sem segundo estorno, saldo que a venda baixou, permissão de status e o piso do seco |
| Relatorios | `relatorios/tests/test_leituras.py` | Painel, fechamento, perfil, cancelamento no número e o dia inclusivo em `America/Sao_Paulo` |

Rodar, na pasta `G_GAS_BACK`:

```powershell
.\venv\Scripts\python.exe manage.py test Colaboradores.colaboradores.tests Auditoria.auditoria.tests Pedidos.pedidos.tests Relatorios.relatorios.tests --verbosity 1
```

O banco de teste é outro SQLite, criado e destruído pelo Django.

Ao mexer em saldo, status ou leitura, estenda o teste do fluxo em vez de duplicar a regra só no serializer. Afirme o número que o balcão vê: cheio, seco, total, troco, código e o status HTTP de quem não pode.
