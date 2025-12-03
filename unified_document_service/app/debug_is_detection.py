#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Отладка детекции информационных систем
"""

import sys
import os
import requests
from docx import Document

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from block_builder import BlockBuilder

def analyze_is_detection():
    """Анализируем детекцию информационных систем"""
    
    input_path = r'C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4_SD2.docx'
    
    print("=" * 120)
    print("АНАЛИЗ ДЕТЕКЦИИ ИНФОРМАЦИОННЫХ СИСТЕМ")
    print("=" * 120)
    
    # Загружаем документ
    doc = Document(input_path)
    
    # Извлекаем текст через BlockBuilder
    bb = BlockBuilder()
    blocks = bb.build_blocks(doc)
    
    # Собираем full_text как в FullAnonymizer
    full_text = ""
    block_positions = []
    
    for block in blocks:
        block_start = len(full_text)
        block_text = block.get('text', '')
        full_text += block_text + "\n"
        block_end = len(full_text) - 1  # Не включаем последний \n
        
        block_positions.append({
            'id': block.get('id'),
            'type': block.get('type'),
            'start': block_start,
            'end': block_end,
            'text': block_text[:100]
        })
    
    print(f"\n📄 Извлечено {len(blocks)} блоков, всего {len(full_text)} символов")
    
    # Ищем упоминания информационных систем в тексте
    is_keywords = [
        "ЕДИНАЯ ИНФОРМАЦИОННАЯ СИСТЕМА",
        "Единой информационной системы",
        "информационной системы управления",
        "подсистемы «Управление имуществом»",
        "ФИНАНСОВО-ХОЗЯЙСТВЕННОЙ ДЕЯТЕЛЬНОСТЬЮ",
        "ЕИС",
    ]
    
    print(f"\n🔍 Поиск упоминаний информационных систем в тексте:")
    for keyword in is_keywords:
        if keyword in full_text or keyword.upper() in full_text.upper():
            # Ищем позиции
            text_to_search = full_text if keyword == keyword.upper() else full_text
            pos = text_to_search.find(keyword)
            if pos == -1:
                # Попробуем case-insensitive
                pos = full_text.upper().find(keyword.upper())
            
            if pos != -1:
                context_start = max(0, pos - 50)
                context_end = min(len(full_text), pos + len(keyword) + 50)
                context = full_text[context_start:context_end]
                print(f"\n  ✅ Найдено '{keyword}' на позиции {pos}")
                print(f"     Контекст: ...{context}...")
    
    # Вызываем NLP Service
    print(f"\n\n📞 Вызываем NLP Service для анализа...")
    nlp_url = "http://localhost:8006/analyze"
    
    # Подготавливаем блоки как ожидает NLP Service
    request_blocks = []
    for i, block in enumerate(blocks[:10]):  # Берем первые 10 блоков для теста
        block_id = block.get('id') or f"block_{i}"  # Используем индекс если id отсутствует
        request_blocks.append({
            "block_id": block_id,
            "content": block.get('text', '')
        })
    
    try:
        response = requests.post(
            nlp_url,
            json={"blocks": request_blocks},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            detections = result.get('detections', [])
            
            print(f"✅ NLP Service вернул {len(detections)} детекций\n")
            
            # Фильтруем только информационные системы
            is_detections = [d for d in detections if d.get('entity_type') == 'information_system']
            
            print(f"🖥️  Детекций информационных систем: {len(is_detections)}")
            
            if is_detections:
                print(f"\nНайденные информационные системы:")
                for i, det in enumerate(is_detections, 1):
                    text = det.get('text', '')
                    start = det.get('start', 0)
                    end = det.get('end', 0)
                    confidence = det.get('confidence', 0)
                    strategy = det.get('detection_strategy', 'unknown')
                    
                    print(f"\n  {i}. Текст: '{text}'")
                    print(f"     Позиция: {start}-{end}")
                    print(f"     Уверенность: {confidence:.2f}")
                    print(f"     Стратегия: {strategy}")
                    
                    # Показываем контекст
                    context_start = max(0, start - 30)
                    context_end = min(len(full_text), end + 30)
                    context = full_text[context_start:context_end]
                    print(f"     Контекст: ...{context}...")
            else:
                print("\n❌ NLP Service НЕ НАШЕЛ информационных систем!")
                print("\n📋 Все детекции (для справки):")
                for i, det in enumerate(detections[:10], 1):
                    print(f"  {i}. {det.get('entity_type')}: '{det.get('text', '')[:80]}'")
                
                # Проверяем конфигурацию NLP Service
                print(f"\n\n🔧 Проверяем конфигурацию NLP Service...")
                config_response = requests.get("http://localhost:8006/config")
                if config_response.status_code == 200:
                    config = config_response.json()
                    print(f"\n📝 Текущая конфигурация NLP Service:")
                    print(f"   - Стратегии включены: {config.get('enabled_strategies', [])}")
                    print(f"   - information_system включена: {'information_system' in config.get('enabled_strategies', [])}")
        else:
            print(f"❌ Ошибка NLP Service: {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Ошибка при вызове NLP Service: {e}")
        import traceback
        traceback.print_exc()
    
    # Проверяем паттерны информационных систем
    print(f"\n\n🔍 Проверяем паттерны информационных систем в NLP Service...")
    try:
        # Читаем конфиг NLP
        nlp_config_path = r'C:\Projects\Anonymizer\nlp_service\config\nlp_config.json'
        if os.path.exists(nlp_config_path):
            import json
            with open(nlp_config_path, 'r', encoding='utf-8') as f:
                nlp_config_data = json.load(f)
            
            # Проверяем настройки в nlp_service_config
            nlp_service_config = nlp_config_data.get('nlp_service_config', {})
            
            # Проверяем detection_methods для information_system
            detection_methods = nlp_service_config.get('detection_methods', {})
            is_method_config = detection_methods.get('information_system', {})
            
            print(f"\n📝 Конфигурация метода information_system:")
            print(f"   - Включенные методы: {is_method_config.get('enabled_methods', [])}")
            print(f"   - Стратегия: {is_method_config.get('strategy', 'unknown')}")
            print(f"   - Max results: {is_method_config.get('max_results', 0)}")
            
            # Проверяем настройки стратегии
            detection_strategies = nlp_service_config.get('detection_strategies', {})
            is_strategy = detection_strategies.get('information_system', {})
            print(f"\n📝 Конфигурация стратегии information_system:")
            print(f"   - Core keywords: {is_strategy.get('core_keywords', [])[:5]}")
            print(f"   - Known abbreviations: {is_strategy.get('known_abbreviations', [])[:10]}")
            print(f"   - Min confidence: {is_strategy.get('confidence_modifiers', {}).get('min_confidence', 0)}")
            
            # Проверяем паттерны
            patterns_path = r'C:\Projects\Anonymizer\nlp_service\patterns\nlp_patterns.json'
            if os.path.exists(patterns_path):
                with open(patterns_path, 'r', encoding='utf-8') as f:
                    patterns_data = json.load(f)
                
                all_patterns = patterns_data.get('patterns', [])
                is_patterns = [p for p in all_patterns if p.get('category') == 'information_system']
                print(f"\n   📋 Паттернов информационных систем: {len(is_patterns)}")
                if is_patterns:
                    print(f"   Примеры паттернов:")
                    for p in is_patterns[:5]:
                        print(f"      - {p.get('pattern', '')[:100]}")
        
    except Exception as e:
        print(f"❌ Ошибка чтения конфигурации: {e}")

if __name__ == "__main__":
    analyze_is_detection()
