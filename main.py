import streamlit as st
import pandas as pd
import plotly.express as px
import openai

# setting up the page
st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="wide")
st.title("💰 Budget Tracker")

# setting up the site background, buttons
st.markdown("""
    <style>
    .stApp {
        background-color: #E0E0E0;
        font-family: Arial, sans-serif;
        color: #000000;
    }
    .stSidebar {
        background-color: #C0C0C0;
    }
    .stButton>button {
        border-radius: 12px;
        background-color: #4CAF50; 
        color: white;
        font-size: 16px;
    }
    .stDataFrame {
        border-radius: 10px;
    }
    .dark-theme {
        background-color: #1E1E1E;
        color: white;
    }
    .dark-theme .stSidebar {
        background-color: #333333;
    }
    </style>
    """, unsafe_allow_html=True)

# dark mode toggle
dark_mode = st.sidebar.checkbox("🌙 dark mode")
if dark_mode:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #1E1E1E;
            color: white;
        }
        .stSidebar {
            background-color: #333333;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #E0E0E0;
            color: #000000;
        }
        .stSidebar {
            background-color: #C0C0C0;
            color: #000000;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# logic for the navigation
st.sidebar.title("navigation")
cash_management_expander = st.sidebar.expander("💰 cash management", expanded=False)
property_investment_expander = st.sidebar.expander("🏠 property & investment", expanded=False)

# initialize session states
if 'active_section' not in st.session_state:
    st.session_state.active_section = "cash management"

# setting up the cash management section
with cash_management_expander:
    cash_option = st.radio("select an option:", [
        "📊 dashboard",
        "💸 initial cash input",
        "➕ add transaction",
        "💰 income tracking",
        "🎯 savings goals",
        "💼 net worth"
    ], key="cash_option")

# setting up the property & investment section
with property_investment_expander:
    property_option = st.radio("select an option:", [
        "🏠 property value",
        "💳 debt payoff",
        "🏦 mortgage calculator"
    ], key="property_option")

# initializing session states for data
if 'transactions' not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=['Date', 'Category', 'Amount'])
if 'income' not in st.session_state:
    st.session_state.income = pd.DataFrame(columns=['Date', 'Source', 'Amount'])
if 'initial_cash' not in st.session_state:
    st.session_state.initial_cash = 0.0
if 'property_value' not in st.session_state:
    st.session_state.property_value = 0.0
if 'debt' not in st.session_state:
    st.session_state.debt = 0.0

# functions for different features

# dashboard logic
def show_dashboard():
    st.header("📊 dashboard")
    total_expenses = st.session_state.transactions['Amount'].sum()
    total_income = st.session_state.income['Amount'].sum()
    net_worth = st.session_state.initial_cash + st.session_state.property_value - st.session_state.debt + total_income - total_expenses
    col1, col2, col3 = st.columns(3)
    col1.metric("total income", f"${total_income:,.2f}")
    col2.metric("total expenses", f"${total_expenses:,.2f}")
    col3.metric("net worth", f"${net_worth:,.2f}")
    st.subheader("expenses overview")
    if not st.session_state.transactions.empty:
        expense_pie = px.pie(st.session_state.transactions, names='Category', values='Amount', title='spending distribution')
        st.plotly_chart(expense_pie)
    else:
        st.write("no expenses recorded yet.")
    st.subheader("income overview")
    if not st.session_state.income.empty:
        income_pie = px.pie(st.session_state.income, names='Source', values='Amount', title='income distribution')
        st.plotly_chart(income_pie)
    else:
        st.write("no income recorded yet.")
    st.subheader("net worth over time")
    st.write("this graph could display net worth progress over time if implemented.")

# transaction input
def add_transaction():
    st.header("➕ add a new transaction")
    with st.form("transaction_form"):
        date = st.date_input("date")
        category = st.text_input("category")
        amount = st.number_input("amount", step=0.01)
        submit = st.form_submit_button("add transaction")
        if submit:
            new_transaction = pd.DataFrame([[date, category, amount]], columns=['Date', 'Category', 'Amount'])
            st.session_state.transactions = pd.concat([st.session_state.transactions, new_transaction], ignore_index=True)
            st.success("transaction added!")

# property value input
def property_value():
    st.header("🏠 property value")
    property_value = st.number_input("enter property value", step=1000.0, value=st.session_state.property_value)
    st.session_state.property_value = property_value
    st.write(f"current property value: ${property_value:,.2f}")

# debt payoff calculator
def debt_payoff():
    st.header("💳 debt payoff calculator")
    debt_amount = st.number_input("total debt", step=1000.0, value=st.session_state.debt)
    interest_rate = st.number_input("interest rate (%)", step=0.01)
    monthly_payment = st.number_input("monthly payment", step=100.0)
    st.session_state.debt = debt_amount

    if monthly_payment > 0:
        months_to_payoff = debt_amount / monthly_payment
        st.write(f"months to pay off: {months_to_payoff:.2f}")
    else:
        st.write("please enter a monthly payment greater than 0.")

# mortgage calculator
def mortgage_calculator():
    st.header("🏦 mortgage calculator")
    loan_amount = st.number_input("loan amount", step=1000.0)
    interest_rate = st.number_input("interest rate (%)", step=0.01)
    loan_term = st.number_input("loan term (years)", step=1)

    if interest_rate > 0 and loan_term > 0:
        monthly_rate = interest_rate / 100 / 12
        num_payments = loan_term * 12
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        st.write(f"estimated monthly payment: ${monthly_payment:,.2f}")
    else:
        st.write("please enter a valid interest rate and loan term.")

# income tracking
def income_tracking():
    st.header("💰 income tracking")
    with st.form("income_form"):
        date = st.date_input("date")
        source = st.text_input("income source")
        amount = st.number_input("amount", step=0.01)
        submit = st.form_submit_button("add income")

        if submit:
            new_income = pd.DataFrame([[date, source, amount]], columns=['Date', 'Source', 'Amount'])
            st.session_state.income = pd.concat([st.session_state.income, new_income], ignore_index=True)
            st.success("income added!")

# savings goals
def savings_goals():
    st.header("🎯 savings goals")
    goal_name = st.text_input("savings goal name")
    goal_amount = st.number_input("goal amount", step=100.0)
    current_savings = st.number_input("current savings", step=100.0)

    if st.button("set goal"):
        if current_savings >= goal_amount:
            st.success(f"congratulations! you've reached your goal of ${goal_amount:,.2f} for {goal_name}.")
        else:
            remaining = goal_amount - current_savings
            st.write(f"you need ${remaining:,.2f} more to reach your goal of ${goal_amount:,.2f} for {goal_name}.")

# net worth calculator
def net_worth():
    st.header("💼 net worth")
    total_income = st.session_state.income['Amount'].sum()
    total_expenses = st.session_state.transactions['Amount'].sum()
    net_worth = st.session_state.initial_cash + st.session_state.property_value - st.session_state.debt + total_income - total_expenses
    st.metric("total net worth", f"${net_worth:,.2f}")

# initial cash input
def initial_cash_input():
    st.header("💸 initial cash input")
    initial_cash = st.number_input("enter initial cash or liquid assets", step=100.0, value=st.session_state.initial_cash)
    st.session_state.initial_cash = initial_cash
    st.write(f"initial cash set: ${initial_cash:,.2f}")

# calling appropriate functions based on user selection
if cash_management_expander.expanded:
    if cash_option == "📊 dashboard":
        show_dashboard()
    elif cash_option == "💸 initial cash input":
        initial_cash_input()
    elif cash_option == "➕ add transaction":
        add_transaction()
    elif cash_option == "💰 income tracking":
        income_tracking()
    elif cash_option == "🎯 savings goals":
        savings_goals()
    elif cash_option == "💼 net worth":
        net_worth()

if property_investment_expander.expanded:
    if property_option == "🏠 property value":
        property_value()
    elif property_option == "💳 debt payoff":
        debt_payoff()
    elif property_option == "🏦 mortgage calculator":
        mortgage_calculator()

#might import as opi but ehh i guess openai will do
import openai

#api key
openai.api_key = "your_openai_api_key_here"

#sidebar
ai_assistant_expander = st.sidebar.expander("🤖 AI Finance Assistant", expanded=False)

#logic
def ai_chatbot():
    st.header("🤖 AI Finance Assistant")

    #input
    #contiue this part tmr
    user_message = st.text_input("Ask your financial question to the AI:")

    #sesh yap
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    #priv chats
    for chat in st.session_state.chat_history:
        st.write(f"You: {chat['user']}")
        st.write(f"AI: {chat['ai']}")

    #handle the sumbisions
    if st.button("Submit"):
        if user_message:
            #add user to the messgaes
            st.session_state.chat_history.append({"user": user_message, "ai": "..."})

            #call to openai api
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI financial assistant. You are only to provide financial assistance and budgeting help. These are your instructions."},
                    {"role": "user", "content": user_message}
                ]
            )

            #extract ai response
            ai_response = response['choices'][0]['message']['content'].strip()

            #update chat
            st.session_state.chat_history[-1]["ai"] = ai_response

            #display ai response
            st.write(f"AI: {ai_response}")

    #  chat history
    if st.button("Clear Chat"):
        st.session_state.chat_history = []

# dipslay
with ai_assistant_expander:
    ai_chatbot()

st.subheader("Developed/Built by Leo F")
