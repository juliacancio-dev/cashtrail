# Atualização anual do IRPF

Os valores fiscais ficam em arquivos versionados por ano-calendário ([ADR-016](../decisoes/ADR-016-parametros-fiscais-por-ano.md)). Sem o arquivo do ano, a tela de IRPF devolve erro (HTTP 422) em vez de calcular com valores velhos. Faça isto **uma vez por ano**, quando a Receita publicar as tabelas do novo ano-calendário.

## Passos

1. Abra a página oficial de tabelas do IRPF da Receita Federal e localize a seção do exercício seguinte ao ano-calendário (para o ano-calendário 2027, a seção "a partir do exercício 2028").
2. Copie o arquivo do ano anterior:
   ```bash
   cp backend/src/features/tax/parameters/2026.json backend/src/features/tax/parameters/2027.json
   ```
3. Atualize, **só com fonte oficial**:
   - faixas e alíquotas da tabela progressiva anual;
   - dedução por dependente, limite de educação, limite do desconto simplificado;
   - redutor (se a lei continuar valendo) e qualquer regra nova;
   - a fonte (URL) e a data da consulta de cada bloco.
4. Mantenha a lista de itens **não verificados** atualizada: o que você não confirmou continua lá e aparece na tela como premissa.
5. Rode os testes da slice e acrescente um caso do ano novo conferido à mão contra a tabela oficial:
   ```bash
   cd backend && pytest src/features/tax
   ```
6. No pull request, cite a página da Receita e a data da consulta.

## O que muda raramente, mas vale conferir

- Regras de renda variável (alíquota, isenção mensal de R$ 20.000 em vendas de ações, código e prazo do DARF).
- Tabela regressiva de previdência e de renda fixa.
- As premissas abertas listadas em [Integrações externas](../referencia/integracoes-externas.md#receita-federal); se alguma for confirmada, mova-a para a parte verificada.
