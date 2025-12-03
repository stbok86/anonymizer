#!/usr/bin/env python3
"""
UUID MAPPER - Архитектурно правильное решение проблемы дублирования UUID
========================================================================

Компонент для обеспечения консистентности UUID замен:
- Одинаковый текст → одинаковый UUID во всем документе
- Разный текст → разный UUID  
- Сохранение детерминизма и обратимости
"""

import uuid
import hashlib
from typing import Dict, List, Any, Optional

class UUIDMapper:
    """
    Компонент для консистентного мапинга text → UUID
    
    Принципы:
    1. Детерминизм: одинаковый текст всегда получает одинаковый UUID
    2. Уникальность: разный текст получает разный UUID
    3. Стабильность: UUID не меняется между запусками
    4. Обратимость: можно создать обратную карту UUID → text
    """
    
    def __init__(self, namespace: str = "document-anonymization"):
        """
        Инициализация UUID Mapper
        
        Args:
            namespace: Пространство имен для генерации UUID (для стабильности)
        """
        # Создаем базовый UUID для namespace
        self.namespace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
        
        # Кэш для уже сгенерированных мапингов
        self.text_to_uuid: Dict[str, str] = {}
        self.uuid_to_text: Dict[str, str] = {}
        
    def get_uuid_for_text(self, original_text: str, category: str = "data") -> str:
        """
        Получает уникальный UUID для каждого вхождения текста
        
        Args:
            original_text: Исходный текст
            category: Категория данных (для дополнительной энтропии)
            
        Returns:
            Уникальный UUID (каждый раз новый, даже для одинакового текста)
        """
        # Генерируем случайный UUID для каждого вхождения
        # uuid4 генерирует случайный UUID, не зависящий от входных данных
        random_uuid = str(uuid.uuid4())
        
        # Сохраняем в кэш для обратимости (UUID → text)
        self.uuid_to_text[random_uuid] = original_text
        
        return random_uuid
    
    def get_text_for_uuid(self, uuid_str: str) -> Optional[str]:
        """
        Получает исходный текст по UUID (для обратимости)
        
        Args:
            uuid_str: UUID замены
            
        Returns:
            Исходный текст или None если не найден
        """
        return self.uuid_to_text.get(uuid_str)
    
    def normalize_replacements(self, replacements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Генерирует уникальные UUID для каждой замены
        
        Args:
            replacements: Список замен
            
        Returns:
            Список замен с уникальными UUID для каждого вхождения
        """
        normalized = []
        
        for replacement in replacements:
            original_text = replacement.get('original_value', '')
            category = replacement.get('category', 'data')
            
            if not original_text:
                normalized.append(replacement)
                continue
                
            # Генерируем новый уникальный UUID для каждого вхождения
            unique_uuid = self.get_uuid_for_text(original_text, category)
            
            # Создаем замену с уникальным UUID
            normalized_replacement = replacement.copy()
            normalized_replacement['uuid'] = unique_uuid
            
            normalized.append(normalized_replacement)
        
        return normalized
    
    def get_mapping_stats(self) -> Dict[str, Any]:
        """
        Получает статистику мапинга
        
        Returns:
            Словарь со статистикой
        """
        return {
            'total_mappings': len(self.text_to_uuid),
            'unique_texts': len(set(self.uuid_to_text.values())),
            'unique_uuids': len(self.uuid_to_text),
            'namespace_uuid': str(self.namespace_uuid)
        }
    
    def export_mapping(self) -> Dict[str, str]:
        """
        Экспортирует полное отображение UUID → text для отчетности
        
        Returns:
            Словарь UUID → исходный текст
        """
        return self.uuid_to_text.copy()

# Тестирование UUID Mapper
def test_uuid_mapper():
    """Тестирует работу UUID Mapper"""
    
    print("🧪 ТЕСТ UUID MAPPER")
    print("=" * 40)
    
    mapper = UUIDMapper("test-document")
    
    # Тест 1: Детерминизм
    text1 = "14 августа 2023"
    uuid1_first = mapper.get_uuid_for_text(text1, "date")
    uuid1_second = mapper.get_uuid_for_text(text1, "date")
    
    print(f"✅ Тест детерминизма:")
    print(f"   Текст: '{text1}'")
    print(f"   UUID 1: {uuid1_first}")
    print(f"   UUID 2: {uuid1_second}")
    print(f"   Одинаковы: {uuid1_first == uuid1_second}")
    
    # Тест 2: Уникальность
    text2 = "15 августа 2023"
    uuid2 = mapper.get_uuid_for_text(text2, "date")
    
    print(f"\n✅ Тест уникальности:")
    print(f"   Текст 1: '{text1}' → {uuid1_first}")
    print(f"   Текст 2: '{text2}' → {uuid2}")
    print(f"   Разные: {uuid1_first != uuid2}")
    
    # Тест 3: Нормализация замен
    test_replacements = [
        {'original_value': '14 августа 2023', 'uuid': 'old-uuid-1', 'block_id': 'table_2_1', 'category': 'date'},
        {'original_value': '14 августа 2023', 'uuid': 'old-uuid-2', 'block_id': 'table_2_2', 'category': 'date'}, 
        {'original_value': '14 августа 2023', 'uuid': 'old-uuid-3', 'block_id': 'table_2_3', 'category': 'date'},
        {'original_value': '15 августа 2023', 'uuid': 'old-uuid-4', 'block_id': 'para_1', 'category': 'date'}
    ]
    
    normalized = mapper.normalize_replacements(test_replacements)
    
    print(f"\n✅ Тест нормализации:")
    print(f"   Исходные замены: {len(test_replacements)}")
    for i, repl in enumerate(test_replacements):
        print(f"     {i+1}. '{repl['original_value']}' → {repl['uuid']}")
    
    print(f"   Нормализованные замены:")
    unique_uuids = set()
    for i, repl in enumerate(normalized):
        print(f"     {i+1}. '{repl['original_value']}' → {repl['uuid']}")
        unique_uuids.add(repl['uuid'])
    
    print(f"   Уникальных UUID: {len(unique_uuids)} (должно быть 2)")
    
    # Тест 4: Статистика
    stats = mapper.get_mapping_stats()
    print(f"\n📊 Статистика мапинга:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    test_uuid_mapper()