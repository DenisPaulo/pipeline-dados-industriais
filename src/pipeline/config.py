"""Configuração do pipeline, lida somente de variáveis de ambiente (sem segredos no código)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
FONTES_VALIDAS = ("ai4i", "simulado")


class ErroConfiguracao(RuntimeError):
    """Variável de ambiente ausente ou inválida."""


@dataclass(frozen=True)
class Config:
    """Parâmetros de execução. Use :meth:`Config.do_ambiente` para ler do ambiente."""

    data_dir: Path
    sql_dir: Path
    fontes: tuple[str, ...] = FONTES_VALIDAS
    semente: int = 42
    db_nome: str = "pipeline"
    db_usuario: str = "pipeline"
    db_senha: str | None = None
    db_host: str = "localhost"
    db_porta: int = 5432

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def bruto_dir(self) -> Path:
        """Camada bruta em Parquet, particionada por data e máquina."""
        return self.data_dir / "processed" / "bruto"

    @property
    def limpo_dir(self) -> Path:
        return self.data_dir / "processed" / "limpo"

    @property
    def relatorio_path(self) -> Path:
        return self.data_dir / "processed" / "relatorio.json"

    def conexao_kwargs(self) -> dict[str, object]:
        """Argumentos para ``psycopg2.connect``. Exige POSTGRES_PASSWORD definido."""
        if not self.db_senha:
            raise ErroConfiguracao(
                "POSTGRES_PASSWORD não definido. Copie .env.example para .env e defina uma senha."
            )
        return {
            "dbname": self.db_nome,
            "user": self.db_usuario,
            "password": self.db_senha,
            "host": self.db_host,
            "port": self.db_porta,
        }

    @classmethod
    def do_ambiente(cls, env: dict[str, str] | None = None) -> Config:
        env = dict(os.environ) if env is None else env
        fontes = tuple(f.strip() for f in env.get("PIPELINE_FONTES", "ai4i,simulado").split(",") if f.strip())
        invalidas = [f for f in fontes if f not in FONTES_VALIDAS]
        if invalidas or not fontes:
            raise ErroConfiguracao(f"PIPELINE_FONTES inválido {invalidas or fontes}; use {FONTES_VALIDAS}.")
        try:
            semente = int(env.get("PIPELINE_SEMENTE", "42"))
            porta = int(env.get("POSTGRES_PORT", "5432"))
        except ValueError as exc:
            raise ErroConfiguracao(f"Valor numérico inválido no ambiente: {exc}") from exc
        return cls(
            data_dir=Path(env.get("PIPELINE_DATA_DIR", RAIZ_PROJETO / "data")),
            sql_dir=Path(env.get("PIPELINE_SQL_DIR", RAIZ_PROJETO / "sql")),
            fontes=fontes,
            semente=semente,
            db_nome=env.get("POSTGRES_DB", "pipeline"),
            db_usuario=env.get("POSTGRES_USER", "pipeline"),
            db_senha=env.get("POSTGRES_PASSWORD") or None,
            db_host=env.get("POSTGRES_HOST", "localhost"),
            db_porta=porta,
        )
