# Variáveis do conjunto Breast Cancer Wisconsin (Diagnostic)
Fonte: UCI Machine Learning Repository (Street, Wolberg e Mangasarian). Dados públicos e anonimizados.

## Origem das variáveis
As 30 variáveis são calculadas por análise computacional de imagens digitalizadas de punção aspirativa por agulha fina (PAAF) de massa mamária. Para cada núcleo celular são medidas dez características: raio, textura, perímetro, área, suavidade, compacidade, concavidade, pontos côncavos, simetria e dimensão fractal. Para cada característica o conjunto traz a média, o erro padrão e o pior valor (média dos três maiores), totalizando 30 variáveis.

## Interpretação cautelosa
Valores maiores de raio, perímetro, área, concavidade e pontos côncavos tendem a estar associados a núcleos de tumores malignos neste conjunto. Isso é uma associação estatística observada nos dados de treinamento, não uma regra clínica. Muitas variáveis são fortemente correlacionadas entre si (por exemplo, raio, perímetro e área), de modo que a importância individual de cada uma deve ser interpretada com cuidado.

## Limite de uso
Essas medidas dependem de uma amostra citológica já coletada e analisada. O modelo treinado nesses dados tem finalidade educacional e de apoio à análise inicial; não é um exame de diagnóstico.
