#@Leo Fratu
import streamlit as st
import pandas as pd
import plotly.express as px
from openai import OpenAI
from datetime import datetime
import hashlib
import os

st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="wide")

#git1 remb to fix the styling
def apply_styling(dark_mode):
    base_style = """
        <style>
        .stApp {
            font-family: 'Roboto', sans-serif;
        }
        .stButton>button {
            border-radius: 12px;
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #45a049;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        </style>
    """
    dark_style = """
        <style>
        .stApp {
            background-color: #2C3E50;
            color: #ECF0F1;
        }
        .stSidebar {
            background-color: #34495E;
        }
        </style>
    """
    light_style = """
        <style>
        .stApp {
            background-color: #ECF0F1;
            color: #2C3E50;
        }
        .stSidebar {
            background-color: #BDC3C7;
        }
        </style>
    """
    st.markdown(base_style, unsafe_allow_html=True)
    st.markdown(dark_style if dark_mode else light_style, unsafe_allow_html=True)

#holy grail of ding
#sidebar issue 2 github repo
def setup_sidebar():
    st.sidebar.title("Navigation")
    dark_mode = st.sidebar.checkbox("🌙 Dark Mode")
    apply_styling(dark_mode)
    finance_expander = st.sidebar.expander("💰 Finance Management", expanded=True)
    ai_assistant_expander = st.sidebar.expander("🤖 AI Finance Assistant", expanded=False)
    with finance_expander:
        option = st.radio("Select an option:", [
            "📊 Dashboard",
            "💸 Initial Cash Input",
            "💰 Transactions & Income",
            "🎯 Savings Goals",
            "💼 Net Worth",
            "🏠 Property Value",
            "💳 Debt Payoff",
            "🏦 Mortgage Calculator"
        ])
    return option, ai_assistant_expander

#session state for future can merge login and session state to be able to log and comeback
def initialize_session_states():
    default_states = {
        'transactions': pd.DataFrame(columns=['Date', 'Category', 'Amount', 'Type']),
        'initial_cash': 0.0,
        'property_value': 0.0,
        'debt': 0.0,
        'chat_history': [],
        'savings_goals': [],
        'user_authenticated': False
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

#user auth ik ik il fix the security up maybe obfusticate the code and lock it
def authenticate_user():
    st.sidebar.header("User Authentication")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == "sotogrande" and password == "admin":
            st.session_state.user_authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")

#proper error handaling
def error_detection(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            #might add a log later
    return wrapper

#dashboard
@error_detection
def show_dashboard():
    st.header("📊 Dashboard")
    expenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Expense']['Amount'].sum()
    income = st.session_state.transactions[st.session_state.transactions['Type'] == 'Income']['Amount'].sum()
    net_worth = calculate_net_worth()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"${income:,.2f}", delta=f"${income - expenses:,.2f}")
    col2.metric("Total Expenses", f"${expenses:,.2f}")
    col3.metric("Net Worth", f"${net_worth:,.2f}")
    st.subheader("Transactions Overview")
    if not st.session_state.transactions.empty:
        fig = px.pie(st.session_state.transactions, names='Category', values='Amount', title='Transaction Distribution', color='Type', color_discrete_map={'Income': 'green', 'Expense': 'red'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions recorded yet.")
    display_savings_goals()

#transactions and income
@error_detection
def transactions_and_income():
    st.header("💰 Transactions & Income")
    transaction_type = st.selectbox("Select transaction type", ["Expense", "Income"])
    with st.form("transaction_form"):
        date = st.date_input("Date", value=datetime.now())
        category = st.text_input("Category")
        amount = st.number_input("Amount", step=0.01, min_value=0.0)
        submit = st.form_submit_button("Add Transaction")
        if submit:
            if category and amount > 0:
                new_transaction = pd.DataFrame([[date, category, amount, transaction_type]], columns=['Date', 'Category', 'Amount', 'Type'])
                st.session_state.transactions = pd.concat([st.session_state.transactions, new_transaction], ignore_index=True)
                st.success(f"{transaction_type} added successfully!")
            else:
                st.error("Please enter a valid category and amount.")
    st.subheader("Recent Transactions")
    st.dataframe(st.session_state.transactions.sort_values("Date", ascending=False).head(10), use_container_width=True)

# saving goals error handaling introduced
@error_detection
def savings_goals():
    st.header("🎯 Savings Goals")
    with st.form("savings_goal_form"):
        goal_name = st.text_input("Savings goal name")
        goal_amount = st.number_input("Goal amount", step=100.0, min_value=0.0)
        current_savings = st.number_input("Current savings", step=100.0, min_value=0.0)
        submit = st.form_submit_button("Set Goal")
        if submit:
            if goal_name and goal_amount > 0:
                st.session_state.savings_goals.append({
                    "name": goal_name,
                    "amount": goal_amount,
                    "current": current_savings
                })
                st.success(f"Savings goal '{goal_name}' set successfully!")
            else:
                st.error("Please enter a valid goal name and amount.")
    display_savings_goals()

@error_detection
def display_savings_goals():
    if st.session_state.savings_goals:
        st.subheader("Your Savings Goals")
        for goal in st.session_state.savings_goals:
            progress = min(goal["current"] / goal["amount"], 1.0)
            st.write(f"{goal['name']}: ${goal['current']:,.2f} / ${goal['amount']:,.2f}")
            st.progress(progress)
    else:
        st.info("No savings goals set. Add a goal to track your progress!")

# net worth calc
@error_detection
def net_worth():
    st.header("💼 Net Worth")
    net_worth = calculate_net_worth()
    st.metric("Total Net Worth", f"${net_worth:,.2f}", delta=f"${net_worth - st.session_state.initial_cash:,.2f}")

def calculate_net_worth():
    expenses = st.session_state.transactions[st.session_state.transactions['Type'] == 'Expense']['Amount'].sum()
    income = st.session_state.transactions[st.session_state.transactions['Type'] == 'Income']['Amount'].sum()
    return st.session_state.initial_cash + st.session_state.property_value - st.session_state.debt + income - expenses

#cash input
@error_detection
def initial_cash_input():
    st.header("💸 Initial Cash Input")
    initial_cash = st.number_input("Enter initial cash or liquid assets", step=100.0, value=st.session_state.initial_cash, min_value=0.0)
    st.session_state.initial_cash = initial_cash
    st.write(f"Initial cash set: ${initial_cash:,.2f}")

@error_detection
def property_value():
    st.header("🏠 Property Value")
    property_value = st.number_input("Enter property value", step=1000.0, value=st.session_state.property_value, min_value=0.0)
    st.session_state.property_value = property_value
    st.write(f"Current property value: ${property_value:,.2f}")

#value calc
@error_detection
def debt_payoff():
    st.header("💳 Debt Payoff Calculator")
    debt_amount = st.number_input("Total debt", step=1000.0, value=st.session_state.debt, min_value=0.0)
    interest_rate = st.number_input("Interest rate (%)", step=0.01, min_value=0.0)
    monthly_payment = st.number_input("Monthly payment", step=100.0, min_value=0.0)
    st.session_state.debt = debt_amount
    if monthly_payment > 0:
        months_to_payoff = calculate_months_to_payoff(debt_amount, interest_rate, monthly_payment)
        total_interest = calculate_total_interest(debt_amount, months_to_payoff, monthly_payment)
        st.write(f"Months to pay off: {months_to_payoff:.2f}")
        st.write(f"Total interest paid: ${total_interest:.2f}")
    else:
        st.warning("Please enter a monthly payment greater than 0.")

def calculate_months_to_payoff(debt_amount, interest_rate, monthly_payment):
    monthly_rate = interest_rate / 100 / 12
    if monthly_rate == 0:
        return debt_amount / monthly_payment
    return -1 * (math.log(1 - debt_amount * monthly_rate / monthly_payment) / math.log(1 + monthly_rate))

def calculate_total_interest(debt_amount, months_to_payoff, monthly_payment):
    return (months_to_payoff * monthly_payment) - debt_amount

#mortage calculator might remove later on
@error_detection
def mortgage_calculator():
    st.header("🏦 Mortgage Calculator")
    loan_amount = st.number_input("Loan amount", step=1000.0, min_value=0.0)
    interest_rate = st.number_input("Interest rate (%)", step=0.01, min_value=0.0)
    loan_term = st.number_input("Loan term (years)", step=1, min_value=1)
    if interest_rate > 0 and loan_term > 0:
        monthly_payment = calculate_monthly_mortgage_payment(loan_amount, interest_rate, loan_term)
        st.write(f"Estimated monthly payment: ${monthly_payment:,.2f}")
    else:
        st.warning("Please enter a valid interest rate and loan term.")

def calculate_monthly_mortgage_payment(loan_amount, interest_rate, loan_term):
    monthly_rate = interest_rate / 100 / 12
    num_payments = loan_term * 12
    return loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)

#chatbot (rember to hide the api key)
@error_detection
def ai_chatbot():
    st.header("🤖 AI Finance Assistant")
    user_message = st.text_input("Ask your financial question to the AI:")
    for chat in st.session_state.chat_history:
        st.text(f"You: {chat['user']}")
        st.text(f"AI: {chat['ai']}")
    if st.button("Submit"):
        if user_message:
            st.session_state.chat_history.append({"user": user_message, "ai": "..."})
            try:
                response = get_ai_response(user_message)
                ai_response = response.choices[0].message.content.strip()
                st.session_state.chat_history[-1]["ai"] = ai_response
                st.text(f"AI: {ai_response}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.chat_history[-1]["ai"] = "Error occurred. Please try again."
    if st.button("Clear Chat"):
        st.session_state.chat_history = []

def get_ai_response(user_message):
    client = OpenAI()
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI financial assistant. You are only to provide financial assistance and budgeting help."},
            {"role": "user", "content": user_message}
        ]
    )

# Main function
def main():
    initialize_session_states()

    if not st.session_state.user_authenticated:
        authenticate_user()

    if st.session_state.user_authenticated:
        option, ai_assistant_expander = setup_sidebar()

        if option == "📊 Dashboard":
            show_dashboard()
        elif option == "💸 Initial Cash Input":
            initial_cash_input()
        elif option == "💰 Transactions & Income":
            transactions_and_income()
        elif option == "🎯 Savings Goals":
            savings_goals()
        elif option == "💼 Net Worth":
            net_worth()
        elif option == "🏠 Property Value":
            property_value()
        elif option == "💳 Debt Payoff":
            debt_payoff()
        elif option == "🏦 Mortgage Calculator":
            mortgage_calculator()

        if ai_assistant_expander.expanded:
            ai_chatbot()

        st.sidebar.text("Developed by Leo Fratu")

    else:
        st.warning("Please log in to access the Budget Tracker.")

#remb to to imrpovde code next time
if __name__ == "__main__":
    main()



#features still to add:
#1. add a login system /dome
#2. add a way to export the data to a file
#3. add a way to import the data from a file
#4. add a way to delete a transaction
#5. add a way to edit a transaction
#6. add a way to categorize the transactions
#7. add a way to see the transactions in a table
#8. add a way to see the transactions in a chart
#9. add a way to see the transactions in a map  \

