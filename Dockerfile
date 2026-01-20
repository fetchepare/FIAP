# Dockerfile para execução do TechChallenge01.ipynb
# Versão: 1.0
# Autor: César Melo Dutra/Fernando Ramos Etchepare
# Data: 20/01/2026

# Use imagem base do Python
FROM python:3.9-slim

# Definir variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    USER=jupyter \
    UID=1000 \
    GID=1000 \
    HOME=/home/jupyter

# Usuário
RUN groupadd -g ${GID} ${USER} \
    && useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USER}

# Dependências
RUN apt-get update && apt-get install -y build-essential curl git && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Dependências
COPY requirements.txt .

# Dependências Python
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

# Copiar notebook principal
COPY TechChallenge01.ipynb .

# Criar diretório para notebooks e conceder permissões
RUN mkdir -p /home/jupyter/notebooks \
    && chown -R ${UID}:${GID} /home/jupyter \
    && chown -R ${UID}:${GID} /app

# Mudar para usuário não-root
USER ${USER}

# Expor porta do Jupyter
EXPOSE 8888

# Comando de inicialização
CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--allow-root", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''", \
     "--notebook-dir=/home/jupyter/notebooks"]
