# -*- coding: utf-8 -*-
import spacy

nlp = spacy.load('ru_core_news_sm')

test_texts = [
    'А. С. Щукина',
    'К.\xa0С. Мясников',
    'В. В. Евтушенко'
]

for text in test_texts:
    doc = nlp(text)
    print(f"\nText: {repr(text)}")
    print(f"Tokens ({len(doc)}):")
    for token in doc:
        print(f"  '{token.text}' → POS={token.pos_}, LENGTH={len(token.text)}, IS_TITLE={token.is_title}")
