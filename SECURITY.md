# Política de Segurança

Este é um projeto educacional/de portfólio (pipeline ETL de sensores industriais com Python, Parquet e PostgreSQL). Não há suporte formal nem garantia de prazo de correção, mas levo a sério qualquer problema reportado.

## Como reportar uma vulnerabilidade

- Se a aba **Security** do repositório exibir **Report a vulnerability**, use essa opção (GitHub Security Advisories) para um relato privado.
- Caso contrário, abra uma [issue](https://github.com/DenisPaulo/pipeline-dados-industriais/issues) descrevendo o problema **sem incluir dados sensíveis** (credenciais, chaves, dados pessoais ou passos de exploração detalhados). Se necessário, peço mais detalhes pela própria issue.

## Segredos e credenciais

- As credenciais do PostgreSQL vêm **somente de variáveis de ambiente** (arquivo `.env` local, já ignorado pelo Git). O `.env.example` traz apenas placeholders.
- Nunca faça commit de chaves, senhas, tokens ou dados pessoais. Se encontrar um segredo exposto neste repositório, avise pela forma acima e não o reutilize.
- O `docker-compose.yml` publica a porta do banco apenas em `127.0.0.1`. Se for usar fora de um ambiente de estudo, troque a senha, não exponha a porta e revise as permissões do banco.
