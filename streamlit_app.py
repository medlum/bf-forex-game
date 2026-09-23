import streamlit as st
import pandas as pd
from streamlit_marquee import streamlit_marquee

#==========================================
# 1. GAME DATA & CONFIGURATION
#==========================================

EXCHANGE_RATES = {
    1: {'SGD': 1.35, 'EUR': 0.90, 'JPY': 160},
    2: {'SGD': 1.32, 'EUR': 0.91, 'JPY': 160},
    3: {'SGD': 1.33, 'EUR': 0.90, 'JPY': 148},
    4: {'SGD': 1.31, 'EUR': 0.91, 'JPY': 150},
    5: {'SGD': 1.27, 'EUR': 0.93, 'JPY': 153}
}

DAILY_SCENARIOS = {
    1: {
        "Event": "Market Open",
        "Hint": "Given Day 1 & 2 rates, buying EUR or SGD yields a profit."
    },
    2: {
        "Event": "Japan Central Bank plans to hike interest rates on Day 3.",
        "Hint": "Higher rates attract foreign capital. Focus on buying JPY."
    },
    3: {
        "Event": "US, EU, and Japan likely to report negative GDP figures due to tariffs.",
        "Hint": "Slowing economy reduces investor confidence. SGD is the safest haven."
    },
    4: {
        "Event": "Singapore announces an increase in the NEER policy slope for Day 5.",
        "Hint": "SGD is likely to appreciate due to strengthening monetary policy."
    },
    5: {
        "Event": "Final Trading Day!",
        "Hint": "Convert all remaining foreign currency back to USD to calculate final profits."
    }
}

#==========================================
# 2. PAGE CONFIG
#==========================================

st.set_page_config(
    page_title="BF Forex Game - Central Bank",
    layout="wide"
)

#==========================================
# 3. SESSION STATE INITIALIZATION
#==========================================

if 'teams' not in st.session_state:
    st.session_state.teams = {}

if 'transactions' not in st.session_state:
    st.session_state.transactions = []

if 'current_day' not in st.session_state:
    st.session_state.current_day = 1

# Day 5 celebration states
if 'day5_completed' not in st.session_state:
    st.session_state.day5_completed = False

if 'day5_popup_open' not in st.session_state:
    st.session_state.day5_popup_open = False

if 'day5_balloon_shown' not in st.session_state:
    st.session_state.day5_balloon_shown = False

#==========================================
# 4. HELPER FUNCTIONS
#==========================================

def calculate_trade(day, from_curr, amount, to_curr):
    """
    Calculates trade ensuring all non-USD trades go through USD.
    """
    rate_from = EXCHANGE_RATES[day].get(from_curr, 1.0)
    rate_to = EXCHANGE_RATES[day].get(to_curr, 1.0)

    # Step 1: Convert to USD
    if from_curr == 'USD':
        usd_amount = amount
    else:
        usd_amount = amount / rate_from

    # Step 2: Convert USD to Target
    if to_curr == 'USD':
        final_amount = usd_amount
    else:
        final_amount = usd_amount * rate_to

    return usd_amount, final_amount


def get_net_worth_usd(team_balances, day):
    """
    Calculates total portfolio value in USD for the current day.
    """
    usd = team_balances['USD']
    sgd = team_balances['SGD'] / EXCHANGE_RATES[day]['SGD']
    eur = team_balances['EUR'] / EXCHANGE_RATES[day]['EUR']
    jpy = team_balances['JPY'] / EXCHANGE_RATES[day]['JPY']

    return usd + sgd + eur + jpy


def get_day5_standings():
    """
    Calculates final standings using Day 5 rates.

    Returns:
        standings: list of dictionaries for leaderboard display
        winners: list of winning team names
        best: highest final USD net worth
    """
    if not st.session_state.teams:
        return [], [], 0.0

    standings = []

    for team, balances in st.session_state.teams.items():
        net_worth = round(get_net_worth_usd(balances, 5), 2)
        profit_loss = round(net_worth - 1000.0, 2)

        standings.append({
            "Team": team,
            "Net Worth (USD)": net_worth,
            "Profit/Loss (USD)": profit_loss
        })

    standings.sort(key=lambda x: x["Net Worth (USD)"], reverse=True)

    best = standings[0]["Net Worth (USD)"]

    # Supports ties: all teams with the same highest net worth are winners
    winners = [
        row["Team"]
        for row in standings
        if row["Net Worth (USD)"] == best
    ]

    return standings, winners, best


@st.dialog("🏆 Day 5 Final Results")
def show_day5_winner_dialog():
    """
    Popup dialog showing winning team(s).
    Supports one winner or multiple tied winners.
    """
    standings, winners, best = get_day5_standings()

    if not winners:
        st.info("No teams available yet.")
        if st.button("Close", key="close_no_teams_dialog"):
            st.session_state.day5_popup_open = False
            st.rerun()
        return

    if len(winners) == 1:
        st.success(f"🎉 Congratulations {winners[0]}! You are the winning team!")
    else:
        st.success(f"🎉 It's a tie! Congratulations to all {len(winners)} winning teams!")

    st.markdown("### Winning team(s)")

    for team in winners:
        st.markdown(f"- **{team}** — USD {best:,.2f}")

    with st.expander("Full final leaderboard", expanded=False):
        leaderboard_df = pd.DataFrame(standings)
        st.dataframe(
            leaderboard_df,
            hide_index=True,
            use_container_width=True
        )

    if st.button("Close", key="close_winner_dialog"):
        st.session_state.day5_popup_open = False
        st.rerun()


#==========================================
# 5. SIDEBAR: HELPER CONTROL PANEL
#==========================================

with st.sidebar:
    st.title("⚙️ Helper Control Panel")

    # Day Selector
    st.session_state.current_day = st.selectbox(
        "Select Current Game Day",
        options=[1, 2, 3, 4, 5],
        index=st.session_state.current_day - 1
    )

    st.markdown("---")

    # Add New Team
    st.subheader("➕ Add New Team")

    new_team_name = st.text_input("Team Name", key="new_team")

    if st.button("Add Team"):
        if new_team_name and new_team_name not in st.session_state.teams:
            st.session_state.teams[new_team_name] = {
                'USD': 1000.0,
                'SGD': 0.0,
                'EUR': 0.0,
                'JPY': 0.0
            }
            st.success(f"Team '{new_team_name}' added with $1,000 USD!")
            st.rerun()

        elif new_team_name in st.session_state.teams:
            st.error("Team already exists!")

        elif not new_team_name:
            st.warning("Please enter a team name.")

    st.markdown("---")

    # Execute Trade
    st.subheader("💱 Execute Trade")

    day = st.session_state.current_day

    # Safety check: ensure at least one team exists before showing trade options
    team_options = list(st.session_state.teams.keys())

    if not team_options:
        st.warning("⚠️ Please add at least one team above to start trading.")
    else:
        selected_team = st.selectbox("Team", team_options)

        team_bal = st.session_state.teams[selected_team]

        # Filter currencies that the team actually has > 0
        available_from = [
            curr for curr in ['USD', 'SGD', 'EUR', 'JPY']
            if team_bal[curr] > 0
        ]

        if not available_from:
            st.info("This team has no currency to sell.")
        else:
            from_curr = st.selectbox("Sell Currency", available_from)

            # Calculate max amount they can sell
            max_amount = team_bal[from_curr]

            amount_to_sell = st.number_input(
                f"Amount to Sell (Max: {max_amount:.2f})",
                min_value=0.0,
                max_value=max_amount,
                step=10.0,
                key=f"sell_amount_{selected_team}_{from_curr}_{day}"
            )

            # Filter target currencies: cannot buy what they are selling
            available_to = [
                curr for curr in ['USD', 'SGD', 'EUR', 'JPY']
                if curr != from_curr
            ]

            to_curr = st.selectbox("Buy Currency", available_to)

            if st.button("🚀 EXECUTE TRADE", type="primary", use_container_width=True):
                if amount_to_sell > 0:
                    intermediate_usd, final_amount = calculate_trade(
                        day,
                        from_curr,
                        amount_to_sell,
                        to_curr
                    )

                    # Update balances
                    st.session_state.teams[selected_team][from_curr] -= amount_to_sell
                    st.session_state.teams[selected_team][to_curr] += final_amount

                    # Log transaction
                    st.session_state.transactions.append({
                        'Day': day,
                        'Team': selected_team,
                        'Sold': f"{amount_to_sell:.2f} {from_curr}",
                        'Intermediate USD': f"${intermediate_usd:.2f}",
                        'Bought': f"{final_amount:.2f} {to_curr}",
                        'Rates Used': (
                            f"{from_curr}:{EXCHANGE_RATES[day].get(from_curr, '-')}, "
                            f"{to_curr}:{EXCHANGE_RATES[day].get(to_curr, '-')}"
                        )
                    })

                    st.success(f"Trade Executed! Received {final_amount:.2f} {to_curr}")
                    st.rerun()
                else:
                    st.error("Please enter a valid amount.")

    # Day 5 Completion / Winner Reveal
    if st.session_state.current_day == 5:
        st.markdown("---")
        st.subheader("🏁 Finish Day 5")

        if not st.session_state.teams:
            st.info("Add at least one team before completing the game.")

        elif not st.session_state.day5_completed:
            if st.button(
                "Complete Day 5 & Reveal Winners",
                type="primary",
                use_container_width=True
            ):
                st.session_state.day5_completed = True
                st.session_state.day5_popup_open = True
                st.session_state.day5_balloon_shown = False
                st.rerun()

        else:
            if st.button(
                "🏆 Show Winners Again",
                use_container_width=True
            ):
                st.session_state.day5_popup_open = True

                # Optional:
                # If you want balloons to appear every time "Show Winners Again"
                # is clicked, uncomment the next line.
                # st.session_state.day5_balloon_shown = False

                st.rerun()

    st.markdown("---")

    # Reset Entire Game
    if st.button("🔄 RESET ENTIRE GAME", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()


#==========================================
# 6. MAIN AREA: LIVE PROJECTION DASHBOARD
#==========================================

st.title("📈 Forex Trading Game - Live Dashboard")

day = st.session_state.current_day

#------------------------------------------
# 6.1 Scenario & Rates Display
#------------------------------------------

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📢 Day {day} Market Scenario")

    event_text = DAILY_SCENARIOS[day].get('Event', '')
    hint_text = DAILY_SCENARIOS[day].get('Hint', '')

    marquee_content = f"""
    <span style="
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 20px;
        font-weight: 600;
    ">
    📰 EVENT: {event_text} | 💡 MARKET HINT: {hint_text}
    </span>
    """

    streamlit_marquee(
        content=marquee_content,
        background="#0e1117",
        color="#29b5e8",
        width=1000,
        height="60px",
        pause_on_hover=True,
        animation_duration="25s",
    )

with col2:
    st.subheader(f"💱 Day {day} Exchange Rates")

    rates_df = pd.DataFrame.from_dict(
        EXCHANGE_RATES[day],
        orient='index',
        columns=['Rate (per 1 USD)']
    )

    rates_df.index.name = 'Currency'

    st.dataframe(
        rates_df,
        use_container_width=True
    )

st.markdown("---")

#------------------------------------------
# 6.2 Live Team Holdings Dashboard
#------------------------------------------

st.subheader("🏦 Central Bank: Live Team Portfolios")

dashboard_data = []

for team, balances in st.session_state.teams.items():
    net_worth = get_net_worth_usd(balances, day)
    profit_loss = net_worth - 1000.0

    if profit_loss >= 0:
        profit_display = f"+${profit_loss:,.2f}"
    else:
        profit_display = f"-${abs(profit_loss):,.2f}"

    dashboard_data.append({
        'Team': team,
        'USD': f"${balances['USD']:,.2f}",
        'SGD': f"${balances['SGD']:,.2f}",
        'EUR': f"€{balances['EUR']:,.2f}",
        'JPY': f"¥{balances['JPY']:,.0f}",
        'Total Net Worth (USD)': f"${net_worth:,.2f}",
        'Profit/Loss (USD)': profit_display
    })

# Safety check: only render the table if there are teams to display
if dashboard_data:
    df_dashboard = pd.DataFrame(dashboard_data)

    st.dataframe(
        df_dashboard,
        column_config={
            'Team': st.column_config.TextColumn('Team', width='small'),
            'Total Net Worth (USD)': st.column_config.TextColumn('Total Net Worth (USD)', width='medium'),
            'Profit/Loss (USD)': st.column_config.TextColumn('Profit/Loss (USD)', width='medium')
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("👈 No teams added yet. Use the sidebar to add teams as they arrive.")

st.markdown("---")

#------------------------------------------
# 6.3 Transaction History
#------------------------------------------

st.subheader("📜 Transaction History")

if st.session_state.transactions:
    df_history = pd.DataFrame(st.session_state.transactions)
    st.dataframe(
        df_history,
        hide_index=True,
        use_container_width=True
    )
else:
    st.caption("No trades executed yet.")


#==========================================
# 7. DAY 5 CELEBRATION LOGIC
#==========================================

# Reset celebration state if user navigates away from Day 5
if st.session_state.current_day != 5:
    st.session_state.day5_completed = False
    st.session_state.day5_popup_open = False
    st.session_state.day5_balloon_shown = False

# Show balloons and winner popup after Day 5 is completed
if (
    st.session_state.current_day == 5
    and st.session_state.day5_completed
    and st.session_state.day5_popup_open
):
    if not st.session_state.day5_balloon_shown:
        st.balloons()
        st.session_state.day5_balloon_shown = True

    show_day5_winner_dialog()