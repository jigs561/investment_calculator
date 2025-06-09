import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("Dividend Reinvestment Calculator")

# User Inputs
ticker = st.text_input("Stock Ticker (e.g., vgs.ax)", "vgs.ax").lower()
period = st.selectbox("Investment Period", options=["1y", "2y", "5y", "10y", "ytd", "max"], index=1)
monthly_contribution = st.number_input("Monthly Contribution ($)", min_value=0, value=1000, step=100)

# Fetch and calculate when the button is clicked
if st.button("Calculate"):
    df = yf.Ticker(ticker).history(period=period, interval="1mo")
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df['Dividends'] = pd.to_numeric(df['Dividends'], errors='coerce')
    df['Close'] = df['Close'].fillna(method='ffill')

    df['cumulative_shares'] = 0.0
    df['investment_amount'] = float(monthly_contribution)
    df['shares_bought'] = 0.0

    for i in range(len(df)):
        if i == 0:
            price = float(df.iloc[i]['Close'])
            df.at[df.index[i], 'shares_bought'] = monthly_contribution / price
            df.at[df.index[i], 'cumulative_shares'] = df.at[df.index[i], 'shares_bought']
        else:
            dividend_amount = df.iloc[i]['Dividends'] * df.iloc[i-1]['cumulative_shares']
            total_investment = monthly_contribution + dividend_amount
            price = float(df.iloc[i]['Close'])
            df.at[df.index[i], 'investment_amount'] = total_investment
            df.at[df.index[i], 'shares_bought'] = total_investment / price
            df.at[df.index[i], 'cumulative_shares'] = df.iloc[i-1]['cumulative_shares'] + df.iloc[i]['shares_bought']

    current_price = yf.Ticker(ticker).history(period="1d", interval="1d").iloc[-1]['Close']
    total_shares = df['cumulative_shares'].iloc[-1]
    total_value = total_shares * current_price
    total_contribution = monthly_contribution * len(df)
    total_dividends = (df['Dividends'] * df['cumulative_shares'].shift(1)).fillna(0).sum()

    col1, col2 = st.columns(2)

    with col1:
        fig1, ax1 = plt.subplots(figsize=(8, 5))
        ax1.plot(df.index, df['cumulative_shares'], label='Cumulative Shares')
        ax1.set_title("Cumulative Shares Over Time")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Shares")
        ax1.grid(True, linestyle="--", alpha=0.7)
        ax1.text(0.05, 0.95, f'Total Shares: {total_shares:.2f}\nTotal Value: ${total_value:,.2f}',
            transform=ax1.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        st.pyplot(fig1)

    with col2:
        fig2, ax2 = plt.subplots(figsize=(8, 5))
        ax2.plot(df.index, df['Close'], label='Price', color='green')
        ax2.set_title("Stock Price Over Time")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Price")
        ax2.grid(True, linestyle="--", alpha=0.7)
        ax2.text(0.05, 0.95, f'Total Contribution: ${total_contribution:,.2f}\nTotal Dividends Reinvested: ${total_dividends:,.2f}',
            transform=ax2.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        st.pyplot(fig2)
    # 1. Average cost per share
    avg_cost_per_share = total_contribution / total_shares if total_shares > 0 else 0

    # 2. Total dividends received in the last year
    one_year_ago = df.index[-1] - pd.DateOffset(years=1)
    df_last_year = df[df.index >= one_year_ago]
    dividends_last_year = df_last_year['Dividends'] * df_last_year['cumulative_shares'].shift(1)
    dividends_last_year = dividends_last_year.fillna(0).sum()

    st.subheader("Summary") 
    st.write(f"📈 **Total Shares Accumulated**: {total_shares:.2f}")
    st.write(f"💰 **Total Portfolio Value**: ${total_value:,.2f}")
    st.write(f"💸 **Total Contribution**: ${total_contribution:,.2f}")
    st.write(f"🔁 **Total Dividends Reinvested**: ${total_dividends:,.2f}")
    st.write(f"💵 **Average Cost per Share**: ${avg_cost_per_share:,.2f}")
    st.write(f"📅 **Dividends Paid in the Last Year**: ${dividends_last_year:,.2f}")
    st.write(f"📊 **Total Return**: ${total_value - total_contribution:,.2f} ({(total_value / total_contribution - 1) * 100:.2f}%)")
    st.dataframe(df.iloc[::-1])
