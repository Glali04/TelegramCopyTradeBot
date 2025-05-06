import aiosqlite
import asyncio

"we will use asynco queue to ensure every trade was wrote in the database, and to prevent database locks"
db_queue = asyncio.Queue()  # Queue for pending database writes


# create a connection to the database
# connection is a Connection object represents the connection to the on-disk database
# In order to execute SQL statements and fetch results from SQL queries, we will need to use a database cursor.


# Function to process database writes from the queue
async def process_db_queue():
    async with aiosqlite.connect('database/finished_trades.db') as database:
        while True:
            query, params = await db_queue.get()  # Get next DB write
            await database.execute(query, params)
            await database.commit()
            db_queue.task_done()


# Function to add a trade to the database
async def save_trade(user_name: str, token_address: str, start_time: float, end_time: float, bought: int, sold: int,
                     exit_reason: str):
    table = "solana_finished_trades" if token_address[0:2] != "0x" else "bsc_finished_trades"
    query = f"""
        INSERT INTO {table}  (user_name, token_address, start_time, end_time, bought, sold, exit_reason)
            VALUES(?, ?, ?, ?, ?, ?, ?)
    """
    await db_queue.put((query, (user_name, token_address, int(start_time), int(end_time), bought, sold, exit_reason)))


async def statistic(from_data, to_data, blockchain):
    blockchain += "_finished_trades"
    async with aiosqlite.connect('finished_trades.db') as database:
        async with database.execute(f"SELECT SUM(bought), SUM(sold) FROM {blockchain}") as cursor:
            result = await cursor.fetchone()

    total_bought, total_sold = result  # unpack values

    print(f"Total Bought {total_bought}, Total Sold: {total_sold}, Panel: {total_sold - total_bought}")


async def delete_all_records(blockchain):
    async with aiosqlite.connect("finished_trades.db") as database:
        table = f"{blockchain}_finished_trades"
        query = f"DELETE FROM {table};"

        async with database.execute(query) as cursor:
            await database.commit()  # Commit the changes to the database
        print(f"All records from table {table} have been deleted.")

#asyncio.run(statistic(0, 0, "Solana"))
#asyncio.run(delete_all_records("solana"))
