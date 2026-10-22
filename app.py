# Painel de Vendas | Demo da Aula 2 "Geração de Código" (MyHUB.IA)
# Código gerado com IA e revisado. Roda em versões antigas e novas do Streamlit.

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Painel de Vendas", page_icon="📊", layout="wide")

# ------------------------------------------------------------------
# Cores e estilo (mesma identidade visual da live)
# ------------------------------------------------------------------
TURQUESA = "#00EDE0"
CINZA = "#3A4A55"
PALETA = ["#00EDE0", "#7C9CFF", "#FFB547", "#FF6B8B", "#9BE564", "#C792EA"]

st.markdown(
    """
    <style>
    .block-container {padding-top: 3.2rem;}
    .card {background:#1C1C1C; border:1px solid #2A2A2A; border-radius:14px; padding:16px 18px;}
    .card .rotulo {color:#8B95A5; font-size:0.85rem; margin-bottom:4px;}
    .card .valor {color:#FFFFFF; font-size:1.7rem; font-weight:700; line-height:1.2;}
    .card .delta-pos {color:#00EDE0; font-size:0.85rem;}
    .card .delta-neg {color:#FF6B8B; font-size:0.85rem;}
    .insight {background:#132726; border-radius:12px; padding:12px 16px; margin-bottom:8px; color:#DDE7E6;}
    .titulo {font-size:2.1rem; font-weight:800; margin-bottom:0;}
    .subtitulo {color:#8B95A5; margin:0 0 14px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------------------------------------------------------
# Compatibilidade: versões novas usam width="stretch",
# versões antigas usam use_container_width=True
# ------------------------------------------------------------------
def grafico(chart):
    try:
        st.altair_chart(chart, width="stretch")
    except Exception:
        st.altair_chart(chart, use_container_width=True)


def tabela(df):
    try:
        st.dataframe(df, hide_index=True, width="stretch")
    except Exception:
        try:
            st.dataframe(df, hide_index=True, use_container_width=True)
        except Exception:
            st.dataframe(df)


def brl(valor):
    """Formata número no padrão brasileiro: R$ 1.234,56"""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sem_formula(texto):
    """O Markdown do Streamlit lê $...$ como fórmula; escapamos o cifrão."""
    return texto.replace("$", "\\$")


def card(coluna, rotulo, valor, delta=None):
    """Indicador em formato de cartão, com variação opcional."""
    html_delta = ""
    if delta is not None:
        classe = "delta-pos" if delta >= 0 else "delta-neg"
        seta = "▲" if delta >= 0 else "▼"
        html_delta = f'<div class="{classe}">{seta} {str(round(abs(delta), 1)).replace(".", ",")}% vs mês anterior</div>'
    coluna.markdown(
        f'<div class="card"><div class="rotulo">{rotulo}</div>'
        f'<div class="valor">{valor}</div>{html_delta}</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------------
# Dados: arquivo do repositório ou CSV enviado pelo usuário
# ------------------------------------------------------------------
@st.cache_data
def preparar(arquivo):
    df = pd.read_csv(arquivo, parse_dates=["data"])
    df["mes"] = df["data"].dt.to_period("M").astype(str)
    df["dia_semana"] = df["data"].dt.dayofweek
    if "canal" not in df.columns:
        df["canal"] = "Não informado"
    return df


st.sidebar.markdown("## 📊 Painel de Vendas")
envio = st.sidebar.file_uploader(
    "Use seus próprios dados (CSV)",
    type="csv",
    help="Colunas esperadas: data, produto, regiao, quantidade, valor e, opcionalmente, canal.",
)
try:
    df = preparar(envio if envio is not None else "vendas.csv")
except Exception as erro:
    st.error(f"Não consegui ler o arquivo. Confira as colunas. Detalhe: {erro}")
    st.stop()

# ------------------------------------------------------------------
# Filtros
# ------------------------------------------------------------------
st.sidebar.markdown("### Filtros")
data_min, data_max = df["data"].min().date(), df["data"].max().date()
periodo = st.sidebar.date_input("Período", (data_min, data_max), min_value=data_min, max_value=data_max)
inicio, fim = (periodo if isinstance(periodo, (list, tuple)) and len(periodo) == 2 else (data_min, data_max))

todos_prod = sorted(df["produto"].unique())
todas_reg = sorted(df["regiao"].unique())
todos_can = sorted(df["canal"].unique())
produtos = st.sidebar.multiselect("Produto", todos_prod, default=todos_prod)
regioes = st.sidebar.multiselect("Região", todas_reg, default=todas_reg)
canais = st.sidebar.multiselect("Canal", todos_can, default=todos_can)

filtro = (
    df["data"].dt.date.between(inicio, fim)
    & df["produto"].isin(produtos)
    & df["regiao"].isin(regioes)
    & df["canal"].isin(canais)
)
dados = df[filtro]

st.sidebar.markdown("---")
st.sidebar.caption("Demo da live Geração de Código | MyHUB.IA")

# ------------------------------------------------------------------
# Cabeçalho
# ------------------------------------------------------------------
st.markdown('<div class="titulo">Painel de Vendas</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="subtitulo">{len(dados)} vendas entre {inicio:%d/%m/%Y} e {fim:%d/%m/%Y}</div>',
    unsafe_allow_html=True,
)

if dados.empty:
    st.warning("Nenhuma venda com esses filtros. Ajuste a barra lateral.")
    st.stop()

# ------------------------------------------------------------------
# Indicadores com variação do último mês contra o anterior
# ------------------------------------------------------------------
por_mes = dados.groupby("mes").agg(faturamento=("valor", "sum"), qtd=("quantidade", "sum"), vendas=("valor", "size"))
por_mes["ticket"] = por_mes["faturamento"] / por_mes["vendas"]


def variacao(coluna):
    if len(por_mes) < 2 or por_mes[coluna].iloc[-2] == 0:
        return None
    return (por_mes[coluna].iloc[-1] / por_mes[coluna].iloc[-2] - 1) * 100


faturamento = dados["valor"].sum()
c1, c2, c3, c4 = st.columns(4)
card(c1, "Faturamento", brl(faturamento), variacao("faturamento"))
card(c2, "Itens vendidos", f"{int(dados['quantidade'].sum()):,}".replace(",", "."), variacao("qtd"))
card(c3, "Ticket médio", brl(faturamento / len(dados)), variacao("ticket"))
card(c4, "Número de vendas", f"{len(dados):,}".replace(",", "."), variacao("vendas"))
st.write("")

# ------------------------------------------------------------------
# Abas
# ------------------------------------------------------------------
aba1, aba2, aba3, aba4, aba5 = st.tabs(["Visão geral", "Produtos", "Regiões e canais", "Simulador de meta", "Dados"])

# ---------------- Visão geral
with aba1:
    esq, dir_ = st.columns([2, 1])
    with esq:
        st.markdown("#### Faturamento por mês")
        serie = por_mes.reset_index()
        serie["media_movel"] = serie["faturamento"].rolling(3, min_periods=1).mean()
        barras = alt.Chart(serie).mark_bar(color=TURQUESA, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("mes:N", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("faturamento:Q", title="R$", axis=alt.Axis(format="~s")),
            tooltip=[alt.Tooltip("mes:N", title="Mês"), alt.Tooltip("faturamento:Q", title="Faturamento", format=",.2f")],
        )
        linha = alt.Chart(serie).mark_line(color="#FFB547", point=True, strokeWidth=2).encode(
            x="mes:N", y="media_movel:Q",
            tooltip=[alt.Tooltip("media_movel:Q", title="Média móvel 3 meses", format=",.2f")],
        )
        grafico((barras + linha).properties(height=320))
        st.caption("Barras: faturamento do mês. Linha laranja: média móvel de 3 meses.")
    with dir_:
        st.markdown("#### Participação por produto")
        part = dados.groupby("produto", as_index=False)["valor"].sum()
        rosca = alt.Chart(part).mark_arc(innerRadius=60).encode(
            theta=alt.Theta("valor:Q"),
            color=alt.Color("produto:N", scale=alt.Scale(range=PALETA), legend=alt.Legend(title=None, orient="bottom", columns=3)),
            tooltip=[alt.Tooltip("produto:N", title="Produto"), alt.Tooltip("valor:Q", title="Faturamento", format=",.2f")],
        )
        grafico(rosca.properties(height=340))

    st.markdown("#### Insights automáticos")
    melhor_prod = dados.groupby("produto")["valor"].sum().idxmax()
    melhor_reg = dados.groupby("regiao")["valor"].sum().idxmax()
    melhor_mes = por_mes["faturamento"].idxmax()
    dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    melhor_dia = dias[dados.groupby("dia_semana")["valor"].sum().idxmax()]
    top = dados.groupby("produto")["valor"].sum().sort_values(ascending=False)
    concentracao = top.head(2).sum() / top.sum() * 100
    for texto in [
        f"🏆 O produto que mais faturou foi <b>{melhor_prod}</b>, e a região líder foi <b>{melhor_reg}</b>.",
        f"📅 O melhor mês do período foi <b>{melhor_mes}</b>, e o dia da semana mais forte é <b>{melhor_dia}</b>.",
        f"🎯 Os dois principais produtos concentram <b>{concentracao:.0f}%</b> do faturamento.",
    ]:
        st.markdown(f'<div class="insight">{texto}</div>', unsafe_allow_html=True)

# ---------------- Produtos
with aba2:
    resumo = dados.groupby("produto").agg(
        faturamento=("valor", "sum"), itens=("quantidade", "sum"), vendas=("valor", "size")
    ).reset_index()
    resumo["ticket"] = resumo["faturamento"] / resumo["vendas"]
    esq, dir_ = st.columns(2)
    with esq:
        st.markdown("#### Ranking de faturamento")
        ranking = alt.Chart(resumo).mark_bar(color=TURQUESA, cornerRadiusEnd=4).encode(
            x=alt.X("faturamento:Q", title="R$", axis=alt.Axis(format="~s")),
            y=alt.Y("produto:N", sort="-x", title=None),
            tooltip=[alt.Tooltip("produto:N"), alt.Tooltip("faturamento:Q", format=",.2f")],
        )
        grafico(ranking.properties(height=320))
    with dir_:
        st.markdown("#### Volume x ticket médio")
        bolhas = alt.Chart(resumo).mark_circle(opacity=0.85).encode(
            x=alt.X("itens:Q", title="Itens vendidos"),
            y=alt.Y("ticket:Q", title="Ticket médio (R$)"),
            size=alt.Size("faturamento:Q", legend=None, scale=alt.Scale(range=[200, 2500])),
            color=alt.Color("produto:N", scale=alt.Scale(range=PALETA), legend=alt.Legend(title=None)),
            tooltip=["produto:N", "itens:Q", alt.Tooltip("ticket:Q", format=",.2f"), alt.Tooltip("faturamento:Q", format=",.2f")],
        )
        grafico(bolhas.properties(height=320))
        st.caption("Bolha maior = mais faturamento. À direita vende muito; no alto vende caro.")

    st.markdown("#### Evolução mensal por produto")
    evol = dados.groupby(["mes", "produto"], as_index=False)["valor"].sum()
    linhas = alt.Chart(evol).mark_line(point=True).encode(
        x=alt.X("mes:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("valor:Q", title="R$", axis=alt.Axis(format="~s")),
        color=alt.Color("produto:N", scale=alt.Scale(range=PALETA), legend=alt.Legend(title=None, orient="top")),
        tooltip=["mes:N", "produto:N", alt.Tooltip("valor:Q", format=",.2f")],
    )
    grafico(linhas.properties(height=300))

# ---------------- Regiões e canais
with aba3:
    esq, dir_ = st.columns(2)
    with esq:
        st.markdown("#### Faturamento por região")
        reg_df = dados.groupby("regiao", as_index=False)["valor"].sum()
        grafico(
            alt.Chart(reg_df).mark_bar(color="#7C9CFF", cornerRadiusEnd=4).encode(
                x=alt.X("valor:Q", title="R$", axis=alt.Axis(format="~s")),
                y=alt.Y("regiao:N", sort="-x", title=None),
                tooltip=["regiao:N", alt.Tooltip("valor:Q", format=",.2f")],
            ).properties(height=280)
        )
    with dir_:
        st.markdown("#### Vendas por canal")
        can_df = dados.groupby("canal", as_index=False)["valor"].sum()
        grafico(
            alt.Chart(can_df).mark_arc(innerRadius=55).encode(
                theta="valor:Q",
                color=alt.Color("canal:N", scale=alt.Scale(range=["#00EDE0", "#FFB547", "#FF6B8B"]), legend=alt.Legend(title=None, orient="bottom")),
                tooltip=["canal:N", alt.Tooltip("valor:Q", format=",.2f")],
            ).properties(height=280)
        )

    st.markdown("#### Mapa de calor: produto x região")
    calor = dados.groupby(["produto", "regiao"], as_index=False)["valor"].sum()
    base = alt.Chart(calor).encode(x=alt.X("regiao:N", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("produto:N", title=None))
    mapa = base.mark_rect(cornerRadius=3).encode(
        color=alt.Color("valor:Q", scale=alt.Scale(range=["#1C2A2A", TURQUESA]), legend=alt.Legend(title="R$", format="~s")),
        tooltip=["produto:N", "regiao:N", alt.Tooltip("valor:Q", format=",.2f")],
    )
    texto = base.mark_text(fontSize=11, color="#FFFFFF").encode(text=alt.Text("valor:Q", format=",.0f"))
    grafico((mapa + texto).properties(height=320))

# ---------------- Simulador de meta
with aba4:
    st.markdown("#### Quanto falta para a meta?")
    media = por_mes["faturamento"].mean()
    col_a, col_b = st.columns(2)
    meta = col_a.number_input("Meta de faturamento mensal (R$)", min_value=0.0, value=float(round(media * 1.15, -3)), step=1000.0, format="%.0f")
    reajuste = col_b.slider("Simular reajuste de preço (%)", -20, 30, 0)

    atual = por_mes["faturamento"].iloc[-1]
    simulado = atual * (1 + reajuste / 100)
    pct = simulado / meta if meta else 0
    st.progress(min(max(pct, 0.0), 1.0))
    st.markdown(
        sem_formula(f"Último mês (**{por_mes.index[-1]}**): {brl(atual)}. "
        f"Com reajuste de {reajuste}%: **{brl(simulado)}**, que é **{pct * 100:.0f}%** da meta.")
    )
    if pct >= 1:
        st.success("Meta batida neste cenário. 🎉")
    else:
        st.info(sem_formula(f"Faltam {brl(meta - simulado)} para a meta neste cenário."))

    meses = por_mes.reset_index()[["mes", "faturamento"]]
    meses["status"] = meses["faturamento"].apply(lambda v: "Acima da meta" if v >= meta else "Abaixo da meta")
    barras_meta = alt.Chart(meses).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("mes:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("faturamento:Q", title="R$", axis=alt.Axis(format="~s")),
        color=alt.Color("status:N", scale=alt.Scale(domain=["Acima da meta", "Abaixo da meta"], range=[TURQUESA, CINZA]), legend=alt.Legend(title=None, orient="top")),
        tooltip=["mes:N", alt.Tooltip("faturamento:Q", format=",.2f"), "status:N"],
    )
    regua = alt.Chart(pd.DataFrame({"meta": [meta]})).mark_rule(color="#FFB547", strokeDash=[6, 4], size=2).encode(y="meta:Q")
    grafico((barras_meta + regua).properties(height=300))
    st.caption("Linha tracejada: meta mensal informada acima.")

# ---------------- Dados
with aba5:
    busca = st.text_input("Buscar na tabela (produto, região ou canal)")
    tabela_view = dados.drop(columns=["mes", "dia_semana"]).sort_values("data", ascending=False)
    if busca:
        termo = busca.lower()
        tabela_view = tabela_view[
            tabela_view[["produto", "regiao", "canal"]].apply(lambda col: col.str.lower().str.contains(termo)).any(axis=1)
        ]
    tabela_view = tabela_view.assign(data=tabela_view["data"].dt.strftime("%d/%m/%Y"))
    tabela(tabela_view)
    st.download_button(
        "⬇️ Baixar dados filtrados (CSV)",
        tabela_view.to_csv(index=False).encode("utf-8"),
        file_name="vendas_filtradas.csv",
        mime="text/csv",
    )
