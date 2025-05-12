## Trading Strategy Report: Mechanical Break & Retest System

**Strategy Name:** Jdub_Trades' Boring & Simple Break and Retest Strategy

**Core Philosophy:**
The strategy is designed to be mechanical, relying on pre-defined key levels and price action reactions around them. It aims to minimize subjective decision-making and daily bias. The core idea is that once a significant level is broken, it often gets retested from the other side, providing an entry opportunity in the direction of the breakout.

**I. General Principles (Applicable to all Setups):**

1.  **Key Level Identification:** This is crucial. Levels are derived from:
    *   Opening Range (first candle of the session).
    *   Previous Day's High (PDH) / Previous Day's Low (PDL).
    *   Order Blocks (last up/down candle before a strong move).
2.  **The Break:** Price must decisively break through a key level. This should ideally be with momentum/strong candle(s).
3.  **The Retest:** After the break, price pulls back to test the *former* resistance as *new* support (for longs), or the *former* support as *new* resistance (for shorts).
4.  **Entry Confirmation:** Entry is taken *after* the retest holds, confirming the level is now acting in its new role. This could be:
    *   A specific candlestick pattern (e.g., engulfing, pin bar, hammer/shooting star) forming at the retest level.
    *   Price starting to move away from the retested level in the breakout direction.
5.  **Stop Loss:**
    *   For longs: Place slightly below the low of the retest candle or below the key level itself.
    *   For shorts: Place slightly above the high of the retest candle or above the key level itself.
    *   The stop loss should be logical and give the trade some room to breathe without invalidating the setup.
6.  **Take Profit:**
    *   Aim for a minimum Risk:Reward (R:R) of 1:2. The speaker achieved R:R multiples like 2.62, 3.73, and 6.70, indicating he often aims for much higher.
    *   Targets can be the next significant key level (e.g., next PDH/PDL, next order block, session high/low).
    *   Partial take-profits can be implemented at 1R, 2R, etc., or at subsequent key levels.
7.  **Timeframes:**
    *   **Higher Timeframe (HTF) Context:** Daily chart for PDH/PDL. Intraday 15-min or 1-hour for overall intraday trend direction.
    *   **Execution Timeframe (LTF):** 1-minute or 5-minute charts for identifying the B&R pattern and entry. (Speaker used 1-min and 5-min in examples).

**II. Specific Setups:**

**A. Opening Range Break & Retest (ORB B&R)**
    *   **Description:** Uses the high and low of the first candle of the New York trading session (9:30 AM EST).
    *   **Key Level Identification:**
        1.  At 9:30 AM EST, identify the first candle (e.g., 1-minute, 5-minute, or 15-minute – *the app needs to allow selection or define a default, e.g., first 5-min candle*).
        2.  Mark the high of this candle (Opening Range High - ORH).
        3.  Mark the low of this candle (Opening Range Low - ORL).
    *   **Long Entry (Breakout & Retest of ORH):**
        1.  Condition 1: Price breaks above ORH.
        2.  Condition 2: Price pulls back and retests ORH.
        3.  Condition 3: ORH holds as support (e.g., bullish confirmation candle forms, price moves up from ORH).
        4.  Action: Enter LONG.
        5.  Stop Loss: Below the low of the retest candle at ORH, or just below ORH.
        6.  Take Profit: Next resistance, High of Day (HOD), pre-defined R:R multiple.
    *   **Short Entry (Breakout & Retest of ORL):**
        1.  Condition 1: Price breaks below ORL.
        2.  Condition 2: Price pulls back and retests ORL.
        3.  Condition 3: ORL holds as resistance (e.g., bearish confirmation candle forms, price moves down from ORL).
        4.  Action: Enter SHORT.
        5.  Stop Loss: Above the high of the retest candle at ORL, or just above ORL.
 хрони
        6.  Take Profit: Next support, Low of Day (LOD), pre-defined R:R multiple.
    *   **Reversal Variation (False Breakout):**
        *   Example: Price breaks ORH, fails to continue, then breaks back *below* ORH. Now, ORH is treated as potential resistance. Look for a retest of ORH from below for a SHORT entry.
        *   The opposite applies for a false breakout below ORL, looking for a LONG entry on a retest of ORL from above.

**B. Previous Day High (PDH) / Previous Day Low (PDL) B&R**
    *   **Description:** Uses the previous trading day's absolute high and low as key levels. These are often strong psychological and institutional levels.
    *   **Key Level Identification:**
        1.  Identify PDH from the previous trading session.
        2.  Identify PDL from the previous trading session.
    *   **Long Entry Scenarios:**
        1.  **PDL Hold:** Price approaches PDL, holds PDL as support (confirmation), enter LONG. Stop below PDL. Target PDH or R:R.
        2.  **PDH Breakout & Retest:** Price breaks above PDH, retests PDH as support (confirmation), enter LONG. Stop below PDH. Target next resistance or R:R.
    *   **Short Entry Scenarios:**
        1.  **PDH Hold:** Price approaches PDH, holds PDH as resistance (confirmation), enter SHORT. Stop above PDH. Target PDL or R:R.
        2.  **PDL Breakout & Retest:** Price breaks below PDL, retests PDL as resistance (confirmation), enter SHORT. Stop above PDL. Target next support or R:R.

**C. Order Block (OB) B&R**
    *   **Description:** Order blocks represent areas of concentrated institutional buying or selling.
    *   **Key Level Identification:**
        1.  **Bearish OB:** The last *up-close candle* (green candle) before a significant downward price move. The zone can be the full candle range or from its low to its high (or wick to body).
        2.  **Bullish OB:** The last *down-close candle* (red candle) before a significant upward price move. The zone can be the full candle range or from its high to its low (or wick to body).
    *   **Short Entry (Bearish OB Retest):**
        1.  Context: Overall downtrend or price approaching a known resistance area.
        2.  Condition 1: Price rallies back into the identified Bearish OB zone.
        3.  Condition 2: Price shows rejection from the Bearish OB (e.g., bearish confirmation candle, stalls).
        4.  Action: Enter SHORT.
        5.  Stop Loss: Slightly above the high of the Bearish OB zone.
        6.  Take Profit: Next support, LOD, or pre-defined R:R multiple.
    *   **Long Entry (Bullish OB Retest):**
        1.  Context: Overall uptrend or price approaching a known support area.
        2.  Condition 1: Price sells off back into the identified Bullish OB zone.
        3.  Condition 2: Price shows rejection/support at the Bullish OB (e.g., bullish confirmation candle, stalls).
        4.  Action: Enter LONG.
        5.  Stop Loss: Slightly below the low of the Bullish OB zone.
        6.  Take Profit: Next resistance, HOD, or pre-defined R:R multiple.

**III. Additional Considerations for Automation:**

1.  **Market Context (Higher Timeframe Bias):**
    *   The speaker often refers to the overall market trend (e.g., "QQQ is weak"). For automation, you might consider a filter based on a longer-term moving average (e.g., 200 EMA on a 15-min or 1-hour chart) to determine the primary trend direction and only take B&R setups in that direction.
    *   Example: If 1-hour 200 EMA is trending down, prioritize short B&R setups.
2.  **Combining Setups (Confluence):**
    *   The strongest setups occur when multiple key levels align.
    *   Example (from video): PDL retest also aligns with an ORB retest. This increases the probability of the setup. The app should ideally be able to recognize if a B&R point is also a PDH/PDL or near an OB.
3.  **Entry Confirmation Specifics:**
    *   For automation, "confirmation" needs to be explicitly defined. Examples:
        *   "Price touches the retest level, then closes X pips/cents away from it in the breakout direction on the next candle."
        *   "A bullish/bearish engulfing candle forms at the retest level."
        *   "Price holds above/below the retest level for X number of candles."
4.  **Volatility/Liquidity:**
    *   The speaker mentioned increased position size due to current market volatility and liquidity. For an automated app, this is complex. Initially, it's better to use a fixed risk percentage per trade (e.g., 1% of account). Advanced versions could incorporate an ATR (Average True Range) filter to adjust position size or avoid trading in extremely low/high volatility.
5.  **Number of Trades:**
    *   The speaker takes 1-3 trades per day. An automated app might need a parameter to limit the number of trades or stop trading after a certain profit/loss for the day.

**IV. Parameters Needed for No-Code App Implementation:**

*   **Asset(s) to Trade:** (e.g., TSLA, NVDA, SPY, QQQ)
*   **Key Level Definitions:**
    *   ORB:
        *   Session start time (e.g., 9:30 AM EST).
        *   Opening range duration (e.g., first 1-min, 5-min, 15-min candle).
    *   PDH/PDL: Automatically calculated from the previous day.
    *   Order Blocks: This is the most complex to automate.
        *   Lookback period to identify OBs.
        *   Criteria for a "significant move" after an OB.
        *   Criteria for OB validity (e.g., has it been mitigated/retested too many times?). *For initial automation, might be simpler to manually input OB levels or focus on ORB and PDH/PDL first.*
*   **Breakout Criteria:**
    *   How far price must close beyond a level to be considered a break (e.g., X ticks/cents or % of ATR).
*   **Retest Criteria:**
    *   How close price must come to the broken level to be considered a retest.
*   **Entry Confirmation Rule:**
    *   Specific candle pattern at retest (if app supports this).
    *   Price moving X pips/cents from retest level.
*   **Stop Loss Placement Rule:**
    *   X ticks/cents beyond the retest candle's extreme.
    *   X ticks/cents beyond the key level itself.
*   **Take Profit Rule:**
    *   Fixed R:R multiple (e.g., 2:1, 3:1).
    *   Target next key opposing level (PDH/PDL, OB, ORH/ORL).
    *   Partial take profit levels (e.g., TP1 at 1R, TP2 at 2R).
*   **Risk Management:**
    *   Max risk per trade (e.g., 1% of account equity).
    *   Daily max loss (e.g., 3% of account equity).
    *   Daily max profit target (optional).
*   **Timeframe for Execution:** (e.g., 1-min, 5-min).
*   **HTF Trend Filter (Optional):**
    *   Moving average type and period (e.g., 200 EMA).
    *   HTF chart period (e.g., 15-min, 1-hour).

**Example Rule Logic (Long ORB B&R on 5-min chart):**

1.  `IF` Time = 9:30 AM EST
2.  `THEN` Record High (ORH) and Low (ORL) of the 9:30-9:35 AM EST candle.
3.  `IF` Current Candle Close > ORH (Breakout Confirmed)
4.  `AND IF` Price subsequently touches or comes within Y ticks of ORH (Retest)
5.  `AND IF` A bullish confirmation candle forms at ORH (e.g., closes above ORH after touching it)
6.  `THEN` Enter LONG at market.
7.  `SET` Stop Loss Z ticks below ORH.
8.  `SET` Take Profit at 2 * (Entry Price - Stop Loss Price) + Entry Price (for 2R).
