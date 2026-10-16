from datetime import date

import pandas as pd
import streamlit as st

from budget_logic import (
    BANK_COLUMNS,
    BUDGET_COLUMNS,
    EXPENSE_COLUMNS,
    INCOME_COLUMNS,
    clean_frame,
    make_projection,
    numeric_total,
    starter_banks,
    starter_budget,
    starter_expenses,
    starter_income,
)
from excel_tools import read_uploaded_workbook, template_bytes
from groq_service import create_budget_review


AGENT_STATUS = "Budget Planner Agent"


def _initialize_state():
    defaults = {
        "income_data": starter_income(),
        "expense_data": starter_expenses(),
        "bank_data": starter_banks(),
        "budget_data": starter_budget(),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _money(value):
    return f"PKR {value:,.0f}"


def render_app():
    st.set_page_config(
        page_title="Ghar | Household Budget",
        page_icon="🏡",
        layout="wide",
    )
    _initialize_state()

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
        .stApp { background: #f5f8f5; font-family: 'DM Sans', sans-serif; }
        .block-container { max-width: 1400px; padding-top: 1.8rem; }
        [data-testid="stMetric"] {
            background: #ffffff; border: 1px solid #e2ebe5; border-radius: 16px;
            padding: 16px 18px; box-shadow: 0 5px 18px rgba(20,60,42,.05);
        }
        .hero {
            background: linear-gradient(115deg,#123d32,#1c7058,#2c8c6c);
            border-radius: 22px; padding: 28px 32px; color: white; margin: 0 0 20px;
        }
        .hero h1 { color: white; font-family: Manrope,sans-serif; margin: 0; }
        .hero p { color: #d4e9df; margin: 7px 0 0; }
        .agent {
            display: inline-block; background: #e7f4ed; color: #176148;
            padding: 7px 12px; border-radius: 999px; font-size: .82rem; font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## 🏡 Ghar")
        st.caption("Your household money, in one calm place.")
        st.markdown(
            f'<span class="agent">● Active agent: {AGENT_STATUS}</span>',
            unsafe_allow_html=True,
        )
        st.divider()
        household = st.text_input("Household name", "My Household")
        selected_month = st.date_input("Budget month", date.today().replace(day=1))
        st.caption("Currency: Pakistani rupees (PKR)")

    income = clean_frame(st.session_state.income_data, INCOME_COLUMNS, 5)
    expenses = clean_frame(st.session_state.expense_data, EXPENSE_COLUMNS, 20)
    banks = clean_frame(st.session_state.bank_data, BANK_COLUMNS, 2)
    goals = clean_frame(st.session_state.budget_data, BUDGET_COLUMNS)

    income_total = numeric_total(income, "Actual PKR")
    expected_income = numeric_total(income, "Expected PKR")
    expense_total = numeric_total(expenses, "Actual PKR")
    budget_expenses = numeric_total(expenses, "Budget PKR")
    bank_total = numeric_total(banks, "Current balance PKR")
    savings_target = numeric_total(goals, "Monthly target PKR")
    actual_savings = income_total - expense_total

    st.markdown(
        f"""
        <div class="hero">
          <h1>{household}, your monthly picture.</h1>
          <p>{selected_month.strftime("%B %Y")} · Plan with clarity, track what happened, and build savings over time.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = st.columns(4)
    cards[0].metric("Actual income", _money(income_total))
    cards[1].metric("Actual expenses", _money(expense_total))
    cards[2].metric(
        "Actual savings",
        _money(actual_savings),
        delta=f"{_money(actual_savings - savings_target)} vs savings goals",
    )
    cards[3].metric("Bank balances", _money(bank_total))

    overview_tab, income_tab, expense_tab, budget_tab, bank_tab, forecast_tab, excel_tab = st.tabs(
        [
            "Overview",
            "💰 Income",
            "🧾 Expenses",
            "🎯 Monthly budget",
            "🏦 Bank accounts",
            "📈 5-year outlook",
            "📤 Excel",
        ]
    )

    with overview_tab:
        st.subheader("Plan versus actual")
        summary = pd.DataFrame(
            {
                "Measure": ["Income", "Expenses", "Savings"],
                "Planned PKR": [
                    expected_income,
                    budget_expenses,
                    expected_income - budget_expenses,
                ],
                "Actual PKR": [
                    income_total,
                    expense_total,
                    actual_savings,
                ],
            }
        )
        st.dataframe(summary, hide_index=True, use_container_width=True)

        if savings_target > actual_savings:
            st.warning("Your savings goals are higher than this month's current surplus.")
        elif actual_savings > 0:
            st.success("You have a positive monthly surplus based on the amounts entered.")

        st.caption(
            "Data is kept in the current app session. Download the Excel workbook "
            "to keep a copy of your entries."
        )

    with income_tab:
        st.subheader("Income sources")
        st.caption("Add up to five income sources. Use expected and actual monthly amounts.")
        edited = st.data_editor(
            income,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="income_editor",
            column_config={
                "Expected PKR": st.column_config.NumberColumn("Expected PKR", min_value=0, step=1000),
                "Actual PKR": st.column_config.NumberColumn("Actual PKR", min_value=0, step=1000),
            },
        )
        st.session_state.income_data = clean_frame(edited, INCOME_COLUMNS, 5)
        if len(edited) > 5:
            st.info("The app supports up to five income sources.")

    with expense_tab:
        st.subheader("Household expenses")
        st.caption(
            "Categories are seeded with common Rawalpindi and Islamabad household costs. "
            "Edit them to suit your household."
        )
        edited = st.data_editor(
            expenses,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="expenses_editor",
            column_config={
                "Budget PKR": st.column_config.NumberColumn("Budget PKR", min_value=0, step=1000),
                "Actual PKR": st.column_config.NumberColumn("Actual PKR", min_value=0, step=1000),
            },
        )
        st.session_state.expense_data = clean_frame(edited, EXPENSE_COLUMNS, 20)
        if len(edited) > 20:
            st.info("The app supports up to twenty expense rows.")

    with budget_tab:
        st.subheader("Monthly budget and savings goals")
        st.caption("Savings goals are compared with actual savings from the income and expenses tabs.")
        edited = st.data_editor(
            goals,
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="goals_editor",
            column_config={
                "Monthly target PKR": st.column_config.NumberColumn(
                    "Monthly target PKR", min_value=0, step=1000
                )
            },
        )
        st.session_state.budget_data = clean_frame(edited, BUDGET_COLUMNS)
        st.metric("Total monthly savings goals", _money(numeric_total(edited, "Monthly target PKR")))
        st.metric("Current actual savings", _money(actual_savings))

    with bank_tab:
        st.subheader("Two bank accounts")
        st.caption("Update current balances as you check them. Record monthly deposits and withdrawals.")
        edited = st.data_editor(
            banks,
            num_rows="fixed",
            hide_index=True,
            use_container_width=True,
            key="banks_editor",
            column_config={
                "Opening balance PKR": st.column_config.NumberColumn(
                    "Opening balance PKR", min_value=0, step=1000
                ),
                "Current balance PKR": st.column_config.NumberColumn(
                    "Current balance PKR", min_value=0, step=1000
                ),
                "Monthly deposits PKR": st.column_config.NumberColumn(
                    "Monthly deposits PKR", min_value=0, step=1000
                ),
                "Monthly withdrawals PKR": st.column_config.NumberColumn(
                    "Monthly withdrawals PKR", min_value=0, step=1000
                ),
            },
        )
        st.session_state.bank_data = clean_frame(edited, BANK_COLUMNS, 2)
        st.dataframe(edited, hide_index=True, use_container_width=True)

    with forecast_tab:
        st.subheader("Five-year savings outlook")
        st.caption(
            "Estimate based on your current bank balance and a consistent monthly contribution. "
            "It does not account for inflation or changing income and expenses."
        )
        col1, col2 = st.columns(2)
        monthly_contribution = col1.number_input(
            "Monthly savings contribution (PKR)",
            min_value=0.0,
            value=max(0.0, actual_savings),
            step=1000.0,
        )
        annual_return = col2.number_input(
            "Assumed annual return (%)",
            min_value=0.0,
            max_value=30.0,
            value=0.0,
            step=0.5,
            help="Optional estimate. Keep at zero if you do not want growth included.",
        )

        projection = make_projection(
            starting_balance=bank_total,
            monthly_saving=monthly_contribution,
            annual_return=annual_return,
            years=5,
        )
        st.area_chart(
            projection.set_index("Year")["Projected balance PKR"],
            color="#1b8063",
            height=300,
        )
        st.dataframe(projection, hide_index=True, use_container_width=True)

    with excel_tab:
        st.subheader("Excel template and upload")
        st.write(
            "Download the starter workbook, fill it in Excel, then upload it here to preview its sheets."
        )

        st.download_button(
            "Download budget.xlsx",
            data=template_bytes(),
            file_name="budget.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

        uploaded = st.file_uploader(
            "Upload a completed budget workbook",
            type=["xlsx"],
        )
        if uploaded:
            try:
                sheets = read_uploaded_workbook(uploaded)
                st.success(f"Found {len(sheets)} recognized budget sheet(s).")
                for name, frame in sheets.items():
                    with st.expander(name.title()):
                        st.dataframe(frame, hide_index=True, use_container_width=True)
                st.info(
                    "This starter version previews uploaded sheets. "
                    "Copy their values into the editable tabs to update calculations."
                )
            except Exception as error:
                st.error(f"Could not read the workbook: {error}")

    st.divider()
    st.subheader("AI budget check-in")
    st.caption("Groq reviews the totals you entered. Your API key stays in Streamlit Secrets.")

    question = st.text_input(
        "What would you like help understanding?",
        "How can I make this monthly budget more realistic?",
    )

    if st.button("Review my budget with Groq", type="primary"):
        try:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            api_key = ""

        if not api_key:
            st.warning(
                "Add GROQ_API_KEY in your Streamlit app settings under Secrets."
            )
        else:
            try:
                with st.spinner("Budget Review Agent is working…"):
                    answer = create_budget_review(
                        api_key=api_key,
                        question=question,
                        monthly_income=income_total,
                        monthly_expenses=expense_total,
                        planned_savings=savings_target,
                        bank_balance=bank_total,
                    )

    def _sync_editor(editor_key, data_key, columns, limit=None):
    edited = st.session_state.get(editor_key)
    if edited is not None:
        st.session_state[data_key] = clean_frame(edited, columns, limit)
                st.markdown(answer)
            except Exception as error:
                st.error(f"Groq request failed: {error}")
