#!/usr/bin/env python3
"""
Профайлер производительности для NLP Service
Измеряет время выполнения различных этапов обработки
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics


@dataclass
class TimingEntry:
    """Запись времени выполнения операции"""
    operation: str
    duration_ms: float
    category: Optional[str] = None
    method: Optional[str] = None
    block_id: Optional[str] = None
    detections_count: int = 0
    
    
class PerformanceProfiler:
    """Профайлер для измерения производительности NLP сервиса"""
    
    def __init__(self):
        self.timings: List[TimingEntry] = []
        self.active_timers: Dict[str, float] = {}
        
    def start_timer(self, operation: str) -> None:
        """Запускает таймер для операции"""
        self.active_timers[operation] = time.perf_counter()
    
    def stop_timer(self, operation: str, **kwargs) -> float:
        """
        Останавливает таймер и записывает результат
        
        Returns:
            Длительность операции в миллисекундах
        """
        if operation not in self.active_timers:
            return 0.0
        
        start_time = self.active_timers.pop(operation)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        entry = TimingEntry(
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )
        self.timings.append(entry)
        
        return duration_ms
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по измерениям"""
        if not self.timings:
            return {"message": "No timing data collected"}
        
        # Группируем по операциям
        by_operation = defaultdict(list)
        for entry in self.timings:
            by_operation[entry.operation].append(entry.duration_ms)
        
        summary = {
            "total_duration_ms": sum(e.duration_ms for e in self.timings),
            "operations": {}
        }
        
        for operation, durations in by_operation.items():
            summary["operations"][operation] = {
                "count": len(durations),
                "total_ms": sum(durations),
                "avg_ms": statistics.mean(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "median_ms": statistics.median(durations)
            }
        
        # Группируем по категориям если есть
        by_category = defaultdict(list)
        for entry in self.timings:
            if entry.category:
                by_category[entry.category].append(entry.duration_ms)
        
        if by_category:
            summary["by_category"] = {}
            for category, durations in by_category.items():
                summary["by_category"][category] = {
                    "count": len(durations),
                    "total_ms": sum(durations),
                    "avg_ms": statistics.mean(durations)
                }
        
        # Группируем по методам если есть
        by_method = defaultdict(list)
        for entry in self.timings:
            if entry.method:
                by_method[entry.method].append(entry.duration_ms)
        
        if by_method:
            summary["by_method"] = {}
            for method, durations in by_method.items():
                summary["by_method"][method] = {
                    "count": len(durations),
                    "total_ms": sum(durations),
                    "avg_ms": statistics.mean(durations)
                }
        
        return summary
    
    def get_bottlenecks(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Возвращает топ самых медленных операций
        
        Args:
            top_n: Количество операций для вывода
        """
        sorted_timings = sorted(self.timings, key=lambda x: x.duration_ms, reverse=True)
        
        return [
            {
                "operation": t.operation,
                "duration_ms": t.duration_ms,
                "category": t.category,
                "method": t.method,
                "detections_count": t.detections_count
            }
            for t in sorted_timings[:top_n]
        ]
    
    def print_summary(self) -> None:
        """Выводит сводку в консоль"""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("PERFORMANCE PROFILING SUMMARY")
        print("="*80)
        
        print(f"\nTotal duration: {summary['total_duration_ms']:.2f} ms")
        
        print("\n--- Operations ---")
        for op, stats in sorted(summary['operations'].items(), 
                               key=lambda x: x[1]['total_ms'], 
                               reverse=True):
            print(f"\n{op}:")
            print(f"  Count: {stats['count']}")
            print(f"  Total: {stats['total_ms']:.2f} ms")
            print(f"  Avg: {stats['avg_ms']:.2f} ms")
            print(f"  Min/Max: {stats['min_ms']:.2f} / {stats['max_ms']:.2f} ms")
        
        if 'by_category' in summary:
            print("\n--- By Category ---")
            for cat, stats in sorted(summary['by_category'].items(),
                                    key=lambda x: x[1]['total_ms'],
                                    reverse=True):
                print(f"{cat}: {stats['total_ms']:.2f} ms ({stats['count']} calls, avg {stats['avg_ms']:.2f} ms)")
        
        if 'by_method' in summary:
            print("\n--- By Method ---")
            for method, stats in sorted(summary['by_method'].items(),
                                       key=lambda x: x[1]['total_ms'],
                                       reverse=True):
                print(f"{method}: {stats['total_ms']:.2f} ms ({stats['count']} calls, avg {stats['avg_ms']:.2f} ms)")
        
        print("\n--- Top 10 Bottlenecks ---")
        for i, bottleneck in enumerate(self.get_bottlenecks(10), 1):
            print(f"{i}. {bottleneck['operation']}: {bottleneck['duration_ms']:.2f} ms " +
                  f"[{bottleneck.get('category', 'N/A')}] " +
                  f"({bottleneck.get('detections_count', 0)} detections)")
        
        print("\n" + "="*80)
    
    def export_to_json(self, filepath: str) -> None:
        """Экспортирует результаты в JSON файл"""
        data = {
            "summary": self.get_summary(),
            "bottlenecks": self.get_bottlenecks(20),
            "all_timings": [asdict(t) for t in self.timings]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def reset(self) -> None:
        """Очищает все измерения"""
        self.timings.clear()
        self.active_timers.clear()
