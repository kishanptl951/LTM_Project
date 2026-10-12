import duckdb
conn = duckdb.connect("db/financials.duckdb")
df = conn.execute("""
    SELECT ticker, fiscal_year, concept, val, filed_date
    FROM financial_facts
    WHERE concept LIKE '%Revenue%'
    ORDER BY ticker, fiscal_year DESC
    LIMIT 5
""").df()
print(df.to_string(index=False))
conn.close()
