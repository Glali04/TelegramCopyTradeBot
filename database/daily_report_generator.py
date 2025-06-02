import asyncio

import aiosqlite

"""it generates me a report how my bot did in a given day, the day we give with timestamp"""
async def fetch_trades(blockchain, start_time, end_time):
    async with aiosqlite.connect("finished_trades.db") as database:
        table = blockchain + "_finished_trades"
        query = f"""
        SELECT
            COUNT(*) AS total_trades,
            SUM(CASE WHEN exit_reason = 'we reached ath then price dropped 15%, most likely sold in profit'
            THEN 1 ELSE 0 END) AS profitable_trades,
            SUM(CASE WHEN exit_reason = 'we sold in loss' THEN 1 ELSE 0 END) AS losing_trades,
            SUM(CASE when sold > bought THEN 1 ELSE 0 END) AS sold_in_profit,
            SUM(bought) AS that_day_bought_for,
            SUM(sold) AS that_day_sold_for,
            MIN(sold) AS most_lose,
            MAX(sold) AS most_gain
        FROM {table}
        WHERE start_time >= ? AND start_time <= ?
        """

        async with database.execute(query, (start_time, end_time)) as cursor:
            row = await cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))  # convert to dictionary
#send time in timestamp
result = asyncio.run(fetch_trades("solana", 1744950278, 1745209478))
print(result)