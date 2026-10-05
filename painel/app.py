"""Painel Streamlit: KPIs e gráficos a partir dos marts do dbt (schema marts)."""

from __future__ import annotations

import streamlit as st

from db import (
    FONTES_VALIDAS,
    MSG_MARTS_AUSENTES,
    carregar_amostra_leituras,
    carregar_dim_maquina,
    carregar_falhas_diarias,
    conectar,
    distribuicao_modos,
    kpis_de_dim,
    marts_existem,
)

st.set_page_config(
    page_title="Pipeline industrial — marts",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Painel de sensores industriais")
st.caption("Dados lidos somente do schema **marts** (dbt). Filtro por fonte afeta KPIs, gráficos e a tabela.")

fontes = st.sidebar.multiselect(
    "Fonte dos dados",
    options=list(FONTES_VALIDAS),
    default=list(FONTES_VALIDAS),
    help="ai4i = dataset público; simulado = gerador com semente fixa.",
)
if not fontes:
    st.warning("Selecione ao menos uma fonte na barra lateral.")
    st.stop()

try:
    conn = conectar()
except Exception as exc:
    st.error(f"Não foi possível conectar ao PostgreSQL: {exc}")
    st.info("Confira as variáveis `POSTGRES_*` (arquivo `.env`) e se o banco está no ar.")
    st.stop()

try:
    if not marts_existem(conn):
        st.warning(MSG_MARTS_AUSENTES)
        conn.close()
        st.stop()

    dim = carregar_dim_maquina(conn, fontes)
    diarias = carregar_falhas_diarias(conn, fontes)
    amostra = carregar_amostra_leituras(conn, fontes, limite=200)
finally:
    conn.close()

kpis = kpis_de_dim(dim)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Máquinas", f"{kpis['maquinas']:,}".replace(",", "."))
c2.metric("Leituras", f"{kpis['leituras']:,}".replace(",", "."))
c3.metric("Leituras com falha", f"{kpis['falhas']:,}".replace(",", "."))
c4.metric("Taxa de falha", f"{kpis['taxa_falha_pct']:.2f} %")

st.subheader("Falhas por máquina")
if dim.empty:
    st.info("Nenhuma máquina para as fontes selecionadas.")
else:
    chart_maq = dim.set_index("id_maquina")[["total_falhas", "total_leituras"]]
    st.bar_chart(chart_maq["total_falhas"])
    st.dataframe(
        dim[["id_maquina", "fonte", "total_leituras", "total_falhas"]],
        use_container_width=True,
        hide_index=True,
    )

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Falhas por dia")
    if diarias.empty:
        st.info("Sem falhas diárias para o filtro atual.")
    else:
        serie = diarias.groupby("data_ref", as_index=False)["qtd_falhas"].sum()
        serie = serie.sort_values("data_ref")
        st.line_chart(serie.set_index("data_ref")["qtd_falhas"])

with col_b:
    st.subheader("Distribuição de modos de falha")
    modos = distribuicao_modos(diarias)
    if modos.empty:
        st.info("Sem modos de falha no filtro atual.")
    else:
        st.bar_chart(modos.set_index("modo")["ocorrencias"])
        st.caption("Contagem de dias-máquina em que o modo aparece (não é o nº de leituras).")

st.subheader("Amostra de leituras (marts.fct_leituras)")
st.dataframe(amostra, use_container_width=True, hide_index=True)

st.divider()
st.markdown(
    "Pré-requisitos: `docker compose up -d postgres` → "
    "`docker compose run --rm app` → "
    "`docker compose run --rm --build dbt build` → este painel."
)
