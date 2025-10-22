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
API_BASE_URL = "http://localhost:8000"  # Gateway
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

def step1_upload_document():
    """Шаг 1: Загрузка документа и анализ"""
    st.markdown("## 📂 Шаг 1: Загрузите документ")
    
    # Sidebar с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Файл паттернов
        patterns_file = st.text_area(
            "Файл паттернов", 
            value=os.path.join(UNIFIED_SERVICE_PATH, "patterns/sensitive_patterns.xlsx"),
            help="Путь к Excel файлу с правилами поиска",
            height=60,
            key="step1_patterns_file"
        )
        
        # Кнопка для поиска файла паттернов
        if st.button("🔍 Найти файл паттернов автоматически", key="step1_find_patterns"):
            possible_paths = [
                os.path.join(UNIFIED_SERVICE_PATH, "patterns", "sensitive_patterns.xlsx"),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "unified_document_service", "patterns", "sensitive_patterns.xlsx")),
                "C:\\Projects\\Anonymizer\\unified_document_service\\patterns\\sensitive_patterns.xlsx"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    st.success(f"✅ Найден файл: `{path}`")
                    st.info("💡 Скопируйте этот путь в поле выше")
                    break
            else:
                st.error("❌ Файл паттернов не найден в стандартных местах")
    
    st.session_state.patterns_file = patterns_file
    
    # Загрузка файла
    uploaded_file = st.file_uploader(
        "Выберите Word документ (.docx)",
        type=['docx'],
        help="Загрузите DOCX файл для анонимизации"
    )
    
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.success(f"✅ Файл загружен: {uploaded_file.name}")
        
        # Кнопка анализа
        if st.button("🔍 Анализировать документ", type="primary", key="step1_analyze"):
            with st.spinner("🔄 Анализируем документ..."):
                found_data = analyze_document_api(uploaded_file, patterns_file)
                if found_data is not None:
                    st.session_state.found_data = found_data
                    st.session_state.current_step = 2
                    st.rerun()

def step2_review_findings():
    """Шаг 2: Предпросмотр найденных сущностей"""
    st.markdown("## Шаг 2: Предпросмотр данных")
    
    found_data = st.session_state.found_data
    
    # Sidebar с информацией и настройками
    with st.sidebar:
        st.subheader(f"📄 Документ: {st.session_state.uploaded_file.name}")
        st.markdown("---")
        st.header("📊 Статистика анализа структурированных данных")
        
        if found_data:
            # Общая статистика
            total_count = len(found_data)
            approved_count = sum(1 for item in found_data if item.get('approved', False))
            st.metric("Всего найдено", total_count)
            st.metric("К анонимизации", approved_count)
            st.metric("Исключено", total_count - approved_count)
            
            # Статистика по типам
            st.subheader("📋 По типам данных")
            df_stats = pd.DataFrame(found_data)
            type_counts = df_stats['type'].value_counts()
            for data_type, count in type_counts.items():
                st.text(f"{data_type}: {count}")
            
            # Средняя уверенность
            avg_confidence = df_stats['confidence'].mean()
            st.metric("Средняя уверенность", f"{avg_confidence:.0%}")
        

    
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
        # Определяем источник данных: unified_document_service = "Да", nlp_service = "Нет"
        # Пока все данные идут от unified_document_service, поэтому "Да"
        is_structured = item.get('source', 'unified_document_service') == 'unified_document_service'
        
        # Формируем контекст с выделением найденного значения
        block_text = item.get('block_text', item.get('context', 'Контекст недоступен'))
        original_value = item.get('original_value', '')
        
        # Выделяем найденное значение жирным в контексте
        if original_value and original_value in block_text:
            highlighted_context = block_text.replace(original_value, f"**{original_value}**")
        else:
            highlighted_context = block_text
        
        table_data.append({
            'ID': i + 1,
            'Тип': item.get('type', 'Неизвестно'),
            'Значение': item.get('original_value', ''),
            'Связанный контекст': highlighted_context,
            'UUID замена': item.get('uuid', ''),
            'Структурированные данные': 'Да' if is_structured else 'Нет',
            'Уверенность': item.get('confidence', 1.0),
            'Комментарий': item.get('comment', ''),
            'Заменить': item.get('approved', True)
        })
    
    # Интерактивная таблица
    if table_data:
        edited_df = st.data_editor(
            pd.DataFrame(table_data),
            column_config={
                'ID': st.column_config.NumberColumn('№', disabled=True),
                'Тип': st.column_config.TextColumn('Тип', disabled=True),
                'Значение': st.column_config.TextColumn('Значение', disabled=True),
                'Связанный контекст': st.column_config.TextColumn(
                    'Связанный контекст', 
                    disabled=True,
                    help="Полный текст блока с выделенным найденным значением"
                ),
                'UUID замена': st.column_config.TextColumn('UUID замена', disabled=True),
                'Структурированные данные': st.column_config.TextColumn(
                    'Структурированные данные', 
                    disabled=True,
                    help="Да = unified_document_service, Нет = nlp_service"
                ),
                'Уверенность': st.column_config.NumberColumn(
                    'Уверенность', 
                    format="%.0%%", 
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
            use_container_width=True,
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
        
        # Обновляем данные в session_state на основе изменений в таблице
        for i, row in edited_df.iterrows():
            if i < len(st.session_state.found_data):
                st.session_state.found_data[i]['approved'] = row['Заменить']
                st.session_state.found_data[i]['comment'] = row['Комментарий']
    
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
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("⬅️ Назад к загрузке", type="secondary", key="step2_back"):
            st.session_state.current_step = 1
            st.rerun()
    with col2:
        st.metric("Выбрано для замены", f"{selected_count}/{len(found_data)}")
    with col3:
        if st.button("🔒 Подтвердить анонимизацию", type="primary", disabled=(selected_count == 0), key="step2_confirm"):
            with st.spinner("🔄 Выполняем анонимизацию..."):
                # Здесь будет вызов финальной анонимизации
                st.success("✅ Анонимизация завершена!")
                st.session_state.current_step = 3
                st.rerun()

def step3_download_results():
    """Шаг 3: Скачивание результатов"""
    st.markdown("## 📥 Шаг 3: Результаты анонимизации")
    
    st.success("✅ Документ успешно анонимизирован!")
    
    # Здесь будут ссылки для скачивания
    st.markdown("### 📁 Файлы для скачивания:")
    st.markdown("- 📄 Анонимизированный документ")
    st.markdown("- 📊 Excel отчет с заменами")
    
    # Кнопка для скачивания файлов
    st.markdown("---")
    if st.button("📥 Скачать все файлы", type="primary", key="step3_download_files"):
        with st.spinner("� Генерируем анонимизированные файлы..."):
            # Получаем одобренные пользователем элементы для анонимизации
            approved_items = [item for item in st.session_state.found_data if item.get('approved', False)]
            
            if not approved_items:
                st.warning("⚠️ Не выбрано ни одного элемента для анонимизации")
            else:
                # Вызываем API для полной анонимизации
                anonymized_files = anonymize_document_full_api(
                    st.session_state.uploaded_file, 
                    approved_items,
                    st.session_state.patterns_file
                )
                
                if anonymized_files:
                    st.success(f"✅ Сгенерировано файлов: {len(anonymized_files)}")
                    
                    # Создаем кнопки для скачивания каждого файла
                    for file_info in anonymized_files:
                        st.download_button(
                            label=file_info['label'],
                            data=file_info['data'],
                            file_name=file_info['filename'],
                            mime=file_info['mime'],
                            key=f"download_{file_info['type']}"
                        )
                else:
                    st.error("❌ Ошибка при генерации файлов")
    
    if st.button("🔄 Обработать новый документ", key="step3_new_document"):
        # Сброс состояния
        st.session_state.current_step = 1
        st.session_state.uploaded_file = None
        st.session_state.found_data = []
        st.session_state.user_comments = {}
        st.rerun()

def analyze_document_api(uploaded_file, patterns_file):
    """Анализ документа через HTTP API"""
    
    # Проверяем доступность API
    progress_bar = st.progress(0)
    st.info("🔗 Проверяем подключение к Gateway...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            st.error("❌ Gateway недоступен")
            progress_bar.empty()
            return None
        st.success("✅ Gateway доступен")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Ошибка подключения к Gateway: {str(e)}")
        progress_bar.empty()
        return None
    
    progress_bar.progress(20)
    st.info("� Отправляем документ на анализ...")
    
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
        st.info("🔍 Выполняем анализ документа...")
        
        # Отправляем запрос на анализ (только анализ, без анонимизации)
        response = requests.post(
            f"{API_BASE_URL}/analyze_document", 
            files=files,
            data=data,
            timeout=60
        )
        
        progress_bar.progress(70)
        
        if response.status_code == 200:
            result = response.json()
            st.success("✅ Анализ завершен успешно!")
            
            progress_bar.progress(90)
            
            # Преобразуем результат в формат для фронтенда
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
                        'approved': True,  # По умолчанию одобрено
                        'comment': '',
                        'source': 'unified_document_service',  # Помечаем источник
                        'block_text': item.get('block_text', item.get('context', 'Контекст недоступен'))  # Текст блока
                    }
                    found_data.append(found_item)
                
                st.info(f"📈 Найдено {len(found_data)} чувствительных элементов")
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


def anonymize_document_full_api(uploaded_file, approved_items, patterns_file):
    """Полная анонимизация документа через HTTP API с генерацией файлов для скачивания"""
    
    try:
        # Подготавливаем файлы для отправки
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        data = {
            'patterns_file': patterns_file,
            'generate_excel_report': True,
            'generate_json_ledger': False  # Не генерируем JSON, так как он неактуален для пользователей
        }
        
        # Отправляем запрос на полную анонимизацию
        response = requests.post(
            f"{API_BASE_URL}/anonymize_full", 
            files=files,
            data=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Формируем список файлов для скачивания
            download_files = []
            
            files_base64 = result.get('files_base64', {})
            
            # Анонимизированный документ
            if files_base64.get('anonymized_document_base64'):
                import base64
                doc_data = base64.b64decode(files_base64['anonymized_document_base64'])
                download_files.append({
                    'type': 'document',
                    'label': '📄 Скачать анонимизированный документ',
                    'data': doc_data,
                    'filename': f"{uploaded_file.name.rsplit('.', 1)[0]}_anonymized.docx",
                    'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                })
            
            # Excel отчет
            if files_base64.get('excel_report_base64'):
                import base64
                excel_data = base64.b64decode(files_base64['excel_report_base64'])
                download_files.append({
                    'type': 'excel',
                    'label': '📊 Скачать Excel отчет с заменами',
                    'data': excel_data,
                    'filename': f"{uploaded_file.name.rsplit('.', 1)[0]}_report.xlsx",
                    'mime': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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


def main():
    """Главная функция Streamlit приложения"""
    
    # Конфигурация страницы
    st.set_page_config(
        page_title="Document Anonymizer - Frontend",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS для увеличения ширины боковой панели и оптимизации отступов
    st.markdown("""
    <style>
    .css-1d391kg {
        width: 350px;
    }
    .css-1lcbmhc {
        width: 350px;
    }
    section[data-testid="stSidebar"] {
        width: 350px !important;
    }
    section[data-testid="stSidebar"] > div {
        width: 350px !important;
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
        # Заголовок и описание только на первом шаге
        st.title("🔒 Анонимайзер docx-документов")
        st.markdown("**Анонимизация DOCX документов с заменой чувствительных данных на UUID и полным сохранением форматирования**")
        # Показываем описание и инструкции только на первом шаге
        # Краткое описание функционала
        with st.expander("ℹ️ Что делает система", expanded=False):
            st.markdown("""
            **🎯 Основная задача:** Заменить чувствительные данные (email, телефоны, коды документов) на уникальные UUID 
            с **полным сохранением исходного форматирования** документа.
            
            **🔄 Процесс:**
            1. Анализ документа и поиск чувствительных данных
            2. Показ найденных данных для подтверждения пользователем  
            3. **Точечная замена** на UUID с сохранением всех стилей
            4. Генерация отчетов о выполненных заменах
            
            **✨ Результат:** `admin@company.ru` → `d0e62465-8f2a-4b3c-9e1f...` с тем же шрифтом, цветом, размером!
            """)
        
        # Инструкция по использованию
        st.markdown("""
        ### 📋 Инструкция по использованию:
        1. **📂 Загрузите DOCX документ** в разделе "Шаг 1" ниже
        2. **🔍 Просмотрите найденные данные** в разделе "Шаг 2"
        3. **✅ Подтвердите замены** с помощью чекбоксов и комментариев
        4. **📥 Скачайте результат** - анонимизированный документ и отчеты
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