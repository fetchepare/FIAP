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

# Criar usuário não-root
RUN groupadd -g ${GID} ${USER} \
    && useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USER}

# Dependências de sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho da aplicação
WORKDIR /app

# Dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

#RUN cp ./TechChallenge.ipynb /home/jupyter/notebooks
#RUN cp ./cancer_mama.csv /home/jupyter/notebooks

# Criar diretório para notebooks e mover notebook principal para lá
RUN mkdir -p /home/jupyter/notebooks && cp /app/cancer_mama.csv /home/jupyter/notebooks/ && cp /app/TechChallenge01.ipynb /home/jupyter/notebooks/ && cp /app/cancer_mama.csv /home/jupyter/notebooks/ && chown -R ${UID}:${GID} /home/jupyter && chown -R ${UID}:${GID} /app

# Mudar para usuário não-root
USER ${USER}

# Expor porta do Jupyter
EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--NotebookApp.token=", "--NotebookApp.password=", "--notebook-dir=/home/jupyter/notebooks"]
