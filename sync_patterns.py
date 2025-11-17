#!/usr/bin/env python3
"""
Синхронизация паттернов между NLP Service и Rule Engine
"""
import pandas as pd
import os

def sync_patterns():
    """Синхронизирует паттерны между двумя сервисами"""
    
    nlp_patterns_file = r"C:\Projects\Anonymizer\nlp_service\patterns\nlp_patterns.xlsx"
    rule_patterns_file = r"C:\Projects\Anonymizer\unified_document_service\patterns\sensitive_patterns.xlsx"
    
    print(f"🔄 Синхронизация паттернов...")
    print(f"📄 NLP паттерны: {nlp_patterns_file}")
    print(f"📄 Rule паттерны: {rule_patterns_file}")
    
    try:
        # Загружаем NLP паттерны (источник)
        df_nlp = pd.read_excel(nlp_patterns_file)
        print(f"📊 NLP паттернов: {len(df_nlp)}")
        
        # Загружаем Rule Engine паттерны (назначение) 
        df_rule = pd.read_excel(rule_patterns_file)
        print(f"📊 Rule паттернов: {len(df_rule)}")
        
        # Находим новые категории в NLP, которых нет в Rule Engine
        nlp_categories = set(df_nlp['category'].unique())
        rule_categories = set(df_rule['category'].unique())
        
        new_categories = nlp_categories - rule_categories
        print(f"\n🆕 Новые категории для Rule Engine: {new_categories}")
        
        if new_categories:
            # Фильтруем NLP паттерны только для новых категорий
            new_patterns = df_nlp[df_nlp['category'].isin(new_categories)].copy()
            
            # Преобразуем формат NLP в формат Rule Engine
            rule_format_patterns = []
            for _, row in new_patterns.iterrows():
                rule_format_patterns.append({
                    'category': row['category'],
                    'pattern': row['pattern'],
                    'description': row['description'], 
                    'confidence': row['confidence']
                })
            
            # Добавляем новые паттерны к существующим Rule Engine
            df_new_rule = pd.DataFrame(rule_format_patterns)
            df_combined = pd.concat([df_rule, df_new_rule], ignore_index=True)
            
            # Сохраняем обновленный файл Rule Engine
            df_combined.to_excel(rule_patterns_file, index=False)
            print(f"✅ Добавлено {len(rule_format_patterns)} новых паттернов в Rule Engine")
            print(f"📊 Общее количество Rule Engine паттернов: {len(df_combined)}")
            
            # Показываем добавленные паттерны
            print(f"\n🔍 Добавленные паттерны:")
            for pattern in rule_format_patterns:
                print(f"  {pattern['category']}: {pattern['description']}")
        else:
            print(f"✅ Все категории уже синхронизированы")
            
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")

if __name__ == "__main__":
    sync_patterns()