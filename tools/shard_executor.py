import sys
import os
import argparse
import logging
from typing import List, Dict

# Додаємо кореневу директорію проекту в шлях, щоб імпортувати app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.sharding import get_sharding_manager, ShardingManager

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DistributedTransactionError(Exception):
    pass

def execute_on_all_shards(sql_file_path: str):
    """
    Виконує SQL скрипт на всіх шардах з механізмом розподіленої транзакції.
    """
    if not os.path.exists(sql_file_path):
        logger.error(f"File not found: {sql_file_path}")
        sys.exit(1)

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    try:
        manager = get_sharding_manager()
        shards = manager.get_all_shards()
    except Exception as e:
        logger.error(f"Failed to initialize sharding manager: {e}")
        logger.error("Make sure you have mapping.json and database connectivity.")
        sys.exit(1)
    
    sessions: Dict[str, Session] = {}
    
    logger.info(f"Starting distributed execution of {sql_file_path} on {len(shards)} shards")
    
    try:
        # 1. Відкриваємо сесії та транзакції для всіх шардів
        for shard_name in shards:
            logger.info(f"Connecting to {shard_name}...")
            session = manager.get_db_session(shard_name)
            sessions[shard_name] = session
            # Перевірка з'єднання
            session.execute(text("SELECT 1"))

        # 2. Виконуємо SQL на кожному шарді (Phase 1: Prepare/Execute)
        for shard_name, session in sessions.items():
            logger.info(f"Executing SQL on {shard_name}...")
            # Використовуємо text() для сирого SQL
            session.execute(text(sql_content))
            # flush відправляє команди в БД, але не робить коміт
            session.flush()
        
        logger.info("SQL executed successfully on all shards. Committing...")

        # 3. Комітимо транзакції (Phase 2: Commit)
        for shard_name, session in sessions.items():
            session.commit()
            logger.info(f"Committed on {shard_name}")
            
        logger.info("Distributed execution completed successfully.")

    except Exception as e:
        logger.error(f"Error occurred: {e}. Rolling back all transactions...")
        # 4. Rollback у разі помилки
        for shard_name, session in sessions.items():
            try:
                session.rollback()
                logger.info(f"Rolled back on {shard_name}")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback on {shard_name}: {rollback_error}")
        
        raise DistributedTransactionError(f"Execution failed: {e}")
    finally:
        # Закриваємо всі сесії
        for session in sessions.values():
            session.close()

def main():
    parser = argparse.ArgumentParser(description='Execute SQL script on all shards with atomic commit.')
    parser.add_argument('file', help='Path to SQL file to execute')
    
    args = parser.parse_args()
    
    try:
        execute_on_all_shards(args.file)
    except DistributedTransactionError:
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

