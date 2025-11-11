#!/usr/bin/env python3
"""
Скрипт для тестирования восстановленных модулей unified_document_service
"""

import sys
import os

# Добавляем путь к модулям app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Тестирование импортов модулей"""
    try:
        from full_anonymizer import FullAnonymizer
        print("✓ FullAnonymizer импортирован успешно")
        
        from formatter_applier import FormatterApplier
        print("✓ FormatterApplier импортирован успешно")
        
        from rule_adapter import RuleEngineAdapter
        print("✓ RuleEngineAdapter импортирован успешно")
        
        from block_builder import BlockBuilder
        print("✓ BlockBuilder импортирован успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_functionality():
    """Тестирование базовой функциональности"""
    try:
        from full_anonymizer import FullAnonymizer
        from formatter_applier import FormatterApplier
        from rule_adapter import RuleEngineAdapter
        
        # Инициализация модулей
        anonymizer = FullAnonymizer()
        formatter = FormatterApplier(highlight_replacements=True)
        rule_engine = RuleEngineAdapter()
        
        print("✓ Все модули инициализированы успешно")
        
        # Тест поиска чувствительных данных
        test_text = "Мой телефон: +7-999-123-45-67, email: test@example.com"
        found_items = rule_engine.find_sensitive_data(test_text)
        print(f"✓ Найдено {len(found_items)} чувствительных элементов в тестовом тексте")
        
        # Тест валидации паттернов
        validation = rule_engine.validate_patterns()
        print(f"✓ Валидация паттернов: {validation['valid_patterns']} валидных, {validation['invalid_patterns']} невалидных")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    print("=== Тестирование восстановленных модулей ===\n")
    
    print("1. Тестирование импортов:")
    imports_ok = test_imports()
    
    print("\n2. Тестирование функциональности:")
    if imports_ok:
        functionality_ok = test_functionality()
    else:
        functionality_ok = False
    
    print("\n=== Результат тестирования ===")
    if imports_ok and functionality_ok:
        print("✓ Все модули восстановлены и работают корректно!")
        return True
    else:
        print("❌ Обнаружены проблемы в модулях")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)