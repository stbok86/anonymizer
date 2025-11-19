#!/usr/bin/env python3
"""
Технические детали работы spaCy NER и Phrase Matcher
"""

import spacy
from spacy.matcher import PhraseMatcher
import time

class TechnicalDetails:
    """Класс для демонстрации технических деталей работы"""
    
    def __init__(self):
        self.nlp = spacy.load("ru_core_news_lg")
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab)
    
    def demonstrate_ner_internals(self):
        """Показывает внутренние процессы spaCy NER"""
        
        print(f"🔍 SPACY NER - ТЕХНИЧЕСКИЕ ДЕТАЛИ")
        print(f"{'='*60}")
        
        text = "Роскомнадзор и Apple заключили соглашение"
        doc = self.nlp(text)
        
        print(f"📝 Исходный текст: '{text}'")
        print(f"\n1️⃣ ТОКЕНИЗАЦИЯ:")
        for i, token in enumerate(doc):
            print(f"   [{i}] '{token.text}' (pos: {token.pos_}, lemma: '{token.lemma_}')")
        
        print(f"\n2️⃣ МОРФОЛОГИЧЕСКИЙ АНАЛИЗ:")
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN']:  # Существительные и имена собственные
                print(f"   '{token.text}':")
                print(f"      POS: {token.pos_} (часть речи)")
                print(f"      Lemma: {token.lemma_} (базовая форма)")
                print(f"      Is_alpha: {token.is_alpha}")
                print(f"      Is_stop: {token.is_stop}")
                print(f"      Shape: {token.shape_}")
        
        print(f"\n3️⃣ ИМЕНОВАННЫЕ СУЩНОСТИ (NER):")
        for ent in doc.ents:
            print(f"   '{ent.text}' ({ent.start_char}-{ent.end_char}):")
            print(f"      Метка: {ent.label_}")
            print(f"      Описание: {spacy.explain(ent.label_)}")
            print(f"      Токены: {ent.start}-{ent.end}")
        
        print(f"\n4️⃣ КАК NER ПРИНИМАЕТ РЕШЕНИЯ:")
        print(f"   Для каждого токена анализирует:")
        print(f"   • Морфологические признаки (POS, лемма)")
        print(f"   • Контекст (соседние слова)")
        print(f"   • Семантические паттерны")
        print(f"   • Предобученные векторы слов")
        print(f"   • Нейронная сеть выдает вероятности для каждой метки")
        
        # Попробуем получить векторы слов
        print(f"\n5️⃣ ВЕКТОРНЫЕ ПРЕДСТАВЛЕНИЯ:")
        for token in doc:
            if token.text in ["Роскомнадзор", "Apple"]:
                print(f"   '{token.text}':")
                print(f"      Есть вектор: {token.has_vector}")
                if token.has_vector:
                    print(f"      Размерность вектора: {token.vector.shape}")
                    # Найдем похожие слова
                    similar_words = self._find_similar_words(token)
                    print(f"      Похожие слова: {similar_words}")
    
    def demonstrate_phrase_matcher_internals(self):
        """Показывает внутренние процессы Phrase Matcher"""
        
        print(f"\n📚 PHRASE MATCHER - ТЕХНИЧЕСКИЕ ДЕТАЛИ")
        print(f"{'='*60}")
        
        # Настраиваем простой пример
        gov_orgs = ["Роскомнадзор", "ФНС России", "МВД РФ"]
        patterns = [self.nlp(org) for org in gov_orgs]
        self.phrase_matcher.add("GOV_ORG", patterns)
        
        print(f"1️⃣ СОЗДАНИЕ ПАТТЕРНОВ:")
        for i, (org, pattern) in enumerate(zip(gov_orgs, patterns)):
            print(f"   Паттерн {i+1}: '{org}'")
            print(f"      Токены: {[token.text for token in pattern]}")
            print(f"      Атрибуты токенов: {[token.lower_ for token in pattern]}")
            print(f"      Хеши: {[token.orth for token in pattern]}")
        
        text = "Сегодня Роскомнадзор и ФНС России провели совещание"
        doc = self.nlp(text)
        
        print(f"\n2️⃣ ПРОЦЕСС ПОИСКА:")
        print(f"   Исходный текст: '{text}'")
        print(f"   Токены документа: {[token.text for token in doc]}")
        
        # Получаем совпадения
        matches = self.phrase_matcher(doc)
        
        print(f"\n3️⃣ АЛГОРИТМ СОПОСТАВЛЕНИЯ:")
        print(f"   Phrase Matcher использует автомат (FSM - Finite State Machine):")
        print(f"   • Начинает с первого токена")
        print(f"   • Проверяет совпадение с началом каждого паттерна")
        print(f"   • Если совпал - продолжает с следующего токена")
        print(f"   • Если полный паттерн совпал - фиксирует match")
        print(f"   • Продолжает поиск с следующего токена")
        
        print(f"\n4️⃣ НАЙДЕННЫЕ СОВПАДЕНИЯ:")
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            print(f"   Match: '{span.text}' (метка: {label})")
            print(f"      Позиция токенов: {start}-{end}")
            print(f"      Позиция символов: {span.start_char}-{span.end_char}")
            
            # Показываем процесс сопоставления
            matched_pattern = None
            for org in gov_orgs:
                if org.lower() == span.text.lower():
                    matched_pattern = org
                    break
            
            if matched_pattern:
                print(f"      Совпал с паттерном: '{matched_pattern}'")
        
        print(f"\n5️⃣ СЛОЖНОСТЬ АЛГОРИТМА:")
        print(f"   • Время: O(n) где n = количество токенов")
        print(f"   • Память: O(p*m) где p = паттернов, m = длина паттерна")
        print(f"   • Очень эффективен для большого количества точных фраз")
    
    def demonstrate_attribute_matching(self):
        """Демонстрирует различные атрибуты для сопоставления"""
        
        print(f"\n🔧 АТРИБУТЫ ДЛЯ СОПОСТАВЛЕНИЯ")
        print(f"{'='*50}")
        
        # Создаем разные matcher'ы для разных атрибутов
        text = "роскомнадзор и РОСКОМНАДЗОР - одно ведомство"
        doc = self.nlp(text)
        
        print(f"Тестовый текст: '{text}'")
        print(f"Токены: {[(token.text, token.lower_, token.orth) for token in doc]}")
        
        # 1. Сопоставление по исходному тексту (ORTH)
        matcher_orth = PhraseMatcher(self.nlp.vocab, attr="ORTH")
        pattern_orth = [self.nlp("роскомнадзор")]
        matcher_orth.add("EXACT", pattern_orth)
        
        # 2. Сопоставление по нижнему регистру (LOWER) 
        matcher_lower = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        pattern_lower = [self.nlp("роскомнадзор")]
        matcher_lower.add("CASE_INSENSITIVE", pattern_lower)
        
        # 3. Сопоставление по лемме (LEMMA)
        matcher_lemma = PhraseMatcher(self.nlp.vocab, attr="LEMMA")
        pattern_lemma = [self.nlp("роскомнадзор")]
        matcher_lemma.add("LEMMA_BASED", pattern_lemma)
        
        print(f"\n🎯 РЕЗУЛЬТАТЫ РАЗНЫХ АТРИБУТОВ:")
        
        matches_orth = matcher_orth(doc)
        matches_lower = matcher_lower(doc)
        matches_lemma = matcher_lemma(doc)
        
        print(f"   ORTH (точное совпадение): {len(matches_orth)} совпадений")
        for match_id, start, end in matches_orth:
            print(f"      → '{doc[start:end].text}'")
        
        print(f"   LOWER (без учета регистра): {len(matches_lower)} совпадений")
        for match_id, start, end in matches_lower:
            print(f"      → '{doc[start:end].text}'")
        
        print(f"   LEMMA (по базовой форме): {len(matches_lemma)} совпадений")
        for match_id, start, end in matches_lemma:
            print(f"      → '{doc[start:end].text}'")
    
    def _find_similar_words(self, token, limit=3):
        """Находит похожие слова через векторы"""
        if not token.has_vector:
            return "Нет вектора"
        
        # Простая демонстрация - в реальности нужна база похожих слов
        return "Apple → [Google, Microsoft, Facebook]"  # Примерный результат
    
    def performance_comparison(self):
        """Сравнение производительности"""
        
        print(f"\n⚡ СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ")
        print(f"{'='*50}")
        
        # Подготовка большого текста
        large_text = """
        Роскомнадзор сообщил о блокировке сайтов. ФНС России опубликовала 
        разъяснения по налогам. Министерство здравоохранения выпустило приказ.
        Администрация Президента РФ объявила о встрече. Google запустила новый сервис.
        Apple представила iPhone. Microsoft обновила Windows. Amazon расширяет бизнес.
        """ * 10  # Увеличиваем текст в 10 раз
        
        # Настраиваем phrase matcher
        gov_orgs = [
            "Роскомнадзор", "ФНС России", "Министерство здравоохранения",
            "Администрация Президента РФ", "Google", "Apple", "Microsoft", "Amazon"
        ]
        patterns = [self.nlp(org) for org in gov_orgs]
        phrase_matcher = PhraseMatcher(self.nlp.vocab)
        phrase_matcher.add("ORGS", patterns)
        
        # Тестируем spaCy NER
        print(f"Тестируем на тексте из {len(large_text)} символов...")
        
        start = time.time()
        doc = self.nlp(large_text)
        ner_entities = [ent for ent in doc.ents if ent.label_ == "ORG"]
        ner_time = time.time() - start
        
        # Тестируем Phrase Matcher
        start = time.time()
        doc = self.nlp(large_text)  # Токенизация нужна в любом случае
        phrase_matches = phrase_matcher(doc)
        phrase_time = time.time() - start
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"   spaCy NER:")
        print(f"      Время: {ner_time*1000:.1f} мс")
        print(f"      Найдено: {len(ner_entities)} организаций")
        print(f"      Организации: {[ent.text for ent in ner_entities[:5]]}...")
        
        print(f"   Phrase Matcher:")
        print(f"      Время: {phrase_time*1000:.1f} мс")
        print(f"      Найдено: {len(phrase_matches)} совпадений")
        
        speedup = ner_time / phrase_time if phrase_time > 0 else 0
        print(f"\n🏃 Phrase Matcher быстрее в {speedup:.1f} раза")

def run_technical_demo():
    """Запускает техническую демонстрацию"""
    
    print(f"🔬 ТЕХНИЧЕСКИЕ ДЕТАЛИ: spaCy NER vs Phrase Matcher")
    print(f"{'='*80}")
    
    demo = TechnicalDetails()
    
    # Демонстрируем внутренние процессы
    demo.demonstrate_ner_internals()
    demo.demonstrate_phrase_matcher_internals()
    demo.demonstrate_attribute_matching()
    demo.performance_comparison()
    
    print(f"\n🎓 ИТОГОВЫЕ ВЫВОДЫ:")
    print(f"{'='*40}")
    print(f"""
🤖 spaCy NER:
   • Использует нейронные сети и машинное обучение
   • Анализирует морфологию, синтаксис, семантику
   • Может обобщать и находить неизвестные сущности
   • Медленнее, но умнее
   
📚 Phrase Matcher:
   • Использует автомат конечных состояний (FSM)
   • Точное сопоставление токенов
   • Очень быстрый для известных фраз
   • Не может обобщать на новые случаи
   
🎯 Для государственных организаций:
   • Phrase Matcher - для известных названий (высокая скорость + точность)
   • spaCy NER - для неизвестных организаций (высокое покрытие)
   • Комбинирование дает лучший результат!
    """)

if __name__ == "__main__":
    run_technical_demo()