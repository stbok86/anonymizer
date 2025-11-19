"""
ТЕХНИЧЕСКАЯ ДЕТАЛИЗАЦИЯ ПРОЦЕССА АНОНИМИЗАЦИИ
==============================================

На примере: "Общество с ограниченной ответственностью «КАМА Технологии»" из paragraph_82

Этот файл содержит детальное объяснение каждого этапа с ссылками на конкретный код.
"""

def detailed_code_explanation():
    print("🔍 ТЕХНИЧЕСКАЯ ДЕТАЛИЗАЦИЯ АНОНИМИЗАЦИИ")
    print("=" * 80)
    
    # ============================================================================
    # ЭТАП 1: ИНИЦИАЦИЯ ПРОЦЕССА (Frontend)
    # ============================================================================
    print("\n📱 ЭТАП 1: ИНИЦИАЦИЯ ПРОЦЕССА")
    print("-" * 35)
    
    print("📍 Файл: frontend/streamlit_app.py, строки 319-356")
    print("🔧 Функция: step2_analyze_results() при нажатии кнопки")
    print()
    
    print("💻 Код (упрощенно):")
    print("""
if st.button("🔒 Подтвердить анонимизацию"):
    # Получаем одобренные пользователем элементы
    approved_items = [item for item in st.session_state.found_data 
                     if item.get('approved', False)]
    
    # Вызываем API для анонимизации
    anonymized_files = anonymize_document_full_api(
        st.session_state.uploaded_file, 
        approved_items,
        st.session_state.patterns_file
    )
""")
    print()
    
    # ============================================================================
    # ЭТАП 2: HTTP API ВЫЗОВ (Frontend → Gateway)
    # ============================================================================
    print("🌐 ЭТАП 2: HTTP API ВЫЗОВ")
    print("-" * 25)
    
    print("📍 Файл: frontend/streamlit_app.py, строки 609-680")
    print("🔧 Функция: anonymize_document_full_api()")
    print()
    
    print("💻 Код:")
    print("""
def anonymize_document_full_api(uploaded_file, approved_items, patterns_file):
    files = {
        'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/...')
    }
    
    data = {
        'patterns_file': patterns_file,
        'selected_items': json.dumps([{
            'block_id': item.get('block_id', ''),
            'original_value': item.get('original_value', ''),
            'uuid': item.get('uuid', ''),  # ⭐ UUID уже сгенерирован!
            'position': item.get('position', {}),
            'category': item.get('category', 'unknown'),
            'confidence': item.get('confidence', 1.0)
        } for item in approved_items])
    }
    
    # POST запрос к Gateway
    response = requests.post(f"{API_BASE_URL}/anonymize_selected", files=files, data=data)
""")
    print()
    
    # ============================================================================
    # ЭТАП 3: GATEWAY ПРОКСИРОВАНИЕ
    # ============================================================================
    print("🚪 ЭТАП 3: GATEWAY ПРОКСИРОВАНИЕ")
    print("-" * 33)
    
    print("📍 Файл: gateway/app/main.py, строки 248-310")
    print("🔧 Функция: anonymize_selected()")
    print()
    
    print("💻 Код:")
    print("""
@app.post("/anonymize_selected")
async def anonymize_selected(file: UploadFile, selected_items: str, patterns_file: str):
    files = {'file': (file.filename, file.file, file.content_type)}
    data = {'patterns_file': patterns_file, 'selected_items': selected_items}
    
    # Пересылаем к unified_document_service
    response = requests.post(f"{UNIFIED_SERVICE_URL}/anonymize_selected", 
                           files=files, data=data, timeout=120)
    
    if response.status_code == 200:
        return response.json()  # Возвращаем результат
""")
    print()
    
    # ============================================================================
    # ЭТАП 4: ОСНОВНАЯ ОБРАБОТКА (Unified Service)
    # ============================================================================
    print("🎯 ЭТАП 4: ОСНОВНАЯ ОБРАБОТКА")
    print("-" * 30)
    
    print("📍 Файл: unified_document_service/app/main.py, строки 387-460")
    print("🔧 Функция: anonymize_selected()")
    print()
    
    print("💻 Код:")
    print("""
@app.post("/anonymize_selected")
async def anonymize_selected(file: UploadFile, selected_items: str):
    # Сохраняем файл во временную директорию
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    output_path = tmp_path.replace(".docx", "_anonymized.docx")
    
    # Парсим выбранные элементы из JSON
    selected_items_list = json.loads(selected_items)
    
    # Инициализируем анонимизатор
    anonymizer = FullAnonymizer()
    
    # ⭐ КЛЮЧЕВОЙ ВЫЗОВ: выполняем анонимизацию
    result = anonymizer.anonymize_selected_items(
        input_path=tmp_path,
        output_path=output_path,
        selected_items=selected_items_list
    )
""")
    print()
    
    # ============================================================================
    # ЭТАП 5: ПОЛНАЯ АНОНИМИЗАЦИЯ (FullAnonymizer)
    # ============================================================================
    print("🔧 ЭТАП 5: ПОЛНАЯ АНОНИМИЗАЦИЯ")
    print("-" * 30)
    
    print("📍 Файл: unified_document_service/app/full_anonymizer.py, строки 248-320")
    print("🔧 Метод: FullAnonymizer.anonymize_selected_items()")
    print()
    
    print("💻 Код:")
    print("""
def anonymize_selected_items(self, input_path: str, output_path: str, selected_items: List[Dict]):
    # Загружаем документ
    doc = Document(input_path)
    
    # Извлекаем блоки документа
    blocks = self.block_builder.build_blocks(doc)
    
    # Создаем карту блоков для быстрого поиска
    blocks_map = {block['block_id']: block for block in blocks}
    
    # Подготавливаем замены
    replacements_for_formatting = []
    seen_replacements = set()  # Дедупликация
    
    for item in selected_items:
        block_id = item.get('block_id')  # 'paragraph_82'
        original_value = item.get('original_value', '')  # 'Общество с ограниченной...'
        
        # ⭐ Дедупликация: создаем уникальный ключ
        dedup_key = (block_id, original_value, position.get('start'), position.get('end'))
        
        if dedup_key not in seen_replacements:
            seen_replacements.add(dedup_key)
            
            if block_id in blocks_map:
                block = blocks_map[block_id]
                replacement = {
                    'block_id': block_id,
                    'original_value': original_value,
                    'uuid': item['uuid'],  # ⭐ Используем существующий UUID!
                    'position': item['position'],
                    'element': block.get('element'),  # ⭐ Ссылка на объект параграфа
                    'category': item['category']
                }
                replacements_for_formatting.append(replacement)
    
    # ⭐ ПРИМЕНЯЕМ ЗАМЕНЫ
    replacement_stats = self.formatter.apply_replacements_to_document(doc, replacements_for_formatting)
    
    # Сохраняем результат
    doc.save(output_path)
""")
    print()
    
    # ============================================================================
    # ЭТАП 6: ПРИМЕНЕНИЕ ЗАМЕН (FormatterApplier)
    # ============================================================================
    print("✨ ЭТАП 6: ПРИМЕНЕНИЕ ЗАМЕН")
    print("-" * 27)
    
    print("📍 Файл: unified_document_service/app/formatter_applier.py")
    print("🔧 Метод: FormatterApplier.apply_replacements_to_document()")
    print()
    
    print("💻 Ключевые части кода:")
    print()
    
    print("🗂️ Группировка и сортировка:")
    print("""
# Группируем замены по блокам
replacements_by_block = {}
for replacement in replacements:
    block_id = replacement.get('block_id')
    if block_id not in replacements_by_block:
        replacements_by_block[block_id] = []
    replacements_by_block[block_id].append(replacement)

# Обрабатываем каждый блок
for block_id, block_replacements in replacements_by_block.items():
    # ⭐ ВАЖНО: Сортируем в ОБРАТНОМ порядке!
    block_replacements.sort(key=lambda x: x.get('position', {}).get('start', 0), reverse=True)
""")
    print()
    
    print("🔧 Применение одной замены:")
    print("""
def _apply_single_replacement(self, replacement: Dict) -> bool:
    element = replacement.get('element')  # Объект параграфа из docx
    original_value = replacement.get('original_value', '')
    
    # ⭐ Генерируем замещающее значение
    replacement_value = self._generate_replacement_value(
        original_value, 
        replacement.get('category', 'unknown'),
        replacement.get('uuid')  # Используем существующий UUID!
    )
    
    if hasattr(element, 'text'):
        # ⭐ ЗАМЕНА В ПАРАГРАФЕ
        return self._replace_in_paragraph(element, original_value, replacement_value, position)
    elif hasattr(element, 'rows'):
        # ⭐ ЗАМЕНА В ТАБЛИЦЕ
        return self._replace_in_table(element, original_value, replacement_value)
""")
    print()
    
    print("🔑 Генерация замещающего значения:")
    print("""
def _generate_replacement_value(self, original_value: str, category: str, existing_uuid: str = None) -> str:
    if existing_uuid:
        # ⭐ Используем UUID, который был сгенерирован на этапе анализа!
        replacement_uuid = existing_uuid
    else:
        # Генерируем новый UUID (редкий случай)
        replacement_uuid = str(uuid.uuid4())
    
    # ⭐ Возвращаем только UUID без префиксов
    return replacement_uuid
""")
    print()
    
    # ============================================================================
    # ФИНАЛЬНЫЙ РЕЗУЛЬТАТ
    # ============================================================================
    print("🎯 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ")
    print("-" * 20)
    
    print("📊 Результат для нашего примера:")
    print("   📝 Исходный текст: 'Общество с ограниченной ответственностью «КАМА Технологии»'")
    print("   🔑 UUID замены: '4f8b1c2d-9e7a-4d3b-8c6f-1a2b3c4d5e6f'")
    print("   📄 Документ после замены: параграф будет содержать UUID вместо названия компании")
    print("   💾 Сохранение: Документ сохраняется с примененными заменами")
    print("   📤 Возврат: base64-encoded файл отправляется обратно пользователю")
    print()
    
    print("🔒 БЕЗОПАСНОСТЬ:")
    print("   • UUID необратимы - исходное значение невозможно восстановить")
    print("   • Каждое значение получает уникальный UUID")
    print("   • Форматирование документа сохраняется")
    print("   • Позиции точно определяют место замены")
    print()
    
    print("📈 ПРОИЗВОДИТЕЛЬНОСТЬ:")
    print("   • Дедупликация предотвращает повторные замены")
    print("   • Обратная сортировка сохраняет корректность позиций")
    print("   • Блочная обработка повышает эффективность")
    print()

if __name__ == "__main__":
    detailed_code_explanation()