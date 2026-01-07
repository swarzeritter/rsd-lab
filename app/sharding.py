"""
Модуль для роботи з шардуванням баз даних.
"""
import json
import os
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool


class ShardingManager:
    """Менеджер для управління шардуванням баз даних."""
    
    def __init__(self, mapping_file: str = "mapping.json"):
        """Ініціалізація менеджера шардування."""
        self.mapping_file = mapping_file
        self.mapping: Dict = {}
        self.engines: Dict[str, any] = {}
        self.session_makers: Dict[str, sessionmaker] = {}
        self._load_mapping()
        self._create_engines()
    
    def _load_mapping(self):
        """Завантажує mapping.json з конфігурацією баз даних."""
        mapping_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.mapping_file)
        if not os.path.exists(mapping_path):
            # Спробуємо в поточній директорії
            mapping_path = self.mapping_file
            if not os.path.exists(mapping_path):
                raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
    
    def _create_engines(self):
        """Створює SQLAlchemy engines для кожної бази даних."""
        for db_name, config in self.mapping.items():
            # Формуємо DATABASE_URL
            db_url = (
                f"postgresql://{config['user']}:{config['password']}"
                f"@{config['host']}:{config['port']}/{config['database']}"
            )
            
            # Створюємо engine з connection pool
            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=False,  # Вимикаємо для продуктивності
                connect_args={
                    "connect_timeout": 10
                }
            )
            
            self.engines[db_name] = engine
            self.session_makers[db_name] = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
    
    def get_shard_name(self, uuid_value: UUID) -> str:
        """
        Визначає назву шарду на основі останнього символу UUID.
        
        Args:
            uuid_value: UUID значення для визначення шарду
            
        Returns:
            Назва бази даних (db_0..db_f)
        """
        uuid_str = str(uuid_value).replace('-', '')
        last_char = uuid_str[-1].lower()
        
        # Маппінг останнього символу на базу даних
        shard_map = {
            '0': 'db_0', '1': 'db_1', '2': 'db_2', '3': 'db_3',
            '4': 'db_4', '5': 'db_5', '6': 'db_6', '7': 'db_7',
            '8': 'db_8', '9': 'db_9', 'a': 'db_a', 'b': 'db_b',
            'c': 'db_c', 'd': 'db_d', 'e': 'db_e', 'f': 'db_f'
        }
        
        return shard_map.get(last_char, 'db_0')
    
    def get_db_session(self, shard_name: Optional[str] = None) -> Session:
        """
        Отримує сесію БД для вказаного шарду.
        
        Args:
            shard_name: Назва шарду (db_0..db_f). Якщо None, повертає сесію для db_0.
            
        Returns:
            SQLAlchemy Session
        """
        if shard_name is None:
            shard_name = 'db_0'
        
        if shard_name not in self.session_makers:
            raise ValueError(f"Unknown shard: {shard_name}")
        
        return self.session_makers[shard_name]()
    
    def get_all_shards(self) -> list:
        """Повертає список всіх доступних шардів."""
        return list(self.mapping.keys())


# Глобальний екземпляр менеджера шардування
_sharding_manager: Optional[ShardingManager] = None


def get_sharding_manager() -> ShardingManager:
    """Отримує глобальний екземпляр менеджера шардування."""
    global _sharding_manager
    if _sharding_manager is None:
        _sharding_manager = ShardingManager()
    return _sharding_manager


def get_sharded_db(travel_plan_id: Optional[UUID] = None) -> Session:
    """
    Отримує сесію БД для вказаного travel_plan_id.
    
    Args:
        travel_plan_id: UUID плану подорожі для визначення шарду
        
    Returns:
        SQLAlchemy Session для відповідного шарду
    """
    manager = get_sharding_manager()
    
    if travel_plan_id is not None:
        shard_name = manager.get_shard_name(travel_plan_id)
    else:
        shard_name = 'db_0'  # За замовчуванням
    
    return manager.get_db_session(shard_name)

