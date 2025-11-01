"""CLI para comparar abstracts desde `descargas/unificado.bib`.

Uso: ejecutar desde la raíz del proyecto:
    python -m src.bibliometria.compare_abstracts

El script carga el archivo `descargas/unificado.bib`, lista las entradas (key y título),
pide al usuario seleccionar una o más entradas por clave o índice, extrae el campo
`abstract` (o `note`/`title` si no existe) y calcula matrices de similitud usando:
 - Cosine (TF-IDF)
 - Jaccard (tokens)
 - Jaro-Winkler

Imprime resultados en la terminal.
"""
from __future__ import annotations
import os
import sys
from typing import List, Dict

try:
    import bibtexparser  
except Exception:
    bibtexparser = None

import cosine_similarity
import jaccard_similarity
import jaro_winkler
import sorensen_Dice
import overlap_similarity
try:
    import cosine_similarity_embeddings
except Exception:
    # Embeddings are optional (sentence-transformers may be missing). Provide a stub
    # object with the same interface so the CLI/server can still run other algorithms.
    class _MissingEmbeddings:
        def compare_texts(self, texts):
            raise RuntimeError("Embeddings not available: install 'sentence-transformers' to enable this module")

    cosine_similarity_embeddings = _MissingEmbeddings()

# === FUNCIONES AUXILIARES ===
def _extract_braced_value(s: str, start_idx: int) -> tuple[str, int]:
    assert s[start_idx] == '{'
    depth = 0
    i = start_idx
    buf = []
    while i < len(s):
        ch = s[i]
        if ch == '{':
            depth += 1
            if depth > 1:
                buf.append(ch)
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return (''.join(buf).strip(), i + 1)
            else:
                buf.append(ch)
        else:
            buf.append(ch)
        i += 1
    return (''.join(buf).strip(), i)


def _extract_quoted_value(s: str, start_idx: int) -> tuple[str, int]:
    i = start_idx
    assert s[i] == '"'
    i += 1
    buf = []
    while i < len(s):
        ch = s[i]
        if ch == '"':
            return (''.join(buf), i + 1)
        if ch == '\\' and i + 1 < len(s):
            buf.append(s[i + 1])
            i += 2
            continue
        buf.append(ch)
        i += 1
    return (''.join(buf), i)


def _extract_field(entry_text: str, field: str) -> str:
    idx = entry_text.lower().find(field.lower())
    if idx == -1:
        return ''
    eq = entry_text.find('=', idx)
    if eq == -1:
        return ''
    i = eq + 1
    while i < len(entry_text) and entry_text[i].isspace():
        i += 1
    if i >= len(entry_text):
        return ''
    if entry_text[i] == '{':
        val, _ = _extract_braced_value(entry_text, i)
        return val.strip()
    if entry_text[i] == '"':
        val, _ = _extract_quoted_value(entry_text, i)
        return val.strip()
    j = i
    buf = []
    while j < len(entry_text) and entry_text[j] not in ',\n':
        buf.append(entry_text[j])
        j += 1
    return ''.join(buf).strip().strip(',')


def _fallback_load_bib(path: str) -> list[dict]:
    text = open(path, 'r', encoding='utf-8').read()
    entries = []
    i = 0
    while True:
        at = text.find('@', i)
        if at == -1:
            break
        brace = text.find('{', at)
        if brace == -1:
            break
        comma = text.find(',', brace)
        if comma == -1:
            break
        key = text[brace + 1:comma].strip()
        depth = 1
        j = comma + 1
        while j < len(text) and depth > 0:
            if text[j] == '{':
                depth += 1
            elif text[j] == '}':
                depth -= 1
            j += 1
        entry_text = text[at:j]
        entry = {'ID': key}
        entry['title'] = _extract_field(entry_text, 'title')
        entry['abstract'] = _extract_field(entry_text, 'abstract')
        if not entry['abstract']:
            entry['abstract'] = _extract_field(entry_text, 'note') or _extract_field(entry_text, 'annote')
        entries.append(entry)
        i = j
    return entries


def load_bib(path: str) -> List[Dict]:
    if bibtexparser is not None:
        with open(path, 'r', encoding='utf-8') as f:
            return bibtexparser.load(f).entries
    return _fallback_load_bib(path)


def get_text_for_entry(entry: Dict) -> str:
    for key in ('abstract', 'note', 'annote', 'summary'):
        if key in entry and entry[key].strip():
            return entry[key].strip()
    if 'title' in entry:
        return entry['title'].strip()
    return ''


def print_matrix(name: str, labels: List[str], matrix: List[List[float]]):
    print(f"\n=== {name} ===")
    print('\t' + '\t'.join(labels))
    for label, row in zip(labels, matrix):
        print(label + '\t' + '\t'.join(f"{v:.4f}" for v in row))


# === FUNCIÓN PRINCIPAL ===
def main(argv: List[str] | None = None):
    import argparse

    parser = argparse.ArgumentParser(description='Comparar abstracts desde un archivo .bib')
    parser.add_argument('--bib-path', default=None, help='Ruta al archivo .bib (por defecto descargas/unificado.bib)')
    parser.add_argument('--keys', help='Claves o índices separadas por comas (por ejemplo: 0,3 o key1,key2)')
    parser.add_argument('--all', action='store_true', help='Seleccionar todas las entradas')
    args = parser.parse_args(argv)

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    bib_path = args.bib_path or os.path.join(root, 'descargas', 'unificado.bib')
    if not os.path.exists(bib_path):
        print(f"No se encontró {bib_path}. Asegúrate de ejecutar desde la raíz del proyecto.")
        sys.exit(1)

    entries = load_bib(bib_path)
    if not entries:
        print("No hay entradas en el archivo .bib.")
        sys.exit(1)

    keys = [e.get('ID', f'entry{i}') for i, e in enumerate(entries)]
    titles = [e.get('title', '').strip() for e in entries]

    chosen = []
    if args.all:
        chosen = list(range(len(entries)))
    elif args.keys:
        parts = [p.strip() for p in args.keys.split(',') if p.strip()]
        for p in parts:
            if p in keys:
                chosen.append(keys.index(p))
            elif p.isdigit():
                idx = int(p)
                if 0 <= idx < len(entries):
                    chosen.append(idx)
                else:
                    print(f"Índice fuera de rango: {idx}")
            else:
                print(f"Clave no encontrada: {p}")
    else:
        print("Entradas encontradas:")
        for i, (k, t) in enumerate(zip(keys, titles)):
            display = t if t else '<sin título>'
            print(f"{i}: {k} — {display}")
        sel = input("\nIntroduce claves o índices separados por comas (por ejemplo: 0,3 o key1,key2), o 'all' para todas: ").strip()
        if sel.lower() == 'all':
            chosen = list(range(len(entries)))
        else:
            parts = [p.strip() for p in sel.split(',') if p.strip()]
            for p in parts:
                if p in keys:
                    chosen.append(keys.index(p))
                elif p.isdigit():
                    idx = int(p)
                    if 0 <= idx < len(entries):
                        chosen.append(idx)
                    else:
                        print(f"Índice fuera de rango: {idx}")
                else:
                    print(f"Clave no encontrada: {p}")

    if not chosen:
        print("No se seleccionaron entradas válidas. Saliendo.")
        sys.exit(1)

    # === AHORA SÍ: procesar y mostrar ===
    labels = [keys[i] for i in chosen]
    texts = [get_text_for_entry(entries[i]) for i in chosen]

    cos_mat = cosine_similarity.compare_texts(texts)
    jac_mat = jaccard_similarity.compare_texts(texts)
    jw_mat = jaro_winkler.compare_texts(texts)
    sor_mat= sorensen_Dice.compare_texts(texts)
    ov_mat= overlap_similarity.compare_texts(texts)
    emb_mat = cosine_similarity_embeddings.compare_texts(texts)

    print_matrix('Cosine (TF-IDF)', labels, cos_mat)
    print_matrix('Jaccard (tokens)', labels, jac_mat)
    print_matrix('Jaro-Winkler', labels, jw_mat)
    print_matrix('Sorensen–Dice', labels, sor_mat)
    print("=============Modelos de IA=============")
    print_matrix('overlap_similarity', labels, ov_mat)
    print_matrix('Cosine (embeddings)', labels, emb_mat)


if __name__ == '__main__':
    main()
