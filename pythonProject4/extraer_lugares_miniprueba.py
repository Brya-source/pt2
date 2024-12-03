import spacy
import re
import pymysql
from transformers import pipeline
import time
import requests

# Cargar el modelo de spaCy en español
nlp = spacy.load('es_core_news_lg')

# Usar otro modelo NER de Hugging Face
ner_model = pipeline("ner", model="dccuchile/bert-base-spanish-wwm-cased", aggregation_strategy="simple")

def diagnostico_spacy_bert(texto):
    # Extracción usando spaCy
    doc = nlp(texto)
    lugares_spacy = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    print(f"Lugares extraídos por spaCy (sin regex): {lugares_spacy}")

    # Extracción usando BART
    entidades = ner_model(texto)
    lugares_bert = [entidad['word'] for entidad in entidades if entidad['entity_group'] == 'LOC']
    print(f"Lugares extraídos por BERT (sin regex): {lugares_bert}")

# Prueba de diagnóstico
texto_prueba = (
    "Sujetos armados privaron de la libertad a Aníbal Roblero Castillo, "
    "alcalde electo por el Partido Verde Ecologista de México (PVEM) del municipio de Frontera Comalapa. "
    "El hecho tuvo lugar en un café del ejido Terán, del municipio de Tuxtla Gutiérrez, "
    "fue captado por la cámara de un tráiler y posteriormente compartido en redes sociales."
)

# Ejecutar prueba de diagnóstico
diagnostico_spacy_bert(texto_prueba)
