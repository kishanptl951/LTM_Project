# SEC Corpus Data Storage Convention

This directory caches machine-readable XBRL JSON facts and raw HTML filings pulled from SEC EDGAR.

## Directory Layout Structure

```text
data/sec_corpus/
└── {TICKER}/                           # Upper-case Ticker symbol (e.g. AAPL, RMD, NVDA)
    ├── xbrl_facts.json                 # Company facts JSON (US-GAAP metrics, income statements, balances)
    └── filings/
        ├── 10-K_2024.html              # Full raw 10-K filing HTML
        ├── 10-K_2024_Item7_MDA.html    # Parsed Item 7 (MD&A) narrative
        └── 10-K_2024_Item8_Notes.html  # Parsed Item 8 (Financial Statements & Notes)
```

> [!NOTE]
> Files in `data/sec_corpus/` are gitignored to avoid checking large raw filing documents into version control.
