# FinFamily - Gestão Financeira Familiar 🏠💰

Sistema completo de gestão financeira familiar, **self-hosted**, rodando em um único container Docker.

## ✨ Funcionalidades

- 📊 **Dashboard** com resumo financeiro, gráficos e indicadores
- 💳 **Importação de extratos** (CSV) com categorização automática
- 👨‍👩‍👧‍👦 **Multi-usuário** com sistema de aprovação
- 🎯 **Metas financeiras** com acompanhamento de progresso
- 🏆 **Gamificação** - Badges, desafios em família e score de saúde financeira
- 🔒 **Segurança** - Autenticação JWT, senhas hasheadas
- 📱 **Interface moderna** - Dark mode, responsivo

## 🚀 Deploy Rápido

### Opção 1: Docker (Recomendado)

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/finamily.git
cd finamily

# Build e run
docker build -t finamily .
docker run -d \
  -p 8000:8000 \
  -v finamily_data:/app/data \
  -e JWT_SECRET=sua-chave-secreta-muito-segura \
  --name finamily \
  finamily
```

Acesse: **http://localhost:8000**

### Opção 2: Docker Compose

Crie um arquivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  finamily:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - finamily_data:/app/data
    environment:
      - JWT_SECRET=sua-chave-secreta-muito-segura
    restart: unless-stopped

volumes:
  finamily_data:
```

```bash
docker-compose up -d
```

### Opção 3: Render.com (Free Tier)

1. Fork este repositório
2. Crie uma conta no [Render.com](https://render.com)
3. New > Web Service > Connect your repo
4. Configure:
   - **Build Command:** `docker build -t finamily .`
   - **Start Command:** Deixe em branco (usa CMD do Dockerfile)
   - **Instance Type:** Free
5. Adicione variável de ambiente:
   - `JWT_SECRET` = sua chave secreta

> ⚠️ No plano gratuito, o serviço "dorme" após 15min de inatividade.

### Opção 4: Railway / Fly.io / DigitalOcean App Platform

Todos suportam deploy via Dockerfile. Siga as instruções específicas de cada plataforma.

## 📋 Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `JWT_SECRET` | Chave secreta para tokens JWT | `change-this-secret-key` |
| `DATABASE_PATH` | Caminho do banco SQLite | `/app/data/finamily.db` |

## 🗄️ Persistência de Dados

Os dados são armazenados em um arquivo SQLite em `/app/data/finamily.db`.

**Importante:** Monte um volume Docker para persistir os dados:

```bash
-v finamily_data:/app/data
# ou
-v /seu/caminho/local:/app/data
```

### Backup

```bash
# Copiar o banco de dados
docker cp finamily:/app/data/finamily.db ./backup_$(date +%Y%m%d).db
```

### Restaurar

```bash
# Parar o container
docker stop finamily

# Copiar o backup
docker cp ./backup.db finamily:/app/data/finamily.db

# Iniciar novamente
docker start finamily
```

## 👤 Primeiro Acesso

1. Acesse a aplicação
2. Clique em "Criar conta"
3. O **primeiro usuário** é automaticamente administrador e aprovado
4. Usuários subsequentes precisam de aprovação do admin

**Credenciais padrão de desenvolvimento:**
- Email: `admin@finamily.com`
- Senha: (definida no registro)

## 🛠️ Desenvolvimento Local

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar
uvicorn server:app --reload --port 8001
```

### Frontend

```bash
cd frontend

# Instalar dependências
yarn install

# Rodar em modo desenvolvimento
yarn start
```

## 📁 Estrutura do Projeto

```
finamily/
├── Dockerfile          # Build unificado (frontend + backend)
├── README.md
├── backend/
│   ├── server.py       # API FastAPI
│   ├── database.py     # Configuração SQLite
│   ├── requirements.txt
│   └── data/           # Banco SQLite (gerado automaticamente)
└── frontend/
    ├── package.json
    ├── src/
    │   ├── pages/      # Páginas React
    │   ├── components/ # Componentes UI
    │   └── App.js
    └── public/
```

## 🔧 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/auth/register` | Registro de usuário |
| POST | `/api/auth/login` | Login |
| GET | `/api/dashboard/summary` | Resumo financeiro |
| GET | `/api/transactions` | Listar transações |
| POST | `/api/transactions/import` | Importar CSV |
| GET | `/api/gamification/health-score` | Score de saúde financeira |
| GET | `/api/health` | Health check |

[Ver documentação completa em `/docs`]

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

Desenvolvido com ❤️ para famílias organizarem suas finanças.
