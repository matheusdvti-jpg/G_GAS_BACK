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

Usuário `admin`, senha `GgasLocal@2026`, e-mail `admin@ggas.com.br`. Vale para o SQLite desta máquina, e só quando `DJANGO_DEBUG` está ligado. O comando não grava auditoria. Com o debug desligado, ele não cria a conta e não escreve a senha. Uma conta `admin` que já existia com `Ggas@123` não é regravada: essa senha continua até alguém trocá-la.

## Variáveis

Copie `.env.example` para `.env`. No computador local, deixe `DJANGO_DEBUG=True`. Sem isso, e com a chave do exemplo, o processo recusa subir.

Sem arquivo, o padrão é `DJANGO_DEBUG` desligado, `ALLOWED_HOSTS=localhost,127.0.0.1`, CORS nas portas 3000 e 5173 e a `SECRET_KEY` de desenvolvimento. Esse padrão não sobe: a chave de desenvolvimento e a chave de banco do exemplo são recusadas quando o debug está desligado.

No ambiente publicado, troque `DJANGO_SECRET_KEY` e `DJANGO_DB_KEY` por valores longos e diferentes do exemplo. Atrás do proxy, o Django lê `X-Forwarded-Proto` e redireciona HTTP para HTTPS, com HSTS de um ano.

## Conferir

- `GET http://127.0.0.1:8000/api/health/`
- Swagger em `http://127.0.0.1:8000/api/schema/swagger/`, depois de entrar como administrador
- Login: `GET /auth/csrf/` e depois `POST /auth/token_jwt/` com `{"username": "admin", "password": "GgasLocal@2026"}` e o cabeçalho `X-CSRFToken` igual ao cookie `csrftoken`. Na base que já tinha o seed antigo, a senha continua `Ggas@123` até a troca.

O front ainda não aponta para esta API.
