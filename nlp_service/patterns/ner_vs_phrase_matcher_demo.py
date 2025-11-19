#!/usr/bin/env python3
"""
Практическая демонстрация различий между spaCy NER и Phrase Matcher
"""

import spacy
from spacy.matcher import PhraseMatcher
from typing import List, Dict, Any
import time

class NERVsPhraseMatcherDemo:
    """Демонстрация различий между spaCy NER и Phrase Matcher"""
    
    def __init__(self):
        print("🔄 Загружаем spaCy модель...")
        self.nlp = spacy.load("ru_core_news_lg")
        
        # Настраиваем Phrase Matcher
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._setup_phrase_matcher()
    
    def _setup_phrase_matcher(self):
        """Настраиваем Phrase Matcher с известными госорганизациями"""
        
        # Список известных государственных организаций
        gov_orgs = [
            "Министерство внутренних дел",
            "МВД России",
            "Роскомнадзор", 
            "ФНС России",
            "Федеральная налоговая служба",
            "Минздрав России",
            "Министерство здравоохранения",
            "Администрация Президента",
            "Правительство РФ",
            "Департамент образования",
            "Управление внутренних дел"
        ]
        
        # Преобразуем в spaCy документы
        patterns = [self.nlp(org) for org in gov_orgs]
        
        # Добавляем в matcher
        self.phrase_matcher.add("GOVERNMENT_ORG", patterns)
        
        print(f"✅ Phrase Matcher настроен с {len(gov_orgs)} организациями")
    
    def demonstrate_ner_approach(self, text: str) -> Dict[str, Any]:
        """Демонстрирует работу spaCy NER"""
        
        print(f"\n🤖 SPACY NER ПОДХОД")
        print(f"{'='*50}")
        print(f"📝 Анализируем: '{text}'")
        
        start_time = time.time()
        doc = self.nlp(text)
        processing_time = time.time() - start_time
        
        # Находим все именованные сущности
        all_entities = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
        
        # Фильтруем только организации
        organizations = [ent for ent in doc.ents if ent.label_ == "ORG"]
        
        print(f"\n🔍 ВСЕ найденные сущности spaCy:")
        for text_span, label, start, end in all_entities:
            confidence = "средняя" if label == "ORG" else "высокая"
            print(f"   • '{text_span}' → {label} (позиция: {start}-{end}, уверенность: {confidence})")
        
        print(f"\n🏛️ Организации (ORG):")
        org_results = []
        for org in organizations:
            # spaCy не дает прямого confidence, оцениваем косвенно
            confidence = self._estimate_ner_confidence(org)
            result = {
                'text': org.text,
                'start': org.start_char,
                'end': org.end_char,
                'confidence': confidence,
                'method': 'spacy_ner'
            }
            org_results.append(result)
            print(f"   ✅ '{org.text}' (confidence: {confidence:.2f})")
        
        print(f"\n⚡ Время обработки: {processing_time*1000:.1f} мс")
        print(f"📊 Принцип работы:")
        print(f"   • Анализирует морфологию, синтаксис, контекст")
        print(f"   • Использует предобученную нейронную сеть")
        print(f"   • Может найти НЕИЗВЕСТНЫЕ организации")
        print(f"   • Понимает контекст (\"работает в Apple\" vs \"купил apple\")")
        
        return {
            'results': org_results,
            'processing_time': processing_time,
            'total_entities': len(all_entities),
            'organizations_found': len(organizations)
        }
    
    def demonstrate_phrase_matcher(self, text: str) -> Dict[str, Any]:
        """Демонстрирует работу Phrase Matcher"""
        
        print(f"\n📚 PHRASE MATCHER ПОДХОД")
        print(f"{'='*50}")
        print(f"📝 Анализируем: '{text}'")
        
        start_time = time.time()
        doc = self.nlp(text)
        matches = self.phrase_matcher(doc)
        processing_time = time.time() - start_time
        
        print(f"\n🔍 Процесс поиска:")
        print(f"   1. Токенизация текста: {[token.text for token in doc]}")
        print(f"   2. Поиск точных совпадений с известными фразами")
        print(f"   3. Найдено совпадений: {len(matches)}")
        
        phrase_results = []
        for match_id, start, end in matches:
            span = doc[start:end]
            result = {
                'text': span.text,
                'start': span.start_char,
                'end': span.end_char,
                'confidence': 0.95,  # Высокая уверенность для точных совпадений
                'method': 'phrase_matcher'
            }
            phrase_results.append(result)
            
            print(f"   ✅ Найдено: '{span.text}' (токены {start}-{end})")
            print(f"      Позиция в тексте: {span.start_char}-{span.end_char}")
            print(f"      Уверенность: 0.95 (точное совпадение)")
        
        print(f"\n⚡ Время обработки: {processing_time*1000:.1f} мс")
        print(f"📊 Принцип работы:")
        print(f"   • Точное сопоставление с заранее известными фразами")
        print(f"   • Очень быстрый поиск (алгоритм автомата)")
        print(f"   • Высокая точность для известных названий")
        print(f"   • НЕ найдет неизвестные организации")
        
        return {
            'results': phrase_results,
            'processing_time': processing_time,
            'matches_found': len(matches)
        }
    
    def _estimate_ner_confidence(self, ent) -> float:
        """Оценивает confidence для NER сущности"""
        # spaCy не предоставляет прямой confidence, делаем оценку
        base_confidence = 0.75
        
        # Бонус за длину (длинные названия обычно точнее)
        length_bonus = min(0.15, len(ent.text.split()) * 0.05)
        
        # Бонус за заглавные буквы (организации часто с большой буквы)
        if ent.text[0].isupper():
            caps_bonus = 0.05
        else:
            caps_bonus = 0
        
        return min(0.90, base_confidence + length_bonus + caps_bonus)
    
    def compare_approaches(self, test_texts: List[str]):
        """Сравнивает оба подхода на тестовых текстах"""
        
        print(f"\n🔬 СРАВНИТЕЛЬНЫЙ АНАЛИЗ")
        print(f"{'='*80}")
        
        total_ner_time = 0
        total_phrase_time = 0
        
        comparison_table = []
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n📄 ТЕСТ {i}: {text}")
            print(f"{'-'*60}")
            
            # Тестируем NER
            ner_results = self.demonstrate_ner_approach(text)
            total_ner_time += ner_results['processing_time']
            
            # Тестируем Phrase Matcher
            phrase_results = self.demonstrate_phrase_matcher(text)
            total_phrase_time += phrase_results['processing_time']
            
            # Сравниваем результаты
            print(f"\n🆚 СРАВНЕНИЕ РЕЗУЛЬТАТОВ:")
            
            ner_orgs = set(r['text'] for r in ner_results['results'])
            phrase_orgs = set(r['text'] for r in phrase_results['results'])
            
            only_ner = ner_orgs - phrase_orgs
            only_phrase = phrase_orgs - ner_orgs
            both = ner_orgs & phrase_orgs
            
            print(f"   🤖 Только NER нашел: {only_ner if only_ner else 'ничего'}")
            print(f"   📚 Только Phrase Matcher: {only_phrase if only_phrase else 'ничего'}")
            print(f"   🎯 Нашли оба: {both if both else 'ничего'}")
            
            comparison_table.append({
                'text': text,
                'ner_count': len(ner_results['results']),
                'phrase_count': len(phrase_results['results']),
                'ner_time': ner_results['processing_time'] * 1000,
                'phrase_time': phrase_results['processing_time'] * 1000,
                'overlap': len(both)
            })
        
        # Итоговое сравнение
        print(f"\n📊 ИТОГОВОЕ СРАВНЕНИЕ")
        print(f"{'='*80}")
        
        print(f"⏱️ Скорость:")
        print(f"   spaCy NER: {total_ner_time*1000:.1f} мс общее время")
        print(f"   Phrase Matcher: {total_phrase_time*1000:.1f} мс общее время")
        speedup = total_ner_time / total_phrase_time if total_phrase_time > 0 else 0
        print(f"   Phrase Matcher быстрее в {speedup:.1f}x раз")
        
        total_ner_found = sum(row['ner_count'] for row in comparison_table)
        total_phrase_found = sum(row['phrase_count'] for row in comparison_table)
        
        print(f"\n🎯 Покрытие:")
        print(f"   spaCy NER: {total_ner_found} организаций найдено")
        print(f"   Phrase Matcher: {total_phrase_found} организаций найдено")
        
        print(f"\n📋 Детальная таблица:")
        print(f"{'Тест':<5} {'NER':<4} {'Phrase':<7} {'Время NER':<10} {'Время Phrase':<13} {'Пересечение':<12}")
        print(f"{'-'*60}")
        for i, row in enumerate(comparison_table, 1):
            print(f"{i:<5} {row['ner_count']:<4} {row['phrase_count']:<7} "
                  f"{row['ner_time']:<10.1f} {row['phrase_time']:<13.1f} {row['overlap']:<12}")

def run_comprehensive_demo():
    """Запускает комплексную демонстрацию"""
    
    print(f"🔬 ДЕМОНСТРАЦИЯ РАЗЛИЧИЙ: spaCy NER vs Phrase Matcher")
    print(f"{'='*80}")
    
    demo = NERVsPhraseMatcherDemo()
    
    # Тестовые тексты с различными сценариями
    test_texts = [
        # 1. Известная организация в словаре
        "Роскомнадзор заблокировал сайт компании.",
        
        # 2. Сокращение в словаре
        "ФНС России опубликовала разъяснения по налогам.",
        
        # 3. Неизвестная организация (НЕТ в словаре Phrase Matcher)
        "Федеральная антимонопольная служба провела проверку.",
        
        # 4. Склонение известной организации
        "Сотрудники Министерства здравоохранения сообщили новости.",
        
        # 5. Коммерческая организация (для сравнения)
        "Компания Google представила новый продукт.",
        
        # 6. Сложный случай с контекстом
        "Представители МВД России и Apple обсудили сотрудничество."
    ]
    
    demo.compare_approaches(test_texts)
    
    # Выводы и рекомендации
    print(f"\n🎯 КЛЮЧЕВЫЕ ВЫВОДЫ:")
    print(f"{'='*50}")
    
    print(f"\n📚 PHRASE MATCHER лучше для:")
    print(f"   ✅ Точного поиска известных названий")
    print(f"   ✅ Высокой скорости обработки")
    print(f"   ✅ Минимизации ложных срабатываний")
    print(f"   ✅ Контроля над тем, что искать")
    
    print(f"\n🤖 SPACY NER лучше для:")
    print(f"   ✅ Обнаружения НЕИЗВЕСТНЫХ организаций")
    print(f"   ✅ Понимания контекста")
    print(f"   ✅ Работы с вариациями названий")
    print(f"   ✅ Обобщения на новые случаи")
    
    print(f"\n💡 РЕКОМЕНДАЦИЯ ДЛЯ ГОСОРГАНОВ:")
    print(f"   🎯 Использовать ОБА ПОДХОДА совместно:")
    print(f"   1. Phrase Matcher для известных названий (высокая точность)")
    print(f"   2. spaCy NER для неизвестных организаций (высокое покрытие)")
    print(f"   3. Объединять результаты с удалением дубликатов")

if __name__ == "__main__":
    run_comprehensive_demo()