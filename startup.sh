#!/bin/bash
# Script de inicialização para Azure App Service
# Configurado em: Configuração → Comandos de Inicialização → bash startup.sh

echo "=== Iniciando IA Saúde da Mulher ==="

# Criar diretório persistente para o banco de dados
mkdir -p /home/data

# Popular banco com dados de demonstração
python seed_db.py

# Iniciar o servidor
# Azure App Service expõe na porta 8000 por padrão (WEBSITES_PORT)
gunicorn \
  --bind=0.0.0.0:8000 \
  --timeout=600 \
  --workers=2 \
  --worker-class=uvicorn.workers.UvicornWorker \
  --access-logfile=- \
  --error-logfile=- \
  src.api.main:app
