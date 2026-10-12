#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "🛡️  Guardiã AI — Inicialização Containerizada (Docker)"
echo "=========================================================="

# Define se usa docker direto ou com sudo
if docker ps >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
    DOCKER_BIN="docker"
else
    echo "ℹ️  Docker requer privilégios administrativos (sudo)."
    DOCKER_COMPOSE="sudo docker compose"
    DOCKER_BIN="sudo docker"
fi

# Conexão do snap a discos em /media caso seja snap
if command -v snap >/dev/null 2>&1 && snap list docker >/dev/null 2>&1; then
    echo "ℹ️  Detectado Docker via Snap. Verificando permissões em mídias externas..."
    sudo snap connect docker:removable-media 2>/dev/null || true
fi

echo "📦 Construindo imagem e inicializando contêineres..."
$DOCKER_COMPOSE up --build -d

echo ""
echo "✅ Contêineres iniciados com sucesso!"
echo "----------------------------------------------------------"
echo "🌐 Interface Web (Streamlit):  http://localhost:8501"
echo "📖 API REST (Swagger Docs):    http://localhost:8000/docs"
echo "----------------------------------------------------------"
echo "Comandos úteis:"
echo "  • Ver logs:   $DOCKER_COMPOSE logs -f"
echo "  • Status:     $DOCKER_COMPOSE ps"
echo "  • Parar:      $DOCKER_COMPOSE down"
echo "=========================================================="
