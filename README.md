# FinFamily - Gestão Financeira Familiar

## 🚀 Deploy no Render

### Pré-requisitos

1. **Conta no MongoDB Atlas** (gratuito)
   - Acesse: https://www.mongodb.com/cloud/atlas
   - Crie um cluster gratuito (M0)
   - Obtenha a connection string (formato: `mongodb+srv://user:password@cluster.mongodb.net/`)

2. **Conta no Render** (gratuito)
   - Acesse: https://render.com
   - Conecte sua conta GitHub

### Passo a Passo

#### 1. Configurar MongoDB Atlas

1. Crie um cluster gratuito no MongoDB Atlas
2. Crie um usuário de banco de dados
3. Adicione `0.0.0.0/0` na lista de IPs permitidos (Network Access)
4. Copie a connection string

#### 2. Deploy do Backend (API)

1. No Render, clique em **New > Web Service**
2. Conecte seu repositório GitHub
3. Configure:
   - **Name:** `finamily-api`
   - **Root Directory:** `backend`
   - **Runtime:** `Docker`
   - **Instance Type:** Free

4. Adicione as **Environment Variables**:
   ```
   MONGO_URL=mongodb+srv://seu-usuario:sua-senha@cluster.mongodb.net/finamily?retryWrites=true&w=majority
   DB_NAME=finamily
   JWT_SECRET=sua-chave-secreta-muito-segura-aqui
   CORS_ORIGINS=https://finamily-app.onrender.com
   ```

5. Clique em **Create Web Service**

#### 3. Deploy do Frontend

1. No Render, clique em **New > Web Service**
2. Conecte o mesmo repositório
3. Configure:
   - **Name:** `finamily-app`
   - **Root Directory:** `frontend`
   - **Runtime:** `Docker`
   - **Instance Type:** Free

4. Adicione as **Environment Variables**:
   ```
   REACT_APP_BACKEND_URL=https://finamily-api.onrender.com
   ```

5. Clique em **Create Web Service**

### 📋 Variáveis de Ambiente

#### Backend
| Variável | Descrição | Exemplo |
|----------|-----------|--------|
| `MONGO_URL` | Connection string do MongoDB | `mongodb+srv://...` |
| `DB_NAME` | Nome do banco de dados | `finamily` |
| `JWT_SECRET` | Chave secreta para tokens JWT | `sua-chave-segura` |
| `CORS_ORIGINS` | URLs permitidas (separadas por vírgula) | `https://finamily-app.onrender.com` |

#### Frontend
| Variável | Descrição | Exemplo |
|----------|-----------|--------|
| `REACT_APP_BACKEND_URL` | URL do backend | `https://finamily-api.onrender.com` |

### ⚠️ Notas Importantes

1. **Plano Gratuito do Render:**
   - Os serviços "dormem" após 15 minutos de inatividade
   - O primeiro acesso após dormir pode demorar 30-60 segundos

2. **MongoDB Atlas Gratuito:**
   - Limite de 512MB de armazenamento
   - Suficiente para uso pessoal/familiar

3. **Atualizações:**
   - O Render faz deploy automático a cada push na branch main

### 🔧 Desenvolvimento Local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

### 📝 Licença

MIT
