# NLP Service Setup Instructions

## Установка зависимостей

### 1. Установка Python пакетов
```bash
cd c:\Projects\Anonymizer\nlp_service
pip install -r requirements.txt
```

### 2. Установка spaCy модели для русского языка

Попробуйте установить модель в следующем порядке (от лучшей к базовой):

#### Большая модель (рекомендуется):
```bash
python -m spacy download ru_core_news_lg
```

#### Если большая модель недоступна, установите среднюю:
```bash 
python -m spacy download ru_core_news_md
```

#### Если средняя модель недоступна, установите малую:
```bash
python -m spacy download ru_core_news_sm  
```

### 3. Проверка установки
```bash
python -c "import spacy; nlp = spacy.load('ru_core_news_sm'); print('spaCy работает!')"
```

## Запуск сервиса

```bash
cd c:\Projects\Anonymizer\nlp_service\app
python main.py
```

Или через uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8003
```

## Проверка работы

### Health check:
```bash
curl http://localhost:8003/healthz
```

### Тестовый анализ:
```bash
curl -X POST "http://localhost:8003/test" -H "Content-Type: application/json" -d '"Иван Петров работает директором в ООО Рога и Копыта"'
```

## Структура NLP Service

```
nlp_service/
├── app/
│   ├── main.py              # FastAPI приложение
│   ├── nlp_adapter.py       # Основной NLP адаптер
│   └── __pycache__/
├── patterns/
│   ├── nlp_patterns.xlsx    # Паттерны для неструктурированных данных
│   └── create_nlp_patterns.py
├── requirements.txt         # Python зависимости
└── README.md               # Этот файл
```

## Возможности

- **spaCy NER**: Обнаружение именованных сущностей (PER, ORG, LOC)
- **Regex паттерны**: Поиск структурированных данных в тексте
- **Контекстные матчеры**: PhraseMatcher для должностей и ролей
- **Морфологический анализ**: Поиск имен по морфологическим признакам
- **Дедупликация**: Удаление перекрывающихся обнаружений

## Категории обнаружения

1. **person_name**: Имена, фамилии, отчества
2. **organization**: Названия организаций 
3. **position**: Должности и роли
4. **department**: Подразделения организации
5. **salary**: Информация о зарплатах
6. **financial_amount**: Денежные суммы
7. **health_info**: Медицинская информация
8. **beliefs**: Убеждения и взгляды
9. **login_credential**: Данные аутентификации  
10. **system_name**: Названия систем
11. **trade_secret**: Коммерческая тайна
12. **contract_info**: Договорная информация
13. **location**: Географические локации
14. **address_context**: Адресная информация

## API Endpoints

- `GET /healthz` - Проверка здоровья сервиса
- `GET /readyz` - Проверка готовности сервиса
- `POST /analyze` - Анализ блоков текста
- `GET /patterns` - Информация о паттернах
- `GET /categories` - Список категорий
- `POST /test` - Тестовый анализ текста