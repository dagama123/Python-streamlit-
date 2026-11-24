
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Cash Plan", page_icon="💰", layout="centered")

st.title("💰 Cash Plan")
st.caption("Особистий трекер бюджету · Python + Streamlit версія")

if "txns" not in st.session_state:
    st.session_state.txns = [
        {"name": "Зарплата",   "amount": 5000, "type": "Дохід",   "cat": "Зарплата",    "date": "2026-06-01"},
        {"name": "Продукти",   "amount": 800,  "type": "Витрата", "cat": "Їжа",         "date": "2026-06-02"},
        {"name": "Проїзд",     "amount": 200,  "type": "Витрата", "cat": "Транспорт",   "date": "2026-06-03"},
        {"name": "Netflix",    "amount": 50,   "type": "Витрата", "cat": "Розваги",     "date": "2026-06-04"},
        {"name": "Стипендія",  "amount": 1200, "type": "Дохід",   "cat": "Інше",        "date": "2026-05-10"},
        {"name": "Комунальні", "amount": 400,  "type": "Витрата", "cat": "Комунальні",  "date": "2026-05-15"},
    ]

if "budget_limit" not in st.session_state:
    st.session_state.budget_limit = 3000

df = pd.DataFrame(st.session_state.txns)

total_inc = df[df["type"] == "Дохід"]["amount"].sum()
total_exp = df[df["type"] == "Витрата"]["amount"].sum()
balance   = total_inc - total_exp

col1, col2, col3 = st.columns(3)
col1.metric("Доходи",  f"+{total_inc:,.0f} zł")
col2.metric("Витрати", f"-{total_exp:,.0f} zł")
col3.metric("Баланс",  f"{balance:+,.0f} zł")

st.divider()

tab_add, tab_chart, tab_budget = st.tabs(["➕ Додати", "📊 Графік", "🎯 Бюджет"])

with tab_add:
    with st.form("add_txn", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name   = c1.text_input("Назва")
        amount = c2.number_input("Сума (zł)", min_value=0.0, step=10.0)
        c3, c4, c5 = st.columns(3)
        txn_type = c3.selectbox("Тип", ["Дохід", "Витрата"])
        cat      = c4.selectbox("Категорія", ["Зарплата", "Їжа", "Транспорт", "Розваги", "Комунальні", "Інше"])
        txn_date = c5.date_input("Дата", value=date.today())
        submitted = st.form_submit_button("Додати транзакцію", use_container_width=True)
        if submitted and name and amount > 0:
            st.session_state.txns.append({
                "name": name, "amount": amount,
                "type": txn_type, "cat": cat,
                "date": str(txn_date)
            })
            st.rerun()

    st.subheader("Транзакції", divider="gray")
    for i, t in enumerate(reversed(st.session_state.txns)):
        idx = len(st.session_state.txns) - 1 - i
        icon  = "🟢" if t["type"] == "Дохід" else "🔴"
        sign  = "+" if t["type"] == "Дохід" else "-"
        rc1, rc2, rc3 = st.columns([3, 1, 0.4])
        rc1.write(f"{icon} **{t['name']}** — {t['cat']} · {t['date']}")
        rc2.write(f"{sign}{t['amount']:,.0f} zł")
        if rc3.button("🗑", key=f"del_{idx}"):
            st.session_state.txns.pop(idx)
            st.rerun()

with tab_chart:
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%b %Y")
    monthly = df.groupby(["month", "type"])["amount"].sum().reset_index()
    fig = px.bar(
        monthly, x="month", y="amount", color="type",
        barmode="group",
        color_discrete_map={"Дохід": "#1D9E75", "Витрата": "#D85A30"},
        labels={"amount": "Сума (zł)", "month": "Місяць", "type": "Тип"},
        title="Доходи та витрати по місяцях"
    )
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)

    cat_exp = df[df["type"] == "Витрата"].groupby("cat")["amount"].sum().reset_index()
    if not cat_exp.empty:
        fig2 = px.pie(cat_exp, names="cat", values="amount", title="Витрати по категоріях",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig2, use_container_width=True)

with tab_budget:
    st.session_state.budget_limit = st.number_input(
        "Місячний ліміт витрат (zł)",
        min_value=0, value=st.session_state.budget_limit, step=100
    )
    current_month = date.today().strftime("%b %Y")
    df["month_str"] = pd.to_datetime(df["date"]).dt.strftime("%b %Y")
    this_month_exp = df[(df["type"] == "Витрата") & (df["month_str"] == current_month)]["amount"].sum()
    pct = min(100, int((this_month_exp / st.session_state.budget_limit * 100))) if st.session_state.budget_limit > 0 else 0

    st.write(f"**Витрачено цього місяця:** {this_month_exp:,.0f} zł з {st.session_state.budget_limit:,.0f} zł ({pct}%)")
    color = "normal" if pct < 70 else ("off" if pct < 90 else "inverse")
    st.progress(pct / 100)
    if pct >= 90:
        st.error("⚠️ Ти перевищуєш бюджет!")
    elif pct >= 70:
        st.warning("📊 Вже 70% бюджету використано")
    else:
        st.success("✅ Бюджет в нормі")
