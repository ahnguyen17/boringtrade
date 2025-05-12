# Futures Trading with BoringTrade

This document provides information about trading futures contracts with BoringTrade.

## Supported Futures Contracts

BoringTrade currently supports the following futures contracts:

- **ES**: E-mini S&P 500 Futures
  - Exchange: CME
  - Tick Size: 0.25
  - Multiplier: $50 per point
  - Margin Requirement: ~$12,000 (varies by broker)

- **MES**: Micro E-mini S&P 500 Futures
  - Exchange: CME
  - Tick Size: 0.25
  - Multiplier: $5 per point
  - Margin Requirement: ~$1,200 (varies by broker)

## Configuration

Futures trading can be configured in the `config.py` file:

```python
# Futures trading settings
"futures": {
    "enabled": True,
    "default_contract_size": 1,  # Number of contracts to trade
    "use_continuous_contracts": True,  # Use continuous contracts for historical data
    "rollover_days_before_expiration": 5,  # Days before expiration to roll over
    "contracts": {
        "ES": {
            "description": "E-mini S&P 500 Futures",
            "exchange": "CME",
            "tick_size": 0.25,
            "multiplier": 50.0,  # $50 per point
            "margin_requirement": 12000.0,  # Approximate initial margin
        },
        "MES": {
            "description": "Micro E-mini S&P 500 Futures",
            "exchange": "CME",
            "tick_size": 0.25,
            "multiplier": 5.0,  # $5 per point
            "margin_requirement": 1200.0,  # Approximate initial margin
        },
    },
},
```

## Trading Futures

To trade futures contracts, simply add the futures symbols to your assets list:

```python
"assets": ["SPY", "QQQ", "AAPL", "TSLA", "NVDA", "ES", "MES"],
```

The system will automatically detect that these are futures contracts and apply the appropriate settings.

## Risk Management for Futures

When trading futures, the risk management system takes into account the contract multiplier. For example:

- For ES, a 1-point move is worth $50
- For MES, a 1-point move is worth $5

The position sizing algorithm will calculate the appropriate number of contracts based on your risk parameters and the contract specifications.

## Trading Hours

Futures contracts have different trading hours than stocks. The E-mini S&P 500 futures (ES and MES) trade almost 24 hours a day, 5 days a week, with a brief maintenance period.

- Regular Trading Hours: 9:30 AM - 4:15 PM ET
- Extended Trading Hours: 6:00 PM - 5:00 PM ET (next day)

## Contract Expiration

Futures contracts expire on a regular schedule. The system can be configured to automatically roll over to the next contract before expiration.

The `rollover_days_before_expiration` setting determines how many days before expiration the system will roll over to the next contract.

## Broker Support

Not all brokers support futures trading. Make sure your broker account is set up for futures trading before attempting to trade futures contracts.

## Strategies

All the existing strategies (ORB, PDH/PDL, OB) work with futures contracts. The system will automatically apply the appropriate settings based on the contract specifications.

## Example: Trading MES with ORB Strategy

The Micro E-mini S&P 500 (MES) is a good starting point for futures trading due to its smaller contract size and lower margin requirements.

To trade MES with the Opening Range Breakout (ORB) strategy:

1. Add "MES" to your assets list
2. Enable the ORB strategy
3. Configure the ORB strategy parameters as needed
4. Run the bot

The system will automatically detect that MES is a futures contract and apply the appropriate settings.

## Considerations for Futures Trading

- **Leverage**: Futures contracts are leveraged instruments. A small move in the underlying index can result in a large profit or loss.
- **Margin Requirements**: Futures contracts require margin. Make sure you have sufficient funds in your account.
- **Overnight Risk**: If you hold futures contracts overnight, you are exposed to gap risk.
- **Contract Rollover**: Futures contracts expire. Make sure you understand the rollover process.
- **Tax Implications**: Futures contracts have different tax treatment than stocks. Consult a tax professional.

## Adding New Futures Contracts

To add support for additional futures contracts, update the `futures.contracts` section in the configuration file with the appropriate contract specifications.

You can also add new contracts to the `COMMON_ASSETS` dictionary in `models/asset.py`.
