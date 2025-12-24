# coding: utf-8
"""
Модуль для загрузки справочников русских имен и фамилий (имена, фамилии, отчества)
"""
import os

def load_dictionary(file_path):
    """Загружает строки из текстового файла в set (без пустых строк, с trim)"""
    names = set()
    if not os.path.exists(file_path):
        return names
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name:
                # Приводим все "ё" к "е" для унификации
                names.add(name.replace("ё", "е").replace("Ё", "Е"))
    return names
