import duckdb
conn = duckdb.connect("db/financials.duckdb")
df = conn.execute("SELECT ticker, COUNT(*) as facts FROM financial_facts GROUP BY ticker ORDER BY ticker").df()
print(df.to_string(index=False))
conn.close()
