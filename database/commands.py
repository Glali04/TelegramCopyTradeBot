import aiosqlite

# create a connection to the database
# connection is a Connection object represents the connection to the on-disk database
# In order to execute SQL statements and fetch results from SQL queries, we will need to use a database cursor.

async def insert_query(user_id: str, token_address: str, start_time: float, end_time: float, bought: int, sold: int,
                       exit_reason: str):
    async with aiosqlite.connect("finished_trades.db") as database:
        # in aiosqlite you do not need to create cursors explicitly, execute() internally creates and manages the cursor
        # for you only need a cursor when fetching results
        await database.execute("""
            INSERT INTO finished_trades(user_id, token_address, start_time, end_time, bought, sold, exit_reason)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """, (user_id, token_address, start_time, end_time, bought, sold, exit_reason)
        )
        await database.commit()