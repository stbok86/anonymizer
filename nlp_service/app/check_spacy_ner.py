# -*- coding: utf-8 -*-
import spacy

nlp = spacy.load("ru_core_news_sm")

texts = [
    'МИНИСТЕРСТВО ИНФОРМАЦИОННОГО РАЗВИТИЯ И СВЯЗИ',
    'Министерство информационного развития и связи',
    'ГБУ ПК «Центр информационного развития Пермского края»',
    'ООО «КАМА Технологии»',
]

for text in texts:
    doc = nlp(text)
    print(f"\nText: {text}")
    print(f"Entities: {[(ent.text, ent.label_) for ent in doc.ents]}")
