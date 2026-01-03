# ============================================
# FinFamily - Unified Docker Build
# Single container: Frontend + Backend + SQLite
# ============================================

# ==================== STAGE 1: Build Frontend ====================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copia apenas o package.json
COPY frontend/package.json ./

# --- CONFIGURAÇÕES PARA EVITAR TIMEOUT NO GOOGLE CLOUD ---
# 1. Aumenta o tempo limite para 10 minutos
RUN yarn config set network-timeout 600000
# 2. Troca o registro padrão do Yarn para o do NPM (costuma ser mais estável)
RUN yarn config set registry https://registry.npmjs.org/
# 3. Desativa verificação estrita de SSL (ajuda em alguns casos de rede)
RUN yarn config set strict-ssl false
# ---------------------------------------------------------

# Instala as dependências
RUN yarn install

# Copia o restante do código fonte
COPY frontend/ .

# Define URL da API como relativa (mesma origem)
ENV REACT_APP_BACKEND_URL=""

# Build do React
RUN yarn build

# ==================== STAGE 2: Production ====================
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/finamily.db

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy built frontend from stage 1
# OBS: O caminho de origem é /app/frontend/build. 
# Se seu projeto usar Vite, pode ser necessário mudar para /app/frontend/dist
COPY --from=frontend-builder /app/frontend/build ./static

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
