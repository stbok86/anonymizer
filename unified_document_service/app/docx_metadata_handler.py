#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Компонент для работы с метаданными DOCX документов (docProps/core.xml)
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import tempfile
import os

class DocxMetadataHandler:
    """
    🎯 КРИТИЧНО: Обработчик метаданных DOCX документа для анонимизации динамических полей в заголовках
    
    DOCX заголовки могут содержать поля, которые получают данные из:
    - docProps/core.xml (название, автор, тема и т.д.)
    - docProps/app.xml (приложение, версия)
    - docProps/custom.xml (пользовательские свойства)
    
    Эти поля отображаются в заголовках как:
    - { DOCPROPERTY "Title" }
    - { AUTHOR }
    - { SUBJECT }
    - и т.д.
    """
    
    def __init__(self, docx_path: str):
        """
        Инициализация обработчика метаданных
        
        Args:
            docx_path: Путь к DOCX файлу
        """
        self.docx_path = docx_path
        self.metadata = {}
        self.custom_properties = {}
        
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Извлекает все метаданные из DOCX файла
        
        Returns:
            Словарь с метаданными документа
        """
        print(f"📋 [METADATA] Извлечение метаданных из: {os.path.basename(self.docx_path)}")
        
        try:
            with zipfile.ZipFile(self.docx_path, 'r') as docx_zip:
                # Извлекаем основные метаданные (core.xml)
                core_metadata = self._extract_core_metadata(docx_zip)
                
                # Извлекаем метаданные приложения (app.xml)
                app_metadata = self._extract_app_metadata(docx_zip)
                
                # Извлекаем пользовательские свойства (custom.xml)
                custom_metadata = self._extract_custom_metadata(docx_zip)
                
                # Объединяем все метаданные
                self.metadata = {
                    'core': core_metadata,
                    'app': app_metadata,
                    'custom': custom_metadata
                }
                
                print(f"📋 [METADATA] ✅ Извлечено метаданных:")
                print(f"  📌 Core properties: {len(core_metadata)}")
                print(f"  📌 App properties: {len(app_metadata)}")
                print(f"  📌 Custom properties: {len(custom_metadata)}")
                
                return self.metadata
                
        except Exception as e:
            print(f"📋 [METADATA] ❌ Ошибка при извлечении метаданных: {str(e)}")
            return {}
    
    def _extract_core_metadata(self, docx_zip: zipfile.ZipFile) -> Dict[str, str]:
        """
        Извлекает основные метаданные из docProps/core.xml
        """
        core_metadata = {}
        
        try:
            if 'docProps/core.xml' in docx_zip.namelist():
                core_xml = docx_zip.read('docProps/core.xml')
                root = ET.fromstring(core_xml)
                
                # Определяем namespace для Dublin Core
                namespaces = {
                    'dc': 'http://purl.org/dc/elements/1.1/',
                    'dcterms': 'http://purl.org/dc/terms/',
                    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
                }
                
                # Извлекаем стандартные свойства
                properties_map = {
                    'title': './/dc:title',
                    'subject': './/dc:subject', 
                    'creator': './/dc:creator',
                    'description': './/dc:description',
                    'keywords': './/cp:keywords',
                    'category': './/cp:category',
                    'lastModifiedBy': './/cp:lastModifiedBy',
                    'created': './/dcterms:created',
                    'modified': './/dcterms:modified'
                }
                
                for prop_name, xpath in properties_map.items():
                    element = root.find(xpath, namespaces)
                    if element is not None and element.text:
                        core_metadata[prop_name] = element.text
                        print(f"📋 [CORE] {prop_name}: '{element.text}'")
                        
        except Exception as e:
            print(f"📋 [CORE] ⚠️ Ошибка при извлечении core.xml: {str(e)}")
            
        return core_metadata
    
    def _extract_app_metadata(self, docx_zip: zipfile.ZipFile) -> Dict[str, str]:
        """
        Извлекает метаданные приложения из docProps/app.xml
        """
        app_metadata = {}
        
        try:
            if 'docProps/app.xml' in docx_zip.namelist():
                app_xml = docx_zip.read('docProps/app.xml')
                root = ET.fromstring(app_xml)
                
                # Определяем namespace
                namespaces = {
                    'app': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
                }
                
                # Извлекаем свойства приложения
                properties_map = {
                    'application': './/app:Application',
                    'appVersion': './/app:AppVersion',
                    'company': './/app:Company',
                    'manager': './/app:Manager',
                    'template': './/app:Template'
                }
                
                for prop_name, xpath in properties_map.items():
                    element = root.find(xpath, namespaces)
                    if element is not None and element.text:
                        app_metadata[prop_name] = element.text
                        print(f"📋 [APP] {prop_name}: '{element.text}'")
                        
        except Exception as e:
            print(f"📋 [APP] ⚠️ Ошибка при извлечении app.xml: {str(e)}")
            
        return app_metadata
    
    def _extract_custom_metadata(self, docx_zip: zipfile.ZipFile) -> Dict[str, str]:
        """
        Извлекает пользовательские свойства из docProps/custom.xml
        """
        custom_metadata = {}
        
        try:
            if 'docProps/custom.xml' in docx_zip.namelist():
                custom_xml = docx_zip.read('docProps/custom.xml')
                root = ET.fromstring(custom_xml)
                
                # Определяем namespace
                namespaces = {
                    'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
                }
                
                # Извлекаем пользовательские свойства
                for prop in root.findall('.//property', namespaces):
                    name = prop.get('name')
                    if name:
                        # Ищем значение в разных типах
                        value_element = (prop.find('.//vt:lpwstr', namespaces) or 
                                       prop.find('.//vt:lpstr', namespaces) or
                                       prop.find('.//vt:i4', namespaces) or
                                       prop.find('.//vt:bool', namespaces))
                        
                        if value_element is not None and value_element.text:
                            custom_metadata[name] = value_element.text
                            print(f"📋 [CUSTOM] {name}: '{value_element.text}'")
                            
        except Exception as e:
            print(f"📋 [CUSTOM] ⚠️ Ошибка при извлечении custom.xml: {str(e)}")
            
        return custom_metadata
    
    def find_sensitive_metadata(self, replacements: List[Dict]) -> List[Dict]:
        """
        Находит чувствительные данные в метаданных документа
        
        Args:
            replacements: Список замен из основного анализа
            
        Returns:
            Список найденных чувствительных метаданных с информацией для замены
        """
        print(f"🔍 [METADATA] Поиск чувствительных данных в метаданных...")
        
        if not self.metadata:
            print(f"🔍 [METADATA] ⚠️ Метаданные не загружены")
            return []
        
        sensitive_metadata = []
        
        # Создаем словарь оригинальных значений для быстрого поиска
        original_values = {}
        for replacement in replacements:
            original_value = replacement.get('original_value', '')
            if original_value:
                original_values[original_value] = replacement
        
        # Проверяем все секции метаданных
        for section_name, section_data in self.metadata.items():
            if not isinstance(section_data, dict):
                continue
                
            for prop_name, prop_value in section_data.items():
                if not prop_value:
                    continue
                
                print(f"🔍 [METADATA] Проверяем {section_name}.{prop_name}: '{prop_value}'")
                
                # Ищем точные совпадения
                if prop_value in original_values:
                    original_replacement = original_values[prop_value]
                    
                    sensitive_metadata.append({
                        'metadata_section': section_name,
                        'metadata_property': prop_name,
                        'original_value': prop_value,
                        'uuid': original_replacement.get('uuid'),
                        'category': original_replacement.get('category'),
                        'confidence': 1.0,  # 100% уверенность для точного совпадения
                        'source': f'metadata_{section_name}',
                        'related_replacement': original_replacement
                    })
                    
                    print(f"🔍 [METADATA] ✅ Найдены чувствительные данные: {section_name}.{prop_name} = '{prop_value}'")
                
                # Ищем частичные совпадения (подстроки)
                # ВАЖНО: Ищем ВСЕ совпадения, не останавливаемся на первом
                else:
                    found_matches = []
                    for original_value, replacement in original_values.items():
                        if len(original_value) >= 3 and original_value in prop_value:
                            found_matches.append({
                                'metadata_section': section_name,
                                'metadata_property': prop_name,
                                'original_value': prop_value,  # Полное значение метаданных
                                'partial_match': original_value,  # Найденная подстрока
                                'uuid': replacement.get('uuid'),
                                'category': replacement.get('category'),
                                'confidence': 0.8,  # Немного меньше уверенности для частичного совпадения
                                'source': f'metadata_{section_name}_partial',
                                'related_replacement': replacement
                            })
                            
                            print(f"🔍 [METADATA] ✅ Найдено частичное совпадение: {section_name}.{prop_name} содержит '{original_value}'")
                    
                    # Добавляем все найденные совпадения
                    sensitive_metadata.extend(found_matches)
        
        print(f"🔍 [METADATA] Найдено чувствительных метаданных: {len(sensitive_metadata)}")
        return sensitive_metadata
    
    def anonymize_metadata_in_docx(self, docx_path: str, output_path: str, 
                                 sensitive_metadata: List[Dict]) -> bool:
        """
        🎯 КРИТИЧНО: Анонимизирует метаданные прямо в DOCX файле
        
        Args:
            docx_path: Путь к исходному DOCX файлу
            output_path: Путь для сохранения анонимизированного файла
            sensitive_metadata: Список найденных чувствительных метаданных
            
        Returns:
            True если анонимизация прошла успешно
        """
        print(f"🔧 [METADATA] Начинаем анонимизацию метаданных...")
        print(f"📄 Input: {os.path.basename(docx_path)}")
        print(f"📄 Output: {os.path.basename(output_path)}")
        print(f"🎯 Замен в метаданных: {len(sensitive_metadata)}")
        if not sensitive_metadata:
            import shutil
            shutil.copy2(docx_path, output_path)
            print(f"🔧 [METADATA] ✅ Нет чувствительных метаданных, файл скопирован")
            return True
        try:
            print(f"🔧 [METADATA] Список замен для метаданных:")
            for i, item in enumerate(sensitive_metadata):
                print(f"    {i+1}. [{item.get('metadata_section')}] '{item.get('original_value')}' → '{item.get('uuid')}' (категория: {item.get('category')})")
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(docx_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                replacements_made = 0
                # Проверяем наличие файлов метаданных
                core_xml_path = os.path.join(temp_dir, 'docProps', 'core.xml')
                app_xml_path = os.path.join(temp_dir, 'docProps', 'app.xml')
                custom_xml_path = os.path.join(temp_dir, 'docProps', 'custom.xml')
                print(f"🔧 [METADATA] Проверяем наличие файлов:")
                print(f"    core.xml:   {'OK' if os.path.exists(core_xml_path) else 'NOT FOUND'}")
                print(f"    app.xml:    {'OK' if os.path.exists(app_xml_path) else 'NOT FOUND'}")
                print(f"    custom.xml: {'OK' if os.path.exists(custom_xml_path) else 'NOT FOUND'}")
                # Анонимизируем core.xml
                if os.path.exists(core_xml_path):
                    print(f"🔧 [METADATA] Обработка core.xml...")
                    replaced = self._anonymize_xml_file(core_xml_path, sensitive_metadata, 'core')
                    print(f"🔧 [METADATA] Замен в core.xml: {replaced}")
                    replacements_made += replaced
                # Анонимизируем app.xml
                if os.path.exists(app_xml_path):
                    print(f"🔧 [METADATA] Обработка app.xml...")
                    replaced = self._anonymize_xml_file(app_xml_path, sensitive_metadata, 'app')
                    print(f"🔧 [METADATA] Замен в app.xml: {replaced}")
                    replacements_made += replaced
                # Анонимизируем custom.xml
                if os.path.exists(custom_xml_path):
                    print(f"🔧 [METADATA] Обработка custom.xml...")
                    replaced = self._anonymize_xml_file(custom_xml_path, sensitive_metadata, 'custom')
                    print(f"🔧 [METADATA] Замен в custom.xml: {replaced}")
                    replacements_made += replaced
                # Пересобираем docx
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, temp_dir)
                            zip_out.write(file_path, arc_path)
                print(f"🔧 [METADATA] ✅ Анонимизация завершена. Замен в метаданных: {replacements_made}")
            return True
        except Exception as e:
            print(f"🔧 [METADATA] ❌ Ошибка при анонимизации метаданных: {str(e)}")
            import traceback
            print(f"🔧 [METADATA] Traceback: {traceback.format_exc()}")
            return False
    
    def _anonymize_xml_file(self, xml_path: str, sensitive_metadata: List[Dict], section: str) -> int:
        """
        Анонимизирует конкретный XML файл метаданных
        
        Args:
            xml_path: Путь к XML файлу
            sensitive_metadata: Список чувствительных метаданных
            section: Секция метаданных ('core', 'app', 'custom')
            
        Returns:
            Количество выполненных замен
        """
        if not os.path.exists(xml_path):
            return 0
            
        try:
            # Читаем XML файл как текст (для простоты замен)
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            print(f"\n===== [DEBUG] Содержимое {os.path.basename(xml_path)} ДО замены =====\n{xml_content[:2000]}\n...\n")

            original_content = xml_content
            replacements_made = 0

            print(f"[DEBUG] Список замен для секции '{section}':")
            for metadata_item in sensitive_metadata:
                if metadata_item.get('metadata_section') == section:
                    print(f"    - original_value: '{metadata_item.get('original_value')}', uuid: '{metadata_item.get('uuid')}', partial_match: '{metadata_item.get('partial_match')}'")

            # Применяем замены для данной секции
            for metadata_item in sensitive_metadata:
                if metadata_item.get('metadata_section') == section:
                    original_value = metadata_item.get('original_value', '')
                    uuid = metadata_item.get('uuid', '')
                    partial_match = metadata_item.get('partial_match')

                    if partial_match:
                        # Частичная замена (заменяем только найденную подстрокe)
                        if partial_match in xml_content:
                            print(f"[DEBUG] Найден partial_match '{partial_match}' в XML, выполняем замену на '{uuid}'")
                            xml_content = xml_content.replace(partial_match, uuid)
                            replacements_made += 1
                            print(f"🔧 [XML-{section.upper()}] Частичная замена: '{partial_match}' → '{uuid}'")
                        else:
                            print(f"[DEBUG] partial_match '{partial_match}' НЕ найден в XML!")
                    else:
                        # Полная замена
                        if original_value in xml_content:
                            print(f"[DEBUG] Найден original_value '{original_value}' в XML, выполняем замену на '{uuid}'")
                            xml_content = xml_content.replace(original_value, uuid)
                            replacements_made += 1
                            print(f"🔧 [XML-{section.upper()}] Полная замена: '{original_value}' → '{uuid}'")
                        else:
                            print(f"[DEBUG] original_value '{original_value}' НЕ найден в XML!")

            # Сохраняем измененный XML файл
            if xml_content != original_content:
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)

                print(f"\n===== [DEBUG] Содержимое {os.path.basename(xml_path)} ПОСЛЕ замены =====\n{xml_content[:2000]}\n...\n")
                print(f"🔧 [XML-{section.upper()}] ✅ Файл обновлен: {os.path.basename(xml_path)}")
            else:
                print(f"[DEBUG] Изменений в {os.path.basename(xml_path)} не было!")

            return replacements_made

        except Exception as e:
            print(f"🔧 [XML-{section.upper()}] ❌ Ошибка при анонимизации {xml_path}: {str(e)}")
            return 0
    
    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Возвращает краткую сводку по метаданным документа
        """
        if not self.metadata:
            return {}
            
        summary = {
            'total_properties': 0,
            'sections': {}
        }
        
        for section_name, section_data in self.metadata.items():
            if isinstance(section_data, dict):
                section_count = len([v for v in section_data.values() if v])
                summary['sections'][section_name] = section_count
                summary['total_properties'] += section_count
        
        return summary


# Тестирование
def test_metadata_handler():
    """
    Тестирует обработчик метаданных
    """
    test_file = r"C:\Projects\Anonymizer\unified_document_service\test_docs\test_01_1_4_SD1-4.docx"
    
    if not os.path.exists(test_file):
        print(f"❌ Тестовый файл не найден: {test_file}")
        return
    
    print("🧪 ТЕСТИРОВАНИЕ ОБРАБОТЧИКА МЕТАДАННЫХ")
    print("=" * 50)
    
    handler = DocxMetadataHandler(test_file)
    
    # Извлекаем метаданные
    metadata = handler.extract_metadata()
    
    # Выводим сводку
    summary = handler.get_metadata_summary()
    print(f"\n📊 СВОДКА МЕТАДАННЫХ:")
    print(f"  📌 Всего свойств: {summary['total_properties']}")
    for section, count in summary['sections'].items():
        print(f"  📌 {section}: {count} свойств")
    
    # Создаем тестовые замены
    test_replacements = [
        {
            'original_value': 'Test Document',
            'uuid': 'test-uuid-001',
            'category': 'document_title'
        },
        {
            'original_value': 'Test Author', 
            'uuid': 'test-uuid-002',
            'category': 'person_name'
        }
    ]
    
    # Ищем чувствительные метаданные
    sensitive = handler.find_sensitive_metadata(test_replacements)
    
    print(f"\n🎯 НАЙДЕНО ЧУВСТВИТЕЛЬНЫХ МЕТАДАННЫХ: {len(sensitive)}")
    for item in sensitive:
        print(f"  🔍 {item['metadata_section']}.{item['metadata_property']}: '{item['original_value'][:50]}{'...' if len(item['original_value']) > 50 else ''}'")

if __name__ == "__main__":
    test_metadata_handler()