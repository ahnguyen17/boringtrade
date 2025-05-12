**Project Title:**  
Break & Retest Trading Bot (Boring & Simple Mechanical Edition)

**Prepared By:**  
Andy Nguyen

**Date:**  
5/11/25

---

## Section 1: The Big Picture - What is this program all about?

**1. Elevator Pitch:**  
This is a fully automated trading bot that implements the exact mechanical break and retest system from Jdub_Trades’ YouTube strategy. It identifies key price levels (like previous day high/low, opening range, and order blocks), detects breakouts and retests, automates entries/exits, monitors your market positions, and works with major brokerage APIs. The bot handles profit-taking, stop outs, tracks positions for the user, and sends detailed trade notifications and performance logs.

**2. Problem Solver:**  
The bot eliminates manual, biased decision-making in trading. It executes strategies exactly as defined, saving screen time and enforcing strict discipline, increasing the consistency and reliability of trading results.

**3. Why Does This Need to Exist?**  
It improves the consistency of trading, reduces missed opportunities, cuts screen time, prevents emotional mistakes, and documents all trade outcomes automatically. Its automation brings powerful strategies to users who may not code or want to babysit charts.

---

## Section 2: The Users - Who is this program for?

**1. Primary Users:**  
Retail traders, algorithmic or mechanical system traders, active investors using tastytrade or Schwab, people who want hands-off but rule-based trading.

**2. User Goals:**  
1. Automate a proven break & retest strategy  
2. Get notified on every trade and see each profit/loss  
3. Adjust number of contracts/positions traded  
4. Safely “flatten” (exit all trades instantly in emergencies)  
5. Limit daily trades and risk as per their plan

---

## Section 3: The Features - What can the program do?

**1. Core Actions:**  
- Connect securely to tastytrade API or Charles Schwab API  
- Select one or multiple trading strategies (ORB, PDH/PDL, OB), and select assets (e.g., TSLA, SPY)  
- Configure key strategy details (entry criteria, R:R, stop/take-profit, contract size, max trades, session times, etc.)  
- Continuously monitor market data for break/retest setups  
- Enter/exit positions automatically as strategy dictates  
- Dynamically manage stop-loss, profit targets, and partial exits  
- Immediate user notifications on trade entries, exits, profits, and losses  
- Option to instantly Flatten All (close every live position)  
- Maintain trade history and daily summaries  
- Filters for HTF trend, confluence, daily limits  
- Optionally, allow manual OB marking/input, for initial version  
- User dashboard to monitor system status, trade logs, P/L, and tweak settings  

**2. Key Feature Deep Dive: Automated Break & Retest Execution for Opening Range**

1. User selects asset (e.g., SPY), specifies opening range timeframe (e.g., first 5-min candle at 9:30am), sets their trade risk, desired contracts, and R:R.
2. At 9:30am, bot marks opening range high/low.
3. Bot monitors for a candle close above (or below) the range.  
4. If price breaks out, then pulls back to retest the level (coming within user-defined number of ticks/cents), bot waits for confirmation candle (e.g., bullish if break above) at the retest.
5. If confirmation present, bot instantly enters trade (LONG or SHORT as appropriate).
6. Places stop-loss just below/above key level or retest candle (per user setting).
7. Sets take-profit according to risk ratio or next key level.
8. Notifies user: (“Entered LONG 2 contracts SPY at 380.43; stop 379.95; TP 382.10 [2R].”)
9. On trade close (for profit or loss), notifies user and logs details.

---

## Section 4: The Information - What does it need to handle?

**1. Information Needed:**  
- User login & encrypted brokerage API keys  
- Asset(s) and markets to trade  
- Key levels (ORB H/L, PDH, PDL, manually input OBs)  
- Market price, volume, candle OHLC data  
- User settings for strategy parameters (risk, contracts, timeframes, confirmation rules, etc.)  
- Trade orders: entry/exit price, timestamp, order status  
- P&L per trade and daily summary  
- Notifications log  
- Max trades per day, max loss/profit per day  
- User-flagged order blocks (optional/manual for now)  
- Current market status (open, closed, trading hours)

**2. Data Relationships:**  
A user has multiple strategies and assets. Each asset/strategy pair has its own log of trades (with levels, entries, exits, P/L, timestamps, signals used). User risk/daily limits settings apply across all trades.

---

## Section 5: The Look & Feel - How should it generally seem?

**1. Overall Style:**  
Professional & Minimal; Clear dashboard, actionable notifications, simple settings interface, “trader-friendly” feedback.

**2. Similar Programs (Appearance):**  
Tradovate dashboard, NinjaTrader control panel, TradingView alerts UI.

---

## Section 6: The Platform - Where will it be used?

**1. Primary Environment:**  
[X] On a Website (browser dashboard)  
[X] As a Computer Program (standalone for desktop, optional)  
[ ] Mobile (secondary; mainly for push notifications)

**2. Offline Mode Needed?**  
No (requires live market data and active brokerage connectivity)

---

## Section 7: The Rules & Boundaries - What are the non-negotiables?

**Must-Have Rules:**  
- Never exceed user-set risk/trade, number of trades/positions, or daily loss limits  
- Never execute a trade unless all strategy conditions are truly met  
- All user credentials and private data must be encrypted  
- Flatten All must override all strategy logic immediately

**Things to Avoid:**  
- Never “double dip” same level without a clearly new trigger  
- Never hold positions overnight (if day-trade mode enabled)  
- Never place live trades unless bot is enabled and user has approved all settings

---

## Section 8: Success Criteria

**Definition of Done:**  
1. After setup, bot connects to tastytrade/Schwab, marks opening range, and enters/exits trades, fully notifying user, as strategy details require.  
2. If bot is running and a stop-out or profit is hit, it closes the position, updates P/L, and notifies instantly.  
3. “Flatten All” closes every open trade, cancels all working orders, and confirms to the user immediately.

---

## Section 9: Inspirations & Comparisons

**Similar Programs (Functionality):**  
Tradovate, NinjaTrader, 3Commas, TradingView PineScript bots, QuantConnect

**Likes:**  
- TradingView’s simple alert interface  
- NinjaTrader’s robust automation and clear logs  
- Tradovate’s instant trade feedback  
**Dislikes:**  
- Cluttered, overly complex dashboards  
- Overly broad notifications (“something happened”) instead of specifics  
- Hard to set up risk or trade controls

---

## Section 10: Future Dreams (Optional)

**Nice-to-Haves:**  
- Full visual statistics/analytics on win rates per setup/level  
- Automated order block detection/marking  
- AI-based “trade quality” scoring  
- Backtesting on historical market data  
- Multi-broker support (IBKR, E*Trade, etc.)

**Long-Term Vision:**  
Enable social/shared strategy frameworks; create a community marketplace for bots or strategies using the Jdub method or others.

---

## Section 11: Technical Preferences (Optional)

**Specific API Requirements:**  
- Must support both tastytrade and Charles Schwab APIs for live trading  
- Codebase should be modular for future broker integrations

**Technical Notes:**  
No preference on coding language—whichever best fits API/documentation/robustness.  
All trade logic must be testable by simulation mode first.

---

