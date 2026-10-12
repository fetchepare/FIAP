# Limites de uso da IA, governança e privacidade
Fonte: boas práticas de IA em saúde e Lei Geral de Proteção de Dados (Lei 13.709/2018). Resumo didático.

## Papel da Guardiã AI
O sistema é de apoio ao profissional. Não realiza diagnóstico médico definitivo, não prescreve medicamentos e não toma decisões de forma automática. A decisão final é sempre de uma pessoa responsável pelo atendimento, que deve registrar sua conclusão.

## Erros do modelo e seus impactos
Um falso negativo (caso maligno classificado como baixo risco) pode atrasar o diagnóstico e é o erro mais grave neste cenário; por isso o limiar do modelo prioriza o recall. Um falso positivo gera ansiedade, exames adicionais e custo, mas é geralmente corrigido na investigação complementar. Resultado de baixo risco nunca exclui doença.

## Dados pessoais
Dados de saúde são dados pessoais sensíveis. Devem ser tratados com finalidade específica, acesso restrito por perfil, registro de acessos e minimização: a aplicação usa um identificador pseudonimizado do caso e evita nomes, CPF e telefone. Dados públicos, anonimizados ou sintéticos devem ser usados em desenvolvimento e demonstrações.

## Explicabilidade e auditoria
Cada análise deve registrar os dados utilizados, a versão do modelo, o resultado, as fontes consultadas e a decisão humana, permitindo auditoria posterior.
