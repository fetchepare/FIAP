# Deploy no Azure App Service

## Passo 1 — Criar o App Service

No portal Azure:
1. **Criar recurso → Web App**
2. Preencha:
   - **Nome**: `saude-mulher-ia` (ou outro disponível)
   - **Publicar**: Código
   - **Pilha de runtime**: Python 3.12
   - **SO**: Linux
   - **Plano**: B1 (Basic) — ~USD 13/mês, suficiente para demo
3. Clique em **Revisar + criar**

---

## Passo 2 — Configurar variáveis de ambiente

No App Service → **Configuração → Configurações do Aplicativo**, adicione:

| Nome | Valor |
|---|---|
| `AZURE_LANGUAGE_KEY` | chave do Azure Language |
| `AZURE_LANGUAGE_ENDPOINT` | endpoint do Azure Language |
| `AZURE_COMMUNICATION_CONNECTION_STRING` | connection string |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/home/credentials/google-credentials.json` |
| `WEBSITES_PORT` | `8000` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |

---

## Passo 3 — Fazer o upload do google-credentials.json (se usar Speech)

Via SSH do App Service ou Azure CLI:
```bash
# Conectar via SSH no portal: App Service → SSH
mkdir -p /home/credentials
# Fazer upload do JSON pelo portal Files ou via CLI
```

---

## Passo 4 — Fazer o deploy do zip

### Opção A — Portal (mais fácil)
1. App Service → **Centro de Implantação → Implantação Manual → ZIP Deploy**
2. Selecione o arquivo `saude-mulher-ia-azure.zip`

### Opção B — Azure CLI
```bash
az login
az webapp deploy \
  --resource-group rg-saude-mulher \
  --name saude-mulher-ia \
  --src-path saude-mulher-ia-azure.zip \
  --type zip
```

---

## Passo 5 — Configurar o comando de startup

App Service → **Configuração → Configurações Gerais → Comando de Inicialização**:
```
bash startup.sh
```

---

## Passo 6 — Acessar

```
https://saude-mulher-ia.azurewebsites.net
```

---

## Observações

- O banco SQLite fica em `/home/data/saude_mulher.db` (persistente entre deploys)
- Logs: App Service → **Fluxo de log**
- Se o build demorar (pacotes ML), aumente o timeout: `az webapp config set --startup-file "bash startup.sh"`
- Os pacotes pesados (ultralytics, mediapipe, librosa) estão comentados no requirements.txt — o sistema funciona em modo demo sem eles
