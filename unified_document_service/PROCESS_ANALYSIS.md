# 📋 АНАЛИЗ ПРОЦЕССА АНОНИМИЗАЦИИ ДОКУМЕНТОВ

## 🏗️ АРХИТЕКТУРА СИСТЕМЫ

```
┌─────────────────────────────────────────────────────────────────────┐
│                         UNIFIED DOCUMENT SERVICE                      │
│                         (Порт 8009)                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
          ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
          │ NLP Service  │  │ Rule Engine  │  │  Frontend    │
          │  (Порт 8006) │  │  (Порт 8003) │  │  (Порт 8501) │
          └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🔄 ПОЛНЫЙ ЦИКЛ АНОНИМИЗАЦИИ: ПОШАГОВОЕ ОПИСАНИЕ

### **📍 ТОЧКА ВХОДА: `/anonymize_full` API**

**Сервис:** `Unified Document Service`  
**Файл:** `unified_document_service/app/main.py`  
**Метод:** `POST /anonymize_full`

**Входные параметры:**
```python
{
    "file": UploadFile,                          # DOCX документ
    "patterns_file": str,                        # Путь к паттернам (по умолчанию: patterns/sensitive_patterns.xlsx)
    "generate_excel_report": bool = True,        # Генерировать Excel отчёт
    "generate_json_ledger": bool = True          # Генерировать JSON журнал
}
```

**Выходные данные:**
```python
{
    "status": "success",
    "statistics": {...},
    "files_base64": {
        "anonymized_document_base64": str,       # Base64 анонимизированного документа
        "excel_report_base64": str,              # Base64 Excel отчёта
        "json_ledger_base64": str                # Base64 JSON журнала
    }
}
```

---

## 🎯 ЭТАП 1: ЗАГРУЗКА И ИНИЦИАЛИЗАЦИЯ

### **1.1. Создание временных файлов**
```python
# Сохраняем загруженный файл во временный файл
tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
input_path = tmp_input.name

# Создаём пути для выходных файлов
output_path = f"{filename_base}_anonymized.docx"
excel_path = f"{filename_base}_report.xlsx"
json_path = f"{filename_base}_ledger.json"
```

### **1.2. Инициализация FullAnonymizer**
```python
anonymizer = FullAnonymizer(patterns_path="patterns/sensitive_patterns.xlsx")
```

**Что создаётся:**
- `BlockBuilder()` — извлекает структурированные блоки из DOCX
- `RuleAdapter()` — загружает regex паттерны из Excel
- `FormatterApplier()` — применяет замены с сохранением форматирования
- `UUIDMapper()` — генерирует детерминистические UUID

---

## 🎯 ЭТАП 2: ИЗВЛЕЧЕНИЕ БЛОКОВ ДОКУМЕНТА

**Сервис:** `Unified Document Service`  
**Компонент:** `BlockBuilder`  
**Файл:** `unified_document_service/app/block_builder.py`

### **2.1. Загрузка документа**
```python
doc = Document(input_path)  # python-docx библиотека
blocks = self.block_builder.build_blocks(doc)
```

### **2.2. Структура блоков**
```python
# Каждый блок содержит:
{
    "block_id": str,           # Уникальный ID: "paragraph_0", "table_1", "header_sdt_2_0"
    "text": str,               # Извлечённый текст блока
    "content": str,            # Альтернативное поле для текста
    "element": object,         # Ссылка на оригинальный элемент DOCX (Paragraph, Table, _Element)
    "type": str                # Тип: "paragraph", "table", "header", "header_sdt", "footer"
}
```

### **2.3. Типы извлекаемых блоков**

| Тип блока | Источник | Пример block_id | Element Type |
|-----------|----------|-----------------|--------------|
| **Параграф** | `doc.paragraphs` | `paragraph_0` | `docx.text.paragraph.Paragraph` |
| **Таблица** | `doc.tables` | `table_0` | `docx.table.Table` |
| **Заголовок** | `section.header.paragraphs` | `header_1_0` | `docx.text.paragraph.Paragraph` |
| **SDT заголовка** | `section.header._element.xpath` | `header_sdt_1_0` | `lxml.etree._Element` |
| **Подвал** | `section.footer.paragraphs` | `footer_1_0` | `docx.text.paragraph.Paragraph` |

**Пример:**
```python
blocks = [
    {
        "block_id": "header_sdt_1_0",
        "text": "PAGE 6 ЕИСУФХД.13/ОК-2023.3.ПМ.1 312822699534",
        "element": <lxml.etree._Element>,
        "type": "header_sdt"
    },
    {
        "block_id": "paragraph_0",
        "text": "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ",
        "element": <Paragraph object>,
        "type": "paragraph"
    },
    {
        "block_id": "table_0",
        "text": "УТВЕРЖДАЮ | УТВЕРЖДАЮ\nНачальник...",
        "element": <Table object>,
        "type": "table"
    }
]
```

---

## 🎯 ЭТАП 3: ДЕТЕКЦИЯ ЧУВСТВИТЕЛЬНЫХ ДАННЫХ

### **3.1. Rule Engine: Regex паттерны**

**Сервис:** `Unified Document Service`  
**Компонент:** `RuleAdapter`  
**Файл:** `unified_document_service/app/rule_adapter.py`

**Обработка:**
```python
processed_blocks = self.rule_engine.apply_rules_to_blocks(blocks)

# Для КАЖДОГО блока отдельно:
for block in blocks:
    text = block.get('text', '')
    regex_matches = self._find_regex_matches(text)  # ← Regex на текст ОДНОГО блока
    block['sensitive_patterns'] = regex_matches
```

**Источник паттернов:**  
`unified_document_service/patterns/sensitive_patterns.xlsx`

**Формат паттерна в Excel:**
| category | pattern | confidence | description |
|----------|---------|------------|-------------|
| person_name | `([А-ЯЁ]\.\s?[А-ЯЁ]\.\s?[А-ЯЁа-яё]+)` | 0.9 | ФИО с инициалами |
| inn | `(\d{10}\|\d{12})` | 1.0 | ИНН 10 или 12 цифр |
| email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | 1.0 | Email адрес |
| contract_number | `Государственн(ый\|ого\|ому) контракт(а\|у).*?№\s*[\d/А-Я-]+` | 0.95 | Гос. контракт |

**Результат:**
```python
rule_engine_matches = [
    {
        "block_id": "table_0",
        "original_value": "К. С. Мясников",
        "position": {"start": 233, "end": 247},
        "element": <Table object>,
        "category": "person_name",
        "confidence": 0.9,
        "source": "rule_engine",
        "method": "regex"
    }
]
```

---

### **3.2. NLP Service: AI-детекция**

**Сервис:** `NLP Service` (внешний микросервис)  
**Порт:** 8006  
**Endpoint:** `POST /analyze`

**Обработка (ПОБЛОЧНАЯ с недавнего исправления):**
```python
# ДО исправления: отправлялся весь документ целиком
# ПОСЛЕ исправления: каждый блок обрабатывается отдельно

for block in blocks:
    block_text = block.get('text', '')
    if not block_text.strip():
        continue
    
    # Вызов NLP Service для ОДНОГО блока
    block_detections = self._call_nlp_service(block_text)
    
    # Добавление детекций с привязкой к блоку
    for detection in block_detections:
        nlp_matches.append({
            "block_id": block["block_id"],
            "original_value": detection["original_value"],
            "position": detection["position"],  # Уже относительно блока!
            "element": block.get("element"),
            "category": detection["category"],
            "confidence": detection["confidence"],
            "source": "nlp_service",
            "method": detection["method"]
        })
```

**Запрос к NLP Service:**
```python
# Метод: _call_nlp_service(text: str)
payload = {
    "blocks": [
        {
            "content": text,           # Текст ОДНОГО блока
            "block_id": "doc_block_1",
            "block_type": "text"
        }
    ],
    "options": {}
}

response = requests.post(
    "http://localhost:8006/analyze",
    json=payload,
    timeout=30
)
```

**Ответ от NLP Service:**
```python
{
    "success": true,
    "detections": [
        {
            "category": "organization",
            "original_value": "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ",
            "confidence": 1.0,
            "position": {"start": 0, "end": 45},  # Позиция относительно блока
            "method": "regex",
            "uuid": "generated-uuid",
            "anonymized_text": null,
            "block_id": "doc_block_1"
        }
    ],
    "total_detections": 1,
    "blocks_processed": 1
}
```

**Методы детекции NLP Service:**
- `regex` — регулярные выражения из nlp_patterns.json
- `custom_matcher` — spaCy Matcher (персонализированные паттерны)
- `spaced_abbreviation` — аббревиатуры с пробелами (ЕИС УФХД ПК)
- `complex_abbreviation` — сложные аббревиатуры (ЕИСУФХД)
- `information_system_regex` — информационные системы

**Файл паттернов NLP:**  
`nlp_service/patterns/nlp_patterns.json` (31 паттерн)

---

### **3.3. Комбинирование результатов**

```python
# Начинаем с NLP (более точные)
all_matches = nlp_matches.copy()

# Добавляем Rule Engine детекции, которые НЕ пересекаются с NLP
for re_match in rule_engine_matches:
    is_duplicate = False
    for nlp_match in nlp_matches:
        if (re_match['block_id'] == nlp_match['block_id'] and
            positions_overlap(re_match['position'], nlp_match['position'])):
            is_duplicate = True
            break
    
    if not is_duplicate:
        all_matches.append(re_match)

# Итого: уникальные детекции из обоих источников
print(f"Найдено: Rule Engine={len(rule_engine_matches)}, NLP={len(nlp_matches)}")
print(f"Итого уникальных: {len(all_matches)}")
```

**Результат комбинирования:**
```python
all_matches = [
    # NLP детекции
    {
        "block_id": "paragraph_0",
        "original_value": "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ",
        "position": {"start": 0, "end": 45},
        "element": <Paragraph>,
        "category": "organization",
        "confidence": 1.0,
        "source": "nlp_service",
        "method": "regex"
    },
    # Rule Engine детекции (не пересекающиеся с NLP)
    {
        "block_id": "table_0",
        "original_value": "312822699534",
        "position": {"start": 450, "end": 462},
        "element": <Table>,
        "category": "inn",
        "confidence": 1.0,
        "source": "rule_engine",
        "method": "regex"
    }
]
```

---

## 🎯 ЭТАП 4: ПРИМЕНЕНИЕ ЗАМЕН

**Сервис:** `Unified Document Service`  
**Компонент:** `FormatterApplier`  
**Файл:** `unified_document_service/app/formatter_applier.py`

### **4.1. Нормализация замен с UUID**

```python
# Метод: apply_replacements_to_document(doc, all_matches)
normalized_replacements = self._normalize_replacements_with_centralized_uuids(all_matches)
```

**Генерация UUID (детерминистическая):**
```python
# Используется UUIDMapper
uuid = uuid_mapper.get_uuid_for_text(original_value, category)

# Алгоритм:
namespace = UUID("document-anonymization-namespace")
hash_input = f"{original_value.lower()}_{category}"
uuid = uuid5(namespace, hash_input)

# Пример:
original_value = "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ"
category = "organization"
→ UUID: "5b407955-d6e1-59ab-a5f5-50f38ec7291b"
```

### **4.2. Группировка замен по блокам**

```python
replacements_by_block = {}
for replacement in all_matches:
    block_id = replacement.get('block_id')
    if block_id not in replacements_by_block:
        replacements_by_block[block_id] = []
    replacements_by_block[block_id].append(replacement)

# Результат:
# {
#     "paragraph_0": [match1, match2],
#     "table_0": [match3, match4, match5]
# }
```

### **4.3. Обработка каждого блока**

```python
for block_id, block_replacements in replacements_by_block.items():
    # Сортируем замены в обратном порядке позиций
    # (чтобы замены в конце не сдвигали позиции для замен в начале)
    block_replacements.sort(key=lambda x: x['position']['start'], reverse=True)
    
    # Применяем замены к блоку
    block_stats = self._apply_replacements_to_block(block_replacements)
```

### **4.4. Применение одной замены**

```python
# Метод: _apply_single_replacement(replacement)

element = replacement.get('element')           # Ссылка на DOCX элемент
original_value = replacement.get('original_value')
replacement_value = replacement.get('uuid')    # UUID для замены
position = replacement.get('position')

# Определяем тип элемента и применяем соответствующий метод:

if 'lxml' in str(type(element)):
    # SDT элемент (Structured Document Tag) - XML элемент
    result = _replace_in_sdt(element, original_value, replacement_value)
    
elif hasattr(element, 'rows'):
    # Таблица
    result = _replace_in_table(element, original_value, replacement_value, position)
    
elif hasattr(element, 'text'):
    # Параграф
    result = _replace_in_paragraph(element, original_value, replacement_value, position)
```

---

### **4.5. Замена в ПАРАГРАФЕ**

**Компонент:** `FormatterApplier._replace_in_paragraph()`

**Проблема:** Текст в параграфе может быть разбит на несколько **runs** (фрагментов с разным форматированием).

**Пример:**
```python
Параграф: "Министерство информационного развития"
Run 0:    "Министерство "       (жирный)
Run 1:    "информационного "    (обычный)
Run 2:    "развития"            (курсив)
```

**Алгоритм замены:**

**Шаг 1: Поиск в одном run**
```python
for i, run in enumerate(paragraph.runs):
    run_text = run.text or ''
    
    # Прямое совпадение
    if original_value in run_text:
        run.text = run_text.replace(original_value, replacement_value, 1)
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW  # Выделение
        return True
```

**Шаг 2: Поиск в нескольких runs**
```python
# Собираем полный текст из всех runs
full_text = ''.join(run.text for run in paragraph.runs)

if original_value in full_text:
    start_pos = full_text.find(original_value)
    end_pos = start_pos + len(original_value)
    
    # Находим затронутые runs и заменяем
    return _replace_across_runs(paragraph, original_value, replacement_value, start_pos, end_pos)
```

**Шаг 3: Замена через runs (сохранение форматирования)**
```python
# Определяем какие runs затронуты
affected_runs = []
current_pos = 0

for i, run in enumerate(paragraph.runs):
    run_start = current_pos
    run_end = current_pos + len(run.text)
    
    # Проверяем пересечение
    if not (run_end <= start_pos or run_start >= end_pos):
        affected_runs.append({
            'index': i,
            'run': run,
            'text_start': max(0, start_pos - run_start),
            'text_end': min(len(run.text), end_pos - run_start)
        })
    
    current_pos = run_end

# Заменяем в первом run, остальные обрезаем
for i, run_info in enumerate(affected_runs):
    if i == 0:
        # Первый run - вставляем replacement_value
        run.text = run.text[:text_start] + replacement_value + run.text[text_end:]
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    else:
        # Остальные runs - удаляем затронутый текст
        run.text = run.text[:text_start] + run.text[text_end:]
```

---

### **4.6. Замена в ТАБЛИЦЕ**

**Компонент:** `FormatterApplier._replace_in_table()`

**Алгоритм:**

**Шаг 1: Построение карты позиций ячеек**
```python
table_text = ""
cell_positions = []

for row_idx, row in enumerate(table.rows):
    for cell_idx, cell in enumerate(row.cells):
        cell_text = cell.text or ''
        cell_start = len(table_text)
        table_text += cell_text
        cell_end = len(table_text)
        
        cell_positions.append({
            'row': row_idx,
            'col': cell_idx,
            'start': cell_start,
            'end': cell_end,
            'cell': cell,
            'text': cell_text
        })
        
        # Разделитель между ячейками (как в BlockBuilder)
        if cell_idx < len(row.cells) - 1:
            table_text += " | "
    
    table_text += "\n"  # Новая строка после каждой строки таблицы
```

**Пример:**
```
Таблица:
┌──────────┬──────────┐
│ Ячейка A │ Ячейка B │
├──────────┼──────────┤
│ Ячейка C │ Ячейка D │
└──────────┴──────────┘

table_text = "Ячейка A | Ячейка B\nЯчейка C | Ячейка D\n"

cell_positions = [
    {row: 0, col: 0, start: 0, end: 8, text: "Ячейка A"},
    {row: 0, col: 1, start: 11, end: 19, text: "Ячейка B"},
    {row: 1, col: 0, start: 20, end: 28, text: "Ячейка C"},
    {row: 1, col: 1, start: 31, end: 39, text: "Ячейка D"}
]
```

**Шаг 2: Поиск ячейки по позиции**
```python
target_position = position_info.get('start')  # Позиция из детекции

for cell_info in cell_positions:
    if original_value in cell_info['text']:
        # Проверка позиции
        if target_position is None or (cell_info['start'] <= target_position < cell_info['end']):
            target_cell = cell_info
            break
```

**Шаг 3: Замена в найденной ячейке**
```python
cell = target_cell['cell']

for paragraph in cell.paragraphs:
    if original_value in paragraph.text:
        # Используем стандартный метод замены в параграфе
        self._replace_in_paragraph(paragraph, original_value, replacement_value, {})
        return True
```

---

### **4.7. Замена в SDT (Structured Document Tag)**

**Компонент:** `FormatterApplier._apply_single_replacement()` (SDT блок)

**Что такое SDT:** XML элементы в заголовках/подвалах DOCX

**Алгоритм:**
```python
# Используем XPath для поиска текстовых элементов
text_elements = element.xpath(
    './/w:t',
    namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
)

for text_element in text_elements:
    current_text = text_element.text or ''
    
    if original_value in current_text:
        # Прямая замена текста в XML элементе
        new_text = current_text.replace(original_value, replacement_value, 1)
        text_element.text = new_text
        return True
```

**Пример SDT:**
```xml
<w:sdt>
    <w:p>
        <w:r>
            <w:t>ЕИСУФХД.13/ОК-2023</w:t>
        </w:r>
    </w:p>
</w:sdt>

После замены:
<w:t>9112b0d5-9237-56e3-a2df-210912cecc09.13/ОК-2023</w:t>
```

---

### **4.8. Обработка заголовков и подвалов**

```python
# Дополнительная обработка после основной замены
header_footer_stats = self._apply_replacements_to_headers_footers(doc, normalized_replacements)

# Проходим по всем секциям документа
for section in doc.sections:
    # Заголовки
    for paragraph in section.header.paragraphs:
        # Применяем те же замены
        
    # Подвалы
    for paragraph in section.footer.paragraphs:
        # Применяем те же замены
```

---

## 🎯 ЭТАП 5: СОХРАНЕНИЕ ДОКУМЕНТА

```python
doc.save(output_path)
```

**Что сохраняется:**
- Все замены применены
- Форматирование сохранено
- UUID выделены жёлтым цветом (если `highlight_replacements=True`)
- Структура документа не изменена

---

## 🎯 ЭТАП 6: ГЕНЕРАЦИЯ ОТЧЁТОВ

### **6.1. Excel отчёт**

**Метод:** `FullAnonymizer._generate_excel_report()`

**Структура Excel:**
```
| № | Исходное значение | UUID замены | Категория | Метод | Confidence |
|---|-------------------|-------------|-----------|-------|------------|
| 1 | ЕИСУФХД | 9112b0d5-... | information_system | complex_abbreviation | 1.0 |
| 2 | К. С. Мясников | 871f90b0-... | person_name | custom_matcher | 0.9 |
| 3 | МИНИСТЕРСТВО... | 5b407955-... | organization | regex | 1.0 |
```

**Генерация UUID для отчёта:**
```python
for match in all_matches:
    original_value = match['original_value']
    category = match['category']
    
    # Генерируем UUID через UUIDMapper (детерминистически)
    uuid = self.formatter.uuid_mapper.get_uuid_for_text(original_value, category)
    
    worksheet.append([
        index,
        original_value,
        uuid,
        category,
        match.get('method', 'N/A'),
        match.get('confidence', 'N/A')
    ])
```

---

### **6.2. JSON журнал**

**Метод:** `FullAnonymizer._generate_json_ledger()`

**Структура JSON:**
```json
{
  "ledger_version": "1.0",
  "timestamp": "2025-12-03T16:33:40",
  "statistics": {
    "total_replacements": 29,
    "categories": {
      "person_name": 3,
      "organization": 2,
      "information_system": 12,
      "contract_number": 5,
      "inn": 2,
      "email": 1
    }
  },
  "replacements": [
    {
      "original_value": "МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ",
      "uuid": "5b407955-d6e1-59ab-a5f5-50f38ec7291b",
      "category": "organization",
      "method": "regex",
      "confidence": 1.0,
      "source": "nlp_service"
    }
  ]
}
```

---

## 🎯 ЭТАП 7: ВОЗВРАТ РЕЗУЛЬТАТА

```python
# Конвертируем файлы в Base64
with open(output_path, 'rb') as f:
    anonymized_doc_base64 = base64.b64encode(f.read()).decode('utf-8')

with open(excel_path, 'rb') as f:
    excel_report_base64 = base64.b64encode(f.read()).decode('utf-8')

# Возвращаем результат
return JSONResponse({
    "status": "success",
    "statistics": {
        "total_replacements": 29,
        "categories": {...}
    },
    "files_base64": {
        "anonymized_document_base64": anonymized_doc_base64,
        "excel_report_base64": excel_report_base64,
        "json_ledger_base64": json_ledger_base64
    }
})
```

---

## 📊 ФОРМАТ ДАННЫХ МЕЖДУ КОМПОНЕНТАМИ

### **1. Block Builder → Rule Engine / NLP Service**
```python
{
    "block_id": str,
    "text": str,
    "element": object,
    "type": str
}
```

### **2. NLP Service → Full Anonymizer**
```python
{
    "category": str,
    "original_value": str,
    "confidence": float,
    "position": {"start": int, "end": int},
    "method": str,
    "block_id": str
}
```

### **3. Rule Engine → Full Anonymizer**
```python
{
    "category": str,
    "original_value": str,
    "position": {"start": int, "end": int},
    "confidence": float,
    "source": "regex"
}
```

### **4. Full Anonymizer → Formatter Applier**
```python
{
    "block_id": str,
    "original_value": str,
    "uuid": str,  # Детерминистический UUID
    "position": {"start": int, "end": int},
    "element": object,  # Ссылка на DOCX элемент
    "category": str,
    "confidence": float,
    "source": str,
    "method": str
}
```

---

## 🔑 КЛЮЧЕВЫЕ ОСОБЕННОСТИ ПРОЦЕССА

### ✅ **Преимущества текущей реализации:**

1. **Поблочная обработка** — гарантирует, что детекции всегда корректно мапятся на элементы
2. **Детерминистические UUID** — одинаковые значения всегда получают одинаковые UUID
3. **Сохранение форматирования** — замены происходят на уровне runs, форматирование не теряется
4. **Два источника детекций** — NLP Service + Rule Engine обеспечивают высокую точность
5. **Выделение UUID** — жёлтый фон помогает визуально проверить замены
6. **Дедупликация** — пересекающиеся детекции из разных источников не дублируются

### ⚠️ **Ограничения:**

1. **Не обрабатываются многоблочные детекции** — если текст распределён по нескольким блокам, он не будет заменён целиком
2. **Зависимость от NLP Service** — если NLP Service недоступен, детекции будут только от Rule Engine
3. **Позиционная зависимость** — если позиции неточные, замена может не сработать

---

## 📈 СТАТИСТИКА ПРИМЕРА ВЫПОЛНЕНИЯ

**Входной документ:** `test_01_1_4_SD33.docx`

**Результаты:**
- **Блоков извлечено:** ~50
- **Детекций NLP Service:** 21
- **Детекций Rule Engine:** 3
- **Итого уникальных детекций:** 24
- **Выполнено замен:** 29 (некоторые значения встречаются несколько раз)
- **Категории:**
  - person_name: 3
  - organization: 2
  - information_system: 12
  - contract_number: 5
  - inn: 2
  - email: 1

**Время обработки:** ~5-10 секунд

---

## 🎓 ЗАКЛЮЧЕНИЕ

Процесс анонимизации — это **многоступенчатый конвейер**, где каждый компонент выполняет специфическую задачу:

1. **BlockBuilder** — структурирует документ
2. **RuleAdapter** — применяет regex паттерны
3. **NLP Service** — использует AI для детекции
4. **FullAnonymizer** — координирует весь процесс
5. **FormatterApplier** — выполняет замены с сохранением форматирования
6. **UUIDMapper** — обеспечивает детерминистические UUID

Вся система работает **синхронно и последовательно**, что гарантирует консистентность результата.
