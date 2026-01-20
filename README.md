Guia de Implantação e de Execução do Docker

Implantação:
mkdir techchallenge-project
cd techchallenge-project
e copiar os arquivos:
- TechChallenge01.ipynb
- Dockerfile
- requirements.txt
- cancer_mama.csv
docker build -t techchallenge:1.0 .
docker images | grep techchallenge

Execução:
docker run -d --name techchallenge-app -p 8888:8888 -v $(pwd)/notebooks:/home/jupyter/notebooks techchallenge:1.0

Acessar o Sistema:
Abrir navegador web e acessar: http://localhost:8888

No Jupyter Lab:
Navegar até /app/TechChallenge01.ipynb
Executar as células do notebook