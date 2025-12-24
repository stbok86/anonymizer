#!/usr/bin/env python3
"""
STREAMLIT WEB UI ДЛЯ DOCUMENT ANONYMIZER
Веб-интерфейс для анонимизации документов через Unified Document Service

Архитектура:
- Frontend (Streamlit) - этот файл
- Backend (FastAPI) - unified_document_service
- Интеграция через HTTP API или прямые вызовы модулей

Функционал согласно сценарию использования:
1. Загрузка Word-документа через UI
2. Анализ и выявление чувствительных данных  
3. Отображение найденных данных с возможностью подтверждения/корректировки
4. Генерация таблицы замен с комментариями пользователя
5. Псевдоанонимизация документа с цветовым выделением
6. Скачивание результатов: Word + Excel отчет
"""

import streamlit as st

# CSS для изменения текста кнопки "Browse files" на "Выбрать файл"
st.markdown("""
<style>
div[data-testid="stFileUploader"] > section[data-testid="stFileUploaderDropzone"] > button span {
    display: none;
}
</style>
""", unsafe_allow_html=True)

import pandas as pd
import tempfile
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import requests
import io
import base64

# Путь к unified_document_service для прямого импорта модулей
# Используем абсолютный путь для надежности
UNIFIED_SERVICE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'unified_document_service'))
sys.path.append(os.path.join(UNIFIED_SERVICE_PATH, 'app'))

# Настройка API (если используем через HTTP)
API_BASE_URL = "http://localhost:8002"  # Gateway
USE_DIRECT_IMPORT = False  # True = прямой импорт, False = через HTTP API

# Прямой импорт модулей отключен, используем только HTTP API режим
USE_DIRECT_IMPORT = False
MODULES_AVAILABLE = False

# Примечание: Прямой импорт модулей unified_document_service отключен
# так как frontend работает через HTTP API Gateway для лучшей изоляции сервисов


def initialize_session_state():
    """Инициализация session state для многоэтапного интерфейса"""
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'found_data' not in st.session_state:
        st.session_state.found_data = []
    if 'patterns_file' not in st.session_state:
        st.session_state.patterns_file = ""
    if 'user_comments' not in st.session_state:
        st.session_state.user_comments = {}
    if 'anonymized_files' not in st.session_state:
        st.session_state.anonymized_files = []
    if 'anonymization_stats' not in st.session_state:
        st.session_state.anonymization_stats = {}  # Статистика анонимизации
    
    # Состояние для деанонимизации
    if 'deanonymized_doc' not in st.session_state:
        st.session_state.deanonymized_doc = None
    if 'replacement_table' not in st.session_state:
        st.session_state.replacement_table = None
    if 'deanonymization_ready' not in st.session_state:
        st.session_state.deanonymization_ready = False

def step1_upload_document():
    """Шаг 1: Загрузка документа и анализ"""
    st.markdown("### Выбор документа для анонимизации")
    
    # Sidebar с настройками (скрыт)
    # with st.sidebar:
    #     st.header("⚙️ Настройки")
    #     
    #     # Файл паттернов
    #     patterns_file = st.text_area(
    #         "Файл паттернов", 
    #         value=os.path.join(UNIFIED_SERVICE_PATH, "patterns/sensitive_patterns.xlsx"),
    #         help="Путь к Excel/CSV файлу с правилами поиска",
    #         height=60,
    #         key="step1_patterns_file"
    #     )
    #     
    #     # Кнопка для поиска файла паттернов
    #     if st.button("🔍 Найти файл паттернов автоматически", key="step1_find_patterns"):
    #         possible_paths = [
    #             os.path.join(UNIFIED_SERVICE_PATH, "patterns", "sensitive_patterns.xlsx"),
    #             os.path.join(UNIFIED_SERVICE_PATH, "patterns", "sensitive_patterns_full.csv"),
    #             os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "unified_document_service", "patterns", "sensitive_patterns.xlsx")),
    #             os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "unified_document_service", "patterns", "sensitive_patterns_full.csv")),
    #             "C:\\Projects\\Anonymizer\\unified_document_service\\patterns\\sensitive_patterns.xlsx",
    #             "C:\\Projects\\Anonymizer\\unified_document_service\\patterns\\sensitive_patterns_full.csv"
    #         ]
    #         
    #         for path in possible_paths:
    #             if os.path.exists(path):
    #                 st.success(f"✅ Найден файл: `{path}`")
    #                 st.info("💡 Скопируйте этот путь в поле выше")
    #                 break
    #         else:
    #             st.error("❌ Файл паттернов не найден в стандартных местах")
    # 
    #     st.session_state.patterns_file = patterns_file
    
    # По умолчанию стандартный путь к паттернам
    patterns_file = os.path.join(UNIFIED_SERVICE_PATH, "patterns/sensitive_patterns.xlsx")
    st.session_state.patterns_file = patterns_file
    
    # Загрузка файла для анонимизации
    uploaded_file = st.file_uploader(
        "Выберите Word документ (.docx)",
        type=['docx'],
        help="Загрузите DOCX файл для анонимизации"
    )
    
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        # Уведомление об успешной загрузке файла скрыто по требованию
        # Кнопка анализа справа
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("Анализировать документ", type="primary", key="step1_analyze"):
                with st.spinner("Анализируем документ..."):
                    found_data = analyze_document_api(uploaded_file, patterns_file)
                    if found_data is not None:
                        st.session_state.found_data = found_data
                        st.session_state.current_step = 2
                        st.rerun()
    
    # Секция деанонимизации
    display_deanonymization_section()

def step2_review_findings():
    """Шаг 2: Предпросмотр найденных сущностей"""
    st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    h1, .stTitle { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    h2, .stHeader { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    h3 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    .stMarkdown { margin-bottom: 0.2rem !important; }
    .stExpander { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("## Шаг 2: Предпросмотр данных")
    
    found_data = st.session_state.found_data
    
    # Sidebar с информацией и настройками (скрыт)
    # with st.sidebar:
    #     st.subheader(f"📄 Документ: {st.session_state.uploaded_file.name}")
    #     st.markdown("---")
    #     st.header("📊 Статистика анализа структурированных данных")
    #     
    #     if found_data:
    #         # Общая статистика
    #         total_count = len(found_data)
    #         approved_count = sum(1 for item in found_data if item.get('approved', False))
    #         st.metric("Всего найдено", total_count)
    #         st.metric("К анонимизации", approved_count)
    #         st.metric("Исключено", total_count - approved_count)
    #         
    #         # Статистика по типам
    #         st.subheader("📋 По типам данных")
    #         df_stats = pd.DataFrame(found_data)
    #         type_counts = df_stats['type'].value_counts()
    #         for data_type, count in type_counts.items():
    #             st.text(f"{data_type}: {count}")
    #         
    #         # Средняя уверенность
    #         avg_confidence = df_stats['confidence'].mean()
    #         st.metric("Средняя уверенность", f"{avg_confidence:.0%}")
        

    
    if not found_data:
        st.info("ℹ️ Чувствительные данные не найдены в документе")
        if st.button("🔄 Анализировать заново", key="step2_reanalyze"):
            st.session_state.current_step = 1
            st.rerun()
        return
    
    # Таблица с найденными данными
    st.markdown(f"### Найдены чувствительные данные: {len(found_data)} элементов")
    
    # Подготавливаем данные для таблицы
    table_data = []
    for i, item in enumerate(found_data):
        # Определяем источник данных
        source = item.get('source', 'Rule Engine')
        is_structured = source == 'Rule Engine'
        
        # Формируем контекст с выделением найденного значения
        block_text = item.get('block_text', item.get('context', 'Контекст недоступен'))
        original_value = item.get('original_value', '')
        
        # Выделяем найденное значение жирным в контексте
        if original_value and original_value in block_text:
            highlighted_context = block_text.replace(original_value, f"**{original_value}**")
        else:
            highlighted_context = block_text
        
        # Определяем метод обнаружения
        method = item.get('method', 'regex' if is_structured else 'nlp_unknown')
        spacy_label = item.get('spacy_label', '')
        
        method_display = {
            'regex': 'Regex паттерн',
            'spacy_ner_per': f'spaCy NER (PER){f" - {spacy_label}" if spacy_label else ""}',
            'spacy_ner_person': f'spaCy NER (PERSON){f" - {spacy_label}" if spacy_label else ""}', 
            'spacy_ner_org': f'spaCy NER (ORG){f" - {spacy_label}" if spacy_label else ""}',
            'spacy_ner_loc': f'spaCy NER (LOC){f" - {spacy_label}" if spacy_label else ""}',
            'spacy_ner_gpe': f'spaCy NER (GPE){f" - {spacy_label}" if spacy_label else ""}',
            'spacy_ner': 'spaCy NER',
            'morphological_enhanced': 'Морфология (улучш.)',
            'morphological': 'Морфология (контекст)',
            'context': 'Контекстный анализ',
            'custom': 'Кастомный паттерн',
            'spacy_context': 'spaCy + контекст',
            'unknown': 'Неизвестно',
            'nlp_unknown': 'Неизвестно'
        }.get(method, method)
        
        table_data.append({
            'ID': i + 1,
            'Источник': source,
            'Метод': method_display,
            'Тип': item.get('type', 'Неизвестно'),
            'Блок': item.get('block_id', 'unknown'),
            'Значение': item.get('original_value', ''),
            'Связанный контекст': highlighted_context,
            'Уверенность': f"{item.get('confidence', 1.0):.2f}",
            'Комментарий': item.get('comment', ''),
            'Заменить': item.get('approved', True)
        })
    
    # Интерактивная таблица
    if table_data:
        # Переименуем столбец 'Значение' в 'Заменяемое значение' для отображения
        df = pd.DataFrame(table_data)
        df = df.rename(columns={'Значение': 'Заменяемое значение'})
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",  # Разрешить отображение всех строк
            column_config={
                'ID': st.column_config.NumberColumn('№', disabled=True, width="extraSmall"),
                'Источник': st.column_config.TextColumn('Источник', disabled=True, width="small"),
                'Метод': st.column_config.TextColumn(
                    'Метод обнаружения', 
                    disabled=True,
                    help="Какой алгоритм определил эту сущность"
                ),
                'Тип': st.column_config.TextColumn('Тип', disabled=True, width="small"),
                'Блок': st.column_config.TextColumn(
                    'ID блока', 
                    disabled=True,
                    width="small",
                    help="Идентификатор блока документа"
                ),
                'Заменяемое значение': st.column_config.TextColumn('Заменяемое значение', disabled=True, width="large"),
                'Связанный контекст': st.column_config.TextColumn(
                    'Связанный контекст', 
                    disabled=True,
                    help="Полный текст блока с выделенным найденным значением"
                ),
                'Уверенность': st.column_config.TextColumn(
                    'Уверенность', 
                    disabled=True,
                    help="Уверенность системы в правильности распознавания"
                ),
                'Комментарий': st.column_config.TextColumn(
                    'Комментарий', 
                    help="Комментарий для журнала операций"
                ),
                'Заменить': st.column_config.CheckboxColumn(
                    'Заменить', 
                    help="Отметьте для включения в анонимизацию"
                )
            },
            hide_index=True,
            width="stretch",
            key="found_data_editor"
        )
        
        # CSS стилизация для выделения отмеченных чекбоксов красным цветом
        st.markdown("""
        <style>
        /* Стилизация отмеченных чекбоксов в таблице */
        div[data-testid="stDataEditor"] [data-testid="column-Заменить"] input[type="checkbox"]:checked {
            accent-color: #ff4b4b;
            background-color: #ff4b4b;
        }
        
        /* Дополнительная стилизация для браузеров, которые не поддерживают accent-color */
        div[data-testid="stDataEditor"] [data-testid="column-Заменить"] input[type="checkbox"]:checked::before {
            background-color: #ff4b4b;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Обновляем данные в session_state на основе изменений в таблице мгновенно
        if st.session_state.get('found_data_editor_last', None) is None:
            st.session_state.found_data_editor_last = edited_df.copy()
        changed = not edited_df.equals(st.session_state.found_data_editor_last)
        if changed:
            for i, row in edited_df.iterrows():
                if i < len(st.session_state.found_data):
                    st.session_state.found_data[i]['approved'] = row['Заменить']
                    st.session_state.found_data[i]['comment'] = row['Комментарий']
            st.session_state.found_data_editor_last = edited_df.copy()
            st.rerun()
    
    # Элементы управления массовыми операциями
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.empty()  # Пустое место для сдвига кнопок вправо
    with col2:
        if st.button("✅ Выбрать все", key="step2_select_all"):
            for i in range(len(found_data)):
                st.session_state.found_data[i]['approved'] = True
            st.rerun()
    with col3:
        if st.button("❌ Снять все", key="step2_deselect_all"):
            for i in range(len(found_data)):
                st.session_state.found_data[i]['approved'] = False
            st.rerun()
    
    # Кнопка подтверждения анонимизации
    st.markdown("---")
    selected_count = sum(1 for item in found_data if item.get('approved', False))
    
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        if st.button("← Назад к загрузке", type="secondary", key="step2_back"):
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        st.metric("Выбрано для замены", f"{selected_count}/{len(found_data)}")
    with col3:
        st.markdown("""
        <style>
        /* Streamlit 1.52+ unique selector for button by text */
        div[data-testid="stButton"] button:where(:not([aria-disabled])) {
            white-space: nowrap !important;
            min-width: 220px !important;
            max-width: 100% !important;
            font-size: 16px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("Подтвердить анонимизацию", type="primary", disabled=(selected_count == 0), key="step2_confirm"):
            with st.spinner("Выполняем анонимизацию и генерируем файлы..."):
                # Получаем одобренные пользователем элементы для анонимизации
                approved_items = [item for item in st.session_state.found_data if item.get('approved', False)]
                
                if not approved_items:
                    st.warning("⚠️ Не выбрано ни одного элемента для анонимизации")
                else:
                    # 🎯 Вызываем API для ПОЛНОЙ анонимизации
                    # Backend сам сгенерирует Excel с правильными UUID
                    anonymized_files = anonymize_document_full_api(
                        st.session_state.uploaded_file, 
                        approved_items,
                        st.session_state.patterns_file,
                        total_found=len(st.session_state.found_data)  # ✅ Передаем общее количество найденных
                    )
                    
                    # ❌ УДАЛЕНО: Генерация Excel на frontend (генерировал случайные UUID)
                    # Excel теперь приходит от backend с детерминистичными UUID
                    
                    if anonymized_files:
                        # Сохраняем сгенерированные файлы в session_state
                        st.session_state.anonymized_files = anonymized_files
                        
                        st.success("✅ Анонимизация завершена! Файлы готовы для скачивания.")
                        st.session_state.current_step = 3
                        st.rerun()
                    else:
                        st.error("❌ Ошибка при генерации файлов")

def step3_download_results():
    """Шаг 3: Скачивание результатов"""
    st.markdown("""
    <style>
    .block-container { padding-top: 0.5rem !important; }
    h1, .stTitle { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    h2, .stHeader { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    h3 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    .stMarkdown { margin-bottom: 0.2rem !important; }
    .stExpander { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown("## Шаг 3: Результаты анонимизации")
    
    st.success("Документ успешно анонимизирован!")
    
    # Отображаем статистику анонимизации
    if 'anonymization_stats' in st.session_state and st.session_state.anonymization_stats:
        stats = st.session_state.anonymization_stats
        
        # Создаем колонки для счетчиков
        col1, col2 = st.columns(2)
        
        with col1:
                st.metric(
                    label="Найдено чувствительных данных",
                    value=f"{stats.get('total_found', 0)} элементов"
                )
        
        with col2:
                st.metric(
                    label="Анонимизировано чувствительных данных", 
                    value=f"{stats.get('replacements_applied', stats.get('total_anonymized', 0))} элементов"
                )
        
        # Дополнительная информация о замене
        # Уведомление 'Выполнено замен: ...' скрыто по требованию
        
        st.markdown("---")
    
    # Проверяем, есть ли готовые файлы
    if st.session_state.anonymized_files:
        st.markdown("### Файлы для скачивания:")
        
        # Разделяем файлы по типу для отображения конкретных кнопок
        anonymized_doc = None
        replacements_table = None
        
        for file_info in st.session_state.anonymized_files:
            if file_info['type'] == 'document':
                anonymized_doc = file_info
            elif file_info['type'] == 'replacements':
                replacements_table = file_info
        
        # Создаем две колонки слева для кнопок
        col_doc, col_repl, col_spacer = st.columns([2, 1, 5])

        with col_doc:
            if anonymized_doc:
                st.download_button(
                    label="Скачать анонимизированный документ",
                    data=anonymized_doc['data'],
                    file_name=anonymized_doc['filename'],
                    mime=anonymized_doc['mime'],
                    key="download_document",
                    type="primary",
                    use_container_width=True
                )
        with col_repl:
            if replacements_table:
                st.download_button(
                    label="Скачать таблицу замен",
                    data=replacements_table['data'],
                    file_name=replacements_table['filename'],
                    mime=replacements_table['mime'],
                    key="download_replacements",
                    type="primary",
                    use_container_width=True
                )
    else:
        st.warning("⚠️ Файлы не готовы. Вернитесь на шаг 2 и подтвердите анонимизацию.")
    
    st.markdown("---")
    if st.button("🔄 Обработать новый документ", key="step3_new_document"):
        # Сброс состояния
        st.session_state.current_step = 1
        st.session_state.uploaded_file = None
        st.session_state.found_data = []
        st.session_state.user_comments = {}
        st.session_state.anonymized_files = []
        st.session_state.anonymization_stats = {}  # Сбрасываем статистику
        st.rerun()

def analyze_document_api(uploaded_file, patterns_file):
    """Анализ документа через HTTP API"""
    
    # Проверяем доступность API
    progress_bar = st.progress(0)
    # Уведомления о подключении к Gateway и отправке документа скрыты по требованию
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            st.error("❌ Gateway недоступен")
            progress_bar.empty()
            return None
        # st.success("✅ Gateway доступен")  # Скрыто
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка подключения к Gateway: {str(e)}")
        progress_bar.empty()
        return None
    progress_bar.progress(20)
    # st.info("� Отправляем документ на анализ...")  # Скрыто
    
    try:
        # Подготавливаем файлы для отправки
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        # Параметры запроса
        data = {
            'patterns_file': patterns_file
        }
        
        progress_bar.progress(40)
        # st.info("🔍 Выполняем анализ документа...")  # Скрыто по требованию
        
        # Отправляем запрос на анализ (только анализ, без анонимизации)
        response = requests.post(
            f"{API_BASE_URL}/analyze_document", 
            files=files,
            data=data,
            timeout=120  # 2 минуты на анализ
        )
        
        progress_bar.progress(70)
        
        if response.status_code == 200:
            result = response.json()
            st.success("✅ Анализ завершен успешно!")
            
            progress_bar.progress(90)
            
            # Получаем объединенные результаты от Rule Engine + NLP Service
            found_data = []
            
            if 'found_items' in result and result['found_items']:
                for i, item in enumerate(result['found_items']):
                    found_item = {
                        'id': i + 1,
                        'block_id': item.get('block_id', f'block_{i}'),
                        'type': item.get('category', item.get('type', 'Неизвестно')),
                        'original_value': item.get('original_value', item.get('value', '')),
                        'uuid': item.get('uuid', item.get('replacement', '')),
                        'position': item.get('position', {}),
                        'confidence': item.get('confidence', 1.0),
                        'method': item.get('method', 'unknown'),  # ⬅️ Добавляем поле method!
                        'spacy_label': item.get('spacy_label', ''),  # ⬅️ Добавляем spacy_label!
                        'approved': True,  # По умолчанию одобрено
                        'comment': item.get('comment', ''),
                        'source': item.get('source', 'Unknown'),  # Источник уже указан в данных
                        'block_text': item.get('block_text', item.get('context', 'Контекст недоступен'))
                    }
                    found_data.append(found_item)
            
            # Выводим сводку
            rule_engine_count = result.get('rule_engine_items', 0)
            nlp_count = result.get('nlp_items', 0)
            total_count = result.get('total_items', len(found_data))
            
            if found_data:
                st.success(f"📈 Общий итог: найдено {total_count} чувствительных элементов")
                st.info(f"   • Rule Engine: {rule_engine_count} элементов")
                st.info(f"   • NLP Service: {nlp_count} элементов")
            else:
                st.info("ℹ️ Чувствительные данные не найдены")
            
            progress_bar.progress(100)
            progress_bar.empty()
            return found_data
            
        else:
            error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            st.error(f"❌ Ошибка API: {response.status_code}")
            st.error(f"Детали: {error_detail}")
            progress_bar.empty()
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Превышено время ожидания. Попробуйте с файлом меньшего размера.")
        progress_bar.empty()
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка соединения: {str(e)}")
        progress_bar.empty()
        return None
    except Exception as e:
        st.error(f"❌ Неожиданная ошибка: {str(e)}")
        progress_bar.empty()
        return None


def anonymize_document_full_api(uploaded_file, approved_items, patterns_file, total_found=None):
    """Полная анонимизация документа через HTTP API с генерацией файлов для скачивания"""
    
    try:
        # Подготавливаем файлы для отправки
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        data = {
            'patterns_file': patterns_file,
            'generate_excel_report': 'true',  # ✅ ВКЛЮЧАЕМ генерацию Excel на backend
            'generate_json_ledger': 'true',     # ✅ ВКЛЮЧАЕМ генерацию JSON Ledger
            'selected_items': json.dumps(approved_items)  # ✅ Передаем выбранные элементы
        }
        
        # 🎯 Отправляем выбранные пользователем элементы на анонимизацию
        response = requests.post(
            f"{API_BASE_URL}/anonymize_selected",  # ✅ Анонимизация только выбранных элементов
            files=files,
            data=data,
            timeout=240  # 4 минуты на анонимизацию
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Сохраняем статистику анонимизации в session_state
            st.session_state.anonymization_stats = {
                'total_found': total_found if total_found is not None else len(approved_items),  # ✅ Общее количество найденных
                'total_anonymized': result.get('statistics', {}).get('total_replacements', 0),  # Фактически замененных
                'replacement_stats': result.get('statistics', {}),  # Детальная статистика замен
                'replacements_applied': result.get('statistics', {}).get('total_replacements', 0)
            }
            
            # Формируем список файлов для скачивания
            download_files = []
            
            # Анонимизированный документ
            if 'files_base64' in result and 'anonymized_document_base64' in result['files_base64']:
                doc_data = base64.b64decode(result['files_base64']['anonymized_document_base64'])
                download_files.append({
                    'type': 'document',
                    'label': '📄 Скачать анонимизированный документ',
                    'data': doc_data,
                    'filename': f"{uploaded_file.name.rsplit('.', 1)[0]}_anonymized.docx",
                    'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                })
            
            # 🎯 ИСПОЛЬЗУЕМ Excel от backend (с правильными UUID)
            if 'files_base64' in result and 'excel_report_base64' in result['files_base64']:
                excel_data = base64.b64decode(result['files_base64']['excel_report_base64'])
                download_files.append({
                    'type': 'replacements',
                    'label': '📋 Таблица замен (Excel)',
                    'data': excel_data,
                    'filename': f"Replacements_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                    'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                })
            
            # JSON Ledger (опционально)
            if 'files_base64' in result and 'json_ledger_base64' in result['files_base64']:
                json_data = base64.b64decode(result['files_base64']['json_ledger_base64'])
                download_files.append({
                    'type': 'ledger',
                    'label': '📊 JSON Ledger',
                    'data': json_data,
                    'filename': f"Ledger_{uploaded_file.name.rsplit('.', 1)[0]}.json",
                    'mime': 'application/json'
                })
            
            return download_files
            
        else:
            st.error(f"❌ Ошибка API: {response.status_code}")
            if hasattr(response, 'json'):
                try:
                    error_detail = response.json().get('detail', 'Неизвестная ошибка')
                    st.error(f"Детали: {error_detail}")
                except:
                    st.error(f"Ответ сервера: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("⏱️ Превышено время ожидания анонимизации. Попробуйте с файлом меньшего размера.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка соединения: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Неожиданная ошибка: {str(e)}")
        return None


def display_deanonymization_section():
    """Отображает секцию деанонимизации документов"""
    
    st.markdown("---")  # Разделитель
    st.markdown("### Выбор документов для восстановления")
    st.markdown("**Восстановление оригинальных данных из ранее анонимизированного документа**")
    
    with st.expander("Как работает деанонимизация", expanded=False):
        st.markdown("""
        **Задача:** Заменить UUID обратно на оригинальные чувствительные данные

        **Что нужно:**
        1. **Анонимизированный документ** (.docx) - документ с UUID вместо чувствительных данных
        2. **Таблица замен** (.xlsx или .csv) - соответствие UUID ↔ оригинальные данные

        **Процесс:**
        1. Загрузка анонимизированного документа и таблицы замен
        2. Анализ соответствий UUID ↔ оригинальные данные
        3. Обратная замена UUID на исходные чувствительные данные
        4. Сохранение форматирования документа

        **Результат:** `d0e62465-8f2a-4b3c-9e1f...` → `admin@company.ru` с исходным форматированием
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 1. Загрузить анонимизированный документ")
        anonymized_file = st.file_uploader(
            "Выберите анонимизированный DOCX файл",
            type=['docx'],
            key="deanon_docx",
            help="Документ, который был ранее анонимизирован нашей системой"
        )
        
        if anonymized_file is not None:
            # Уведомление об успешной загрузке файла скрыто по требованию
            st.session_state.deanonymized_doc = anonymized_file
        
    with col2:
        st.markdown("#### 2. Загрузить таблицу замен")
        
        # Кнопка загрузки таблицы замен - активна только если загружен документ
        replacement_file = st.file_uploader(
            "Выберите файл с соответствиями",
            type=['xlsx', 'csv'],
            key="deanon_table",
            help="Excel или CSV файл с соответствием UUID ↔ оригинальные данные",
            disabled=(anonymized_file is None)
        )
        
        if replacement_file is not None:
            # Уведомление об успешной загрузке файла скрыто по требованию
            st.session_state.replacement_table = replacement_file
    
    # Проверяем готовность к деанонимизации
    if (st.session_state.deanonymized_doc is not None and 
        st.session_state.replacement_table is not None):
        
        st.session_state.deanonymization_ready = True
        
        st.markdown("---")
        
        # Кнопка деанонимизации справа, компактная ширина
        col1, col2 = st.columns([6, 1])
        with col2:
            # Короткое название для кнопки, чтобы не было переноса
            st.markdown("""
            <style>
            .stButton button, .stButton > button {
                white-space: nowrap !important;
                min-width: 220px;
                max-width: 100%;
            }
            </style>
            """, unsafe_allow_html=True)
            if st.button(
                "Деанонимизировать документ",  # Короткое название без переноса
                key="deanonymize_btn",
                type="primary",
                use_container_width=True
            ):
                perform_deanonymization()
    else:
        st.session_state.deanonymization_ready = False


def perform_deanonymization():
    """Выполняет процесс деанонимизации"""
    
    try:
        with st.spinner("🔄 Выполняется деанонимизация..."):
            
            # Создаем временные файлы
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_doc:
                tmp_doc.write(st.session_state.deanonymized_doc.getvalue())
                doc_path = tmp_doc.name
            
            with tempfile.NamedTemporaryFile(
                suffix='.xlsx' if st.session_state.replacement_table.name.endswith('.xlsx') else '.csv', 
                delete=False
            ) as tmp_table:
                tmp_table.write(st.session_state.replacement_table.getvalue())
                table_path = tmp_table.name
            
            # Отправляем запрос на деанонимизацию через API
            response = send_deanonymization_request(doc_path, table_path)
            
            if response and response.get('success', False):
                st.success("🎉 Деанонимизация успешно выполнена!")
                
                # Отображаем статистику
                stats = response.get('statistics', {})
                display_deanonymization_stats(stats)
                
                # Подготавливаем файлы для скачивания
                deanonymized_content = response.get('deanonymized_document')
                if deanonymized_content:
                    
                    # Кнопки скачивания
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Декодируем base64 содержимое
                        doc_bytes = base64.b64decode(deanonymized_content)
                        
                        st.download_button(
                            label="📥 Скачать восстановленный документ",
                            data=doc_bytes,
                            file_name=f"deanonymized_{st.session_state.deanonymized_doc.name}",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="download_deanon_doc"
                        )
                    
                    with col2:
                        # Отчет о деанонимизации
                        if 'deanonymization_report' in response:
                            report_content = response['deanonymization_report']
                            st.download_button(
                                label="📊 Скачать отчет о деанонимизации",
                                data=report_content,
                                file_name=f"deanonymization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key="download_deanon_report"
                            )
                else:
                    st.error("❌ Не удалось получить деанонимизированный документ")
            else:
                error_msg = response.get('error', 'Неизвестная ошибка') if response else 'Нет ответа от сервера'
                st.error(f"❌ Ошибка при деанонимизации: {error_msg}")
            
            # Очищаем временные файлы
            try:
                os.unlink(doc_path)
                os.unlink(table_path)
            except:
                pass
                
    except Exception as e:
        st.error(f"❌ Ошибка при выполнении деанонимизации: {str(e)}")


def send_deanonymization_request(doc_path: str, table_path: str) -> dict:
    """Отправляет запрос на деанонимизацию через API"""
    
    try:
        # Подготавливаем файлы для отправки
        files = {
            'document': ('document.docx', open(doc_path, 'rb'), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            'replacement_table': ('replacements.xlsx', open(table_path, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        # Отправляем запрос
        response = requests.post(
            f"{API_BASE_URL}/deanonymize",
            files=files,
            timeout=120  # 2 минуты на обработку
        )
        
        # Закрываем файлы
        for file_tuple in files.values():
            file_tuple[1].close()
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ Превышено время ожидания ответа от сервера")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Не удалось подключиться к серверу {API_BASE_URL}")
        st.info("💡 Убедитесь, что Gateway сервис запущен на порту 8002")
        return None
    except Exception as e:
        st.error(f"❌ Ошибка при отправке запроса: {str(e)}")
        return None


def display_deanonymization_stats(stats: dict):
    """Отображает статистику деанонимизации"""
    
    if not stats:
        return
    
    st.markdown("### 📊 Статистика деанонимизации")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🔄 UUID заменено",
            stats.get('total_replacements', 0)
        )
    
    with col2:
        st.metric(
            "✅ Успешных замен",
            stats.get('successful_replacements', 0)
        )
    
    with col3:
        st.metric(
            "❌ Ошибок замен",
            stats.get('failed_replacements', 0)
        )
    
    with col4:
        success_rate = 0
        total = stats.get('total_replacements', 0)
        successful = stats.get('successful_replacements', 0)
        if total > 0:
            success_rate = round((successful / total) * 100, 1)
        
        st.metric(
            "📈 Успешность",
            f"{success_rate}%"
        )
    
    # Детальная информация
    if 'replacement_details' in stats:
        with st.expander("📋 Детали замен", expanded=False):
            details_df = pd.DataFrame(stats['replacement_details'])
            st.dataframe(details_df, use_container_width=True)


def main():
    """Главная функция Streamlit приложения"""
    
    # Конфигурация страницы
    st.set_page_config(
        page_title="Document Anonymizer - Frontend",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # CSS для скрытия боковой панели
    st.markdown("""
    <style>
    /* Скрываем боковую панель */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Убираем кнопку сворачивания/разворачивания */
    button[title="Open sidebar"], button[title="Close sidebar"] {
        display: none !important;
    }
    
    /* Уменьшение отступов для более компактного интерфейса */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Уменьшение отступов заголовков */
    h1 {
        padding-top: 0rem;
        margin-top: 0rem;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* Уменьшение отступов между элементами */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    /* Компактные метрики */
    div[data-testid="metric-container"] {
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Инициализация состояния
    initialize_session_state()
    
    # Маршрутизация по этапам
    current_step = st.session_state.current_step
    
    if current_step == 1:
        # Уменьшаем вертикальные отступы для компактности первой страницы
        st.markdown("""
        <style>
        .block-container { padding-top: 0.5rem !important; }
        h1, .stTitle { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
        h2, .stHeader { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
        h3 { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
        .stMarkdown { margin-bottom: 0.2rem !important; }
        .stExpander { margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
        </style>
        """, unsafe_allow_html=True)
        st.title("Анонимайзер docx-документов")
        st.markdown("**Анонимизация DOCX документов с заменой чувствительных данных на UUID и полным сохранением форматирования**")
        # Показываем описание и инструкции только на первом шаге
        # Объединенное описание функционала и инструкций
        with st.expander("Как работает анонимизация", expanded=False):
            st.markdown("""
            **Основная задача:** Заменить чувствительные данные (email, телефоны, коды документов) на уникальные UUID 
            с **полным сохранением исходного форматирования** документа.

            **Пошаговый процесс анонимизации:**

            **1. Загрузка документа**
            - Загрузите DOCX документ в разделе "Выберите документ для анонимизации" ниже
            - Система автоматически проанализирует структуру документа

            **2. Анализ и поиск данных**
            - Автоматический поиск чувствительных данных (email, телефоны, ИНН, паспорта и др.)
            - Использование современных NLP технологий и регулярных выражений

            **3. Подтверждение замен**
            - Просмотр найденных данных в разделе "Шаг 2"
            - Выберите данные для анонимизации с помощью чекбоксов
            - Добавьте комментарии при необходимости

            **4. Точечная замена**
            - Замена выбранных данных на уникальные UUID
            - **Полное сохранение форматирования:** шрифт, цвет, размер, стили остаются без изменений

            **5. Получение результатов**
            - Скачивание анонимизированного документа
            - Получение таблицы соответствий (UUID ↔ оригинальные данные)
            - Детальные отчеты о выполненных заменах

            **Результат:** `admin@company.ru` → `d0e62465-8f2a-4b3c-9e1f...` с тем же шрифтом, цветом, размером!

            **Безопасность:** Все оригинальные данные сохраняются в зашифрованной таблице замен для возможности восстановления.
            """)
        
        step1_upload_document()
    elif current_step == 2:
        step2_review_findings()
    elif current_step == 3:
        step3_download_results()
    else:
        st.session_state.current_step = 1
        st.rerun()


if __name__ == "__main__":
    main()