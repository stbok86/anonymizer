#!/usr/bin/env python3
"""
Создание файла паттернов для NLP Service
Фокус на неструктурированных данных и именованных сущностях
"""

import pandas as pd
import os

def create_nlp_patterns():
    """Создаем паттерны для NLP обработки неструктурированных данных"""
    
    patterns_data = []
    
    # 1. ПЕРСОНАЛЬНЫЕ ДАННЫЕ (неструктурированные)
    patterns_data.extend([
        # ФИО в различных форматах
        {
            "category": "person_name",
            "pattern": r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b",
            "description": "ФИО полностью (Фамилия Имя Отчество)",
            "confidence": 0.8,
            "pattern_type": "regex",
            "context_required": True
        },
        {
            "category": "person_name", 
            "pattern": r"\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.",
            "description": "Фамилия И.О.",
            "confidence": 0.9,
            "pattern_type": "regex", 
            "context_required": False
        },
        {
            "category": "person_name",
            "pattern": r"\b[А-ЯЁ]\.\s*[А-ЯЁ]\.\s+[А-ЯЁ][а-яё]+",
            "description": "И.О. Фамилия",
            "confidence": 0.9,
            "pattern_type": "regex",
            "context_required": False
        },
        
        # Должности и роли
        {
            "category": "position",
            "pattern": "",  # Будет использовать spaCy NER + контекст
            "description": "Должности и роли сотрудников",
            "confidence": 0.7,
            "pattern_type": "spacy_context",
            "context_required": True
        }
    ])
    
    # 2. ОРГАНИЗАЦИОННЫЕ ДАННЫЕ
    patterns_data.extend([
        {
            "category": "organization",
            "pattern": r"\b(ООО|АО|ПАО|ЗАО|ИП|ГУП|МУП)\s+[«\"']?[А-ЯЁа-яё\s\-]+[»\"']?",
            "description": "Организации с юридической формой",
            "confidence": 0.9,
            "pattern_type": "regex",
            "context_required": False
        },
        {
            "category": "organization",
            "pattern": "",  # spaCy ORG entities
            "description": "Организации (NER)",
            "confidence": 0.7,
            "pattern_type": "spacy_ner",
            "context_required": True
        },
        {
            "category": "department",
            "pattern": r"\b(отдел|управление|департамент|служба|сектор)\s+[А-ЯЁа-яё\s]+",
            "description": "Подразделения организации",
            "confidence": 0.8,
            "pattern_type": "regex",
            "context_required": True
        }
    ])
    
    # 3. ФИНАНСОВАЯ ИНФОРМАЦИЯ (неструктурированная)
    patterns_data.extend([
        {
            "category": "salary",
            "pattern": r"\b(зарплата|оклад|заработная\s+плата|доход)\s*[:\-]?\s*\d+[\d\s]*\s?(руб|₽|рублей?|долларов?|\$|евро|€)",
            "description": "Информация о зарплате/доходах",
            "confidence": 0.8,
            "pattern_type": "regex",
            "context_required": True
        },
        {
            "category": "financial_amount",
            "pattern": r"\b\d+[\d\s]*[,.]?\d*\s?(руб|₽|рублей?|долларов?|\$|евро|€)\b",
            "description": "Денежные суммы в контексте",
            "confidence": 0.6,
            "pattern_type": "regex",
            "context_required": True
        }
    ])
    
    # 4. СПЕЦИАЛЬНЫЕ КАТЕГОРИИ
    patterns_data.extend([
        {
            "category": "health_info",
            "pattern": r"\b(диагноз|болезнь|заболевание|лечение|медицин|больниц|поликлиник|врач|доктор)\b",
            "description": "Сведения о здоровье (контекст)",
            "confidence": 0.7,
            "pattern_type": "regex",
            "context_required": True
        },
        {
            "category": "beliefs",
            "pattern": r"\b(религ|веро|полит|убежден|мировоззрен|партии)\b",
            "description": "Убеждения и взгляды",
            "confidence": 0.6,
            "pattern_type": "regex",
            "context_required": True
        }
    ])
    
    # 5. ТЕХНИЧЕСКИЕ ИДЕНТИФИКАТОРЫ (контекстные)
    patterns_data.extend([
        {
            "category": "login_credential",
            "pattern": r"\b(логин|пароль|учетн[ая]\s+запись|авторизац|аутентиф)\b",
            "description": "Данные аутентификации (контекст)",
            "confidence": 0.7,
            "pattern_type": "regex",
            "context_required": True
        },
        {
            "category": "system_name",
            "pattern": r"\b(система|подсистема|сервис|платформа)\s+[А-ЯЁа-яё\-\d]+",
            "description": "Названия систем и сервисов",
            "confidence": 0.8,
            "pattern_type": "regex",
            "context_required": True
        }
    ])
    
    # 6. КОММЕРЧЕСКАЯ ТАЙНА
    patterns_data.extend([
        {
            "category": "trade_secret",
            "pattern": r"\b(конфиденциальн|коммерческ[ая]\s+тайн|ноу-хау|секретн)\b",
            "description": "Коммерческая тайна (контекст)",
            "confidence": 0.7,
            "pattern_type": "regex",
            "context_required": True
        },
        {
            "category": "contract_info",
            "pattern": r"\b(договор|контракт|соглашение)\s+№?\s*[\dА-ЯЁа-яё\-/]+",
            "description": "Информация о договорах",
            "confidence": 0.8,
            "pattern_type": "regex",
            "context_required": True
        }
    ])
    
    # 7. ЛОКАЦИИ (через spaCy)
    patterns_data.extend([
        {
            "category": "location",
            "pattern": "",  # spaCy LOC entities
            "description": "Географические локации (NER)",
            "confidence": 0.7,
            "pattern_type": "spacy_ner",
            "context_required": True
        },
        {
            "category": "address_context",
            "pattern": r"\b(адрес|проживает?|находится|расположен)\s+[А-ЯЁа-яё\s\d,.-]+",
            "description": "Адресная информация в контексте",
            "confidence": 0.6,
            "pattern_type": "regex", 
            "context_required": True
        }
    ])
    
    # Создаем DataFrame
    df = pd.DataFrame(patterns_data)
    
    # Путь к Excel файлу
    excel_path = os.path.join(os.path.dirname(__file__), "nlp_patterns.xlsx")
    
    # Сохраняем в Excel
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    print(f"✅ Создан файл паттернов NLP: {excel_path}")
    print(f"📊 Всего паттернов: {len(df)}")
    
    # Показываем статистику по категориям
    print("\n📋 Паттерны по категориям:")
    category_stats = df['category'].value_counts()
    for category, count in category_stats.items():
        print(f"   {category}: {count}")
    
    # Показываем типы паттернов
    print("\n🔧 По типам обработки:")
    type_stats = df['pattern_type'].value_counts()
    for pattern_type, count in type_stats.items():
        print(f"   {pattern_type}: {count}")
    
    return excel_path

if __name__ == "__main__":
    create_nlp_patterns()