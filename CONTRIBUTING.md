# Contribuindo

Obrigado pelo interesse em **pipeline-dados-industriais**! Este é um projeto educacional/de portfólio (pipeline ETL de sensores industriais com Python, Parquet e PostgreSQL).

## Como sugerir melhorias

- **Ideias e problemas:** abra uma [issue](https://github.com/DenisPaulo/pipeline-dados-industriais/issues) explicando o que você observou ou propõe.
- **Código ou documentação:** faça um fork, crie uma branch e abra um Pull Request descrevendo a mudança. Prefira PRs pequenos e focados.

## Como rodar localmente

Siga o [README](README.md). Resumo:

```bash
python -m venv .venv && source .venv/bin/activate
make install          # instala requirements-dev.txt
cp .env.example .env  # e troque a senha
```

## Antes de abrir o PR

```bash
make lint   # ruff check + ruff format --check
make test   # pytest rápido: sem rede e sem PostgreSQL
```

Os testes de integração (exigem um PostgreSQL real) são opcionais: `make up && make test-integration`.

Não inclua segredos, credenciais ou dados pessoais no código, nos commits ou nos exemplos (veja a [Política de Segurança](SECURITY.md)).

## Padrão de commits

Mensagens curtas e no imperativo, em português, com um prefixo opcional:

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` documentação
- `test:` testes
- `chore:` manutenção
