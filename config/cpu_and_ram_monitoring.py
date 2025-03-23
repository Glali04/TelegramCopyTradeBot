import psutil
from asyncio import sleep


async def monitor_resources():
    while True:
        cpu = psutil.cpu_percent(interval=1)  # CPU usage in %
        ram = psutil.virtual_memory().used / (1024 ** 3)  # RAM in GB
        print(f"CPU usage: {cpu}% | RAM usage: {ram:.2f} GB")
        await sleep(1)  # Non-blocking sleep
