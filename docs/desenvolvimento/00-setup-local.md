# G-GÁS — Setup local

Pasta: `G_GAS_BACK`. Python 3.12. Shell: PowerShell. Não use `&&`.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_inicial
python manage.py runserver
```

Se o `venv` já existe, ative e use `.\venv\Scripts\python.exe`.

## Seed

Usuário `admin`, senha `Ggas@123`, e-mail `admin@ggas.com.br`. Vale para o SQLite desta máquina. O comando não grava auditoria.

## Variáveis

Copie `.env.example` para `.env` se quiser sobrepor o padrão. Sem arquivo, o projeto sobe com:

- `DJANGO_DEBUG=True`
- `ALLOWED_HOSTS=localhost,127.0.0.1`
- `CORS` para as portas 3000 e 5173
- `SECRET_KEY` de desenvolvimento longa o bastante para o HMAC do JWT

Troque a chave antes de qualquer ambiente compartilhado. O JWT exige pelo menos 32 bytes.

## Conferir

- `GET http://127.0.0.1:8000/api/health/`
- Swagger em `http://127.0.0.1:8000/api/schema/swagger/`
- Login: `POST /auth/token_jwt/` com `{"username": "admin", "password": "Ggas@123"}`

O front ainda não aponta para esta API.
