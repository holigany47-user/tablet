import asyncio
import os
import sys

# Добавляем корневую папку в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main

if __name__ == "__main__":
    asyncio.run(main())
