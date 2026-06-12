"""初始化数据库表"""

import asyncio
import sys
sys.path.insert(0, ".")

from src.infrastructure.database import init_db


async def main():
    print("创建数据库表...")
    await init_db()
    print("完成。")


if __name__ == "__main__":
    asyncio.run(main())
