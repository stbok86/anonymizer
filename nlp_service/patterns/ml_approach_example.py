#!/usr/bin/env python3
"""
Пример ML подхода для детекции государственных организаций
"""

import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
from typing import List, Tuple, Dict, Any

class GovernmentOrgMLDetector:
    """ML детектор государственных организаций на основе spaCy"""
    
    def __init__(self):
        # Создаем пустую модель для обучения
        self.nlp = spacy.blank("ru")
        
        # Добавляем компонент NER
        if "ner" not in self.nlp.pipe_names:
            ner = self.nlp.add_pipe("ner", last=True)
        else:
            ner = self.nlp.get_pipe("ner")
        
        # Добавляем кастомный лейбл для государственных организаций
        ner.add_label("GOV_ORG")
        
        self.is_trained = False
    
    def prepare_training_data(self) -> List[Tuple[str, Dict]]:
        """
        Подготавливает тренировочные данные
        
        В реальности эти данные собираются из:
        - Размеченных документов
        - Открытых справочников
        - Экспертной разметки
        """
        
        training_data = [
            # Федеральные органы
            ("МВД России проводит операцию", {
                "entities": [(0, 10, "GOV_ORG")]
            }),
            ("Роскомнадзор заблокировал сайт", {
                "entities": [(0, 12, "GOV_ORG")]
            }),
            ("Федеральная налоговая служба объявила", {
                "entities": [(0, 27, "GOV_ORG")]
            }),
            ("Минздрав России утвердил программу", {
                "entities": [(0, 15, "GOV_ORG")]
            }),
            
            # Региональные органы
            ("Правительство Пермского края приняло решение", {
                "entities": [(0, 27, "GOV_ORG")]
            }),
            ("Департамент образования города Москвы объявил", {
                "entities": [(0, 35, "GOV_ORG")]
            }),
            ("Администрация Свердловской области сообщила", {
                "entities": [(0, 31, "GOV_ORG")]
            }),
            
            # Муниципальные органы
            ("Городская дума Перми приняла закон", {
                "entities": [(0, 17, "GOV_ORG")]
            }),
            ("Мэрия города Екатеринбурга планирует", {
                "entities": [(0, 24, "GOV_ORG")]
            }),
            
            # Негативные примеры (НЕ госорганы)
            ("ООО Рога и Копыта заключило договор", {
                "entities": []
            }),
            ("АО Газпром увеличило прибыль", {
                "entities": []
            }),
            ("Компания Apple представила новинку", {
                "entities": []
            }),
        ]
        
        return training_data
    
    def train_model(self, iterations: int = 100):
        """Обучает модель на подготовленных данных"""
        
        training_data = self.prepare_training_data()
        
        print(f"🎓 Начинаем обучение ML модели ({iterations} итераций)...")
        
        # Отключаем другие компоненты во время обучения
        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        with self.nlp.disable_pipes(*other_pipes):
            
            # Инициализируем модель
            self.nlp.begin_training()
            
            for iteration in range(iterations):
                random.shuffle(training_data)
                losses = {}
                
                # Создаем батчи для обучения
                batches = minibatch(training_data, size=compounding(4.0, 32.0, 1.001))
                
                for batch in batches:
                    examples = []
                    for text, annotations in batch:
                        doc = self.nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        examples.append(example)
                    
                    # Обновляем модель
                    self.nlp.update(examples, losses=losses, drop=0.3)
                
                if iteration % 20 == 0:
                    print(f"   Итерация {iteration}: потери = {losses.get('ner', 0):.4f}")
        
        self.is_trained = True
        print("✅ Обучение завершено!")
    
    def detect_government_orgs(self, text: str) -> List[Dict[str, Any]]:
        """Детектирует государственные организации используя обученную модель"""
        
        if not self.is_trained:
            raise ValueError("Модель не обучена! Вызовите train_model() сначала.")
        
        doc = self.nlp(text)
        detections = []
        
        for ent in doc.ents:
            if ent.label_ == "GOV_ORG":
                detection = {
                    'category': 'government_org',
                    'original_value': ent.text,
                    'confidence': self._calculate_ml_confidence(ent),
                    'position': {
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'method': 'ml_trained_model',
                    'model_confidence': getattr(ent, 'confidence', 0.8)
                }
                detections.append(detection)
        
        return detections
    
    def _calculate_ml_confidence(self, ent) -> float:
        """Рассчитывает уверенность для ML детекции"""
        # В реальной модели это может включать:
        # - Вероятности из модели
        # - Анализ контекста
        # - Проверку в справочниках
        base_confidence = 0.8
        
        # Бонус за длину
        length_bonus = min(0.15, len(ent.text.split()) * 0.02)
        
        return min(0.95, base_confidence + length_bonus)
    
    def evaluate_model(self, test_data: List[Tuple[str, Dict]]) -> Dict[str, float]:
        """Оценивает качество модели на тестовых данных"""
        
        if not self.is_trained:
            raise ValueError("Модель не обучена!")
        
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        for text, annotations in test_data:
            # Предсказания модели
            predicted = self.detect_government_orgs(text)
            predicted_entities = set((det['position']['start'], det['position']['end']) 
                                   for det in predicted)
            
            # Истинные аннотации
            true_entities = set((start, end) for start, end, label in annotations.get('entities', []) 
                              if label == 'GOV_ORG')
            
            # Подсчитываем метрики
            true_positives += len(predicted_entities & true_entities)
            false_positives += len(predicted_entities - true_entities)
            false_negatives += len(true_entities - predicted_entities)
        
        # Рассчитываем precision, recall, F1
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }

def demonstrate_ml_approach():
    """Демонстрирует ML подход для детекции госорганов"""
    
    print("🤖 ДЕМОНСТРАЦИЯ MACHINE LEARNING ПОДХОДА")
    print("=" * 60)
    
    # Создаем и обучаем модель
    detector = GovernmentOrgMLDetector()
    detector.train_model(iterations=50)  # Быстрое обучение для демо
    
    # Тестируем на новых примерах
    test_texts = [
        "ФСБ России провела спецоперацию.",
        "Минфин РФ представил отчет.",
        "Департамент здравоохранения Москвы сообщил.",
        "ООО Лукойл увеличил добычу.",  # Не госорган
        "Правительство Татарстана утвердило бюджет."
    ]
    
    print(f"\n🧪 ТЕСТИРОВАНИЕ НА НОВЫХ ПРИМЕРАХ:")
    print("-" * 40)
    
    total_detected = 0
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 Тест {i}: {text}")
        detections = detector.detect_government_orgs(text)
        
        if detections:
            print(f"✅ ML модель нашла {len(detections)} госорганов:")
            for det in detections:
                print(f"   • '{det['original_value']}' (confidence: {det['confidence']:.3f})")
            total_detected += len(detections)
        else:
            print("❌ Госорганы не найдены")
    
    print(f"\n📊 ИТОГО: ML модель обнаружила {total_detected} государственных организаций")
    
    # Объясняем преимущества
    print(f"\n🎯 ПРЕИМУЩЕСТВА ML ПОДХОДА:")
    print(f"✅ Автоматически изучает паттерны из данных")
    print(f"✅ Адаптируется к новым форматам")
    print(f"✅ Учитывает контекст и семантику")
    print(f"✅ Может обобщать на неизвестные примеры")
    print(f"✅ Улучшается с добавлением новых данных")
    
    print(f"\n⚠️ ТРЕБОВАНИЯ:")
    print(f"• Качественные размеченные данные (1000+ примеров)")
    print(f"• Вычислительные ресурсы для обучения")
    print(f"• Экспертиза в области ML")
    print(f"• Регулярное переобучение модели")

if __name__ == "__main__":
    demonstrate_ml_approach()