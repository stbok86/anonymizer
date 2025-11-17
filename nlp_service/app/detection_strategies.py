#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Стратегии для централизованного управления методами обнаружения данных
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set
import uuid


class DetectionStrategy(ABC):
    """Базовый класс для стратегий комбинирования результатов детекции"""
    
    def __init__(self, config_settings: Dict[str, Any]):
        """
        Args:
            config_settings: Настройки стратегии из конфигурации
        """
        self.settings = config_settings
    
    @abstractmethod
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Комбинирует результаты разных методов согласно стратегии
        
        Args:
            results_by_method: Словарь {method_name: [detections]}
            
        Returns:
            Объединенный список детекций
        """
        pass
    
    def _remove_duplicates(self, detections: List[Dict[str, Any]], 
                          threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Удаляет дубликаты на основе пересечения позиций"""
        unique_detections = []
        
        for detection in sorted(detections, key=lambda x: x['confidence'], reverse=True):
            is_duplicate = False
            
            for existing in unique_detections:
                overlap = self._calculate_overlap(detection['position'], existing['position'])
                if overlap >= threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_detections.append(detection)
        
        return unique_detections
    
    def _calculate_overlap(self, pos1: Dict[str, int], pos2: Dict[str, int]) -> float:
        """Рассчитывает коэффициент пересечения двух позиций"""
        start1, end1 = pos1['start'], pos1['end']
        start2, end2 = pos2['start'], pos2['end']
        
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return 0.0
        
        overlap_length = overlap_end - overlap_start
        total_length = min(end1 - start1, end2 - start2)
        
        return overlap_length / total_length if total_length > 0 else 0.0


class BestConfidenceStrategy(DetectionStrategy):
    """Стратегия выбора результата с наивысшей уверенностью"""
    
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        all_detections = []
        
        # Собираем все детекции
        for method_name, detections in results_by_method.items():
            all_detections.extend(detections)
        
        if not all_detections:
            return []
        
        # Сортируем по confidence
        all_detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Удаляем дубликаты, предпочитая результаты с высокой confidence
        unique_detections = self._remove_duplicates(
            all_detections, 
            self.settings.get('dedup_threshold', 0.8)
        )
        
        # Предпочитаем более длинные совпадения при равной confidence
        if self.settings.get('prefer_longer_matches', True):
            unique_detections = self._prefer_longer_matches(unique_detections)
        
        return unique_detections
    
    def _prefer_longer_matches(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """При равной confidence предпочитает более длинные совпадения"""
        def sort_key(detection):
            length = detection['position']['end'] - detection['position']['start']
            return (-detection['confidence'], -length)
        
        return sorted(detections, key=sort_key)


class CombineAllStrategy(DetectionStrategy):
    """Стратегия объединения результатов всех методов"""
    
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        all_detections = []
        
        # Собираем все детекции
        for method_name, detections in results_by_method.items():
            all_detections.extend(detections)
        
        if not all_detections:
            return []
        
        # Если настройка combine_overlapping включена, удаляем дубликаты
        if self.settings.get('combine_overlapping', True):
            threshold = self.settings.get('dedup_threshold', 0.8)
            all_detections = self._remove_duplicates(all_detections, threshold)
        
        # Сортируем по позиции для стабильности
        return sorted(all_detections, key=lambda x: x['position']['start'])


class FirstMatchStrategy(DetectionStrategy):
    """Стратегия возврата первого найденного результата"""
    
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        min_confidence = self.settings.get('min_confidence_threshold', 0.7)
        
        # Проверяем методы в порядке приоритета
        for method_name in sorted(results_by_method.keys()):
            detections = results_by_method[method_name]
            
            for detection in detections:
                if detection['confidence'] >= min_confidence:
                    return [detection]
        
        return []


class WeightedAverageStrategy(DetectionStrategy):
    """Стратегия взвешенного усреднения результатов"""
    
    def combine_results(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        method_weights = self.settings.get('method_weights', {})
        
        # Группируем детекции по пересекающимся позициям
        grouped_detections = self._group_overlapping_detections(results_by_method)
        
        combined_results = []
        for group in grouped_detections:
            combined_detection = self._combine_group_weighted(group, method_weights)
            if combined_detection:
                combined_results.append(combined_detection)
        
        return combined_results
    
    def _group_overlapping_detections(self, results_by_method: Dict[str, List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
        """Группирует пересекающиеся детекции"""
        all_detections = []
        for detections in results_by_method.values():
            all_detections.extend(detections)
        
        groups = []
        used = set()
        
        for i, detection in enumerate(all_detections):
            if i in used:
                continue
            
            group = [detection]
            used.add(i)
            
            for j, other_detection in enumerate(all_detections[i+1:], i+1):
                if j in used:
                    continue
                
                if self._calculate_overlap(detection['position'], other_detection['position']) > 0.3:
                    group.append(other_detection)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _combine_group_weighted(self, group: List[Dict[str, Any]], 
                               method_weights: Dict[str, float]) -> Optional[Dict[str, Any]]:
        """Комбинирует группу детекций с весовым усреднением"""
        if not group:
            return None
        
        if len(group) == 1:
            return group[0]
        
        # Вычисляем взвешенную confidence
        total_weight = 0
        weighted_confidence = 0
        
        for detection in group:
            method = detection.get('method', 'unknown')
            weight = method_weights.get(method, 0.5)
            weighted_confidence += detection['confidence'] * weight
            total_weight += weight
        
        if total_weight == 0:
            return group[0]  # Fallback
        
        # Выбираем детекцию с наибольшим весом как базовую
        best_detection = max(group, key=lambda x: method_weights.get(x.get('method', 'unknown'), 0.5))
        
        # Создаем комбинированную детекцию
        combined = best_detection.copy()
        combined['confidence'] = weighted_confidence / total_weight
        combined['method'] = 'weighted_combination'
        combined['uuid'] = str(uuid.uuid4())
        
        return combined


class DetectionStrategyFactory:
    """Фабрика для создания стратегий детекции"""
    
    STRATEGIES = {
        'best_confidence': BestConfidenceStrategy,
        'combine_all': CombineAllStrategy,
        'first_match': FirstMatchStrategy,
        'weighted_average': WeightedAverageStrategy
    }
    
    @classmethod
    def create_strategy(cls, strategy_name: str, config_settings: Dict[str, Any]) -> DetectionStrategy:
        """
        Создает стратегию по имени
        
        Args:
            strategy_name: Имя стратегии
            config_settings: Настройки стратегии
            
        Returns:
            Экземпляр стратегии
        """
        if strategy_name not in cls.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy_name}. Available: {list(cls.STRATEGIES.keys())}")
        
        strategy_class = cls.STRATEGIES[strategy_name]
        return strategy_class(config_settings)