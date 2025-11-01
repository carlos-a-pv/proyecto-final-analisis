from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import io
import sys
import contextlib
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# load OpenAPI spec from separate JSON file. Prefer canonical openapi.json, fall back to openapi_fixed.json
_openapi_path = os.path.join('src', 'api', 'openapi.json')
_openapi_fixed = os.path.join('src', 'api', 'openapi_fixed.json')
openapi_spec = {}
# try canonical -> fixed fallback
for p in (_openapi_path, _openapi_fixed):
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as _f:
                openapi_spec = json.load(_f)
                break
        except Exception:
            openapi_spec = {}

# import helpers from the api package to keep this file focused on routes
from src.api.utils import load_module_from_path, extract_abstracts, list_bib_articles


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/openapi.json', methods=['GET'])
def openapi_json():
    return jsonify(openapi_spec)


@app.route('/docs', methods=['GET'])
def swagger_ui():
    html = '''<!doctype html><html><head><meta charset="utf-8"/><title>API Docs</title><link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4/swagger-ui.css"/></head><body><div id="swagger-ui"></div><script src="https://unpkg.com/swagger-ui-dist@4/swagger-ui-bundle.js"></script><script>window.onload=function(){SwaggerUIBundle({url:'/openapi.json',dom_id:'#swagger-ui',presets:[SwaggerUIBundle.presets.apis],layout:'BaseLayout'});};</script></body></html>'''
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route('/run/r1', methods=['POST'])
def run_r1():
    data = request.get_json(silent=True) or {}
    bib_path = data.get('bib', 'descargas/unificado.bib')
    script_path = os.path.join('src', 'r-1 automatizacion', 'automatizacion.py')
    if not os.path.exists(script_path):
        return jsonify({'error': 'script not found', 'path': script_path}), 404
    try:
        mod = load_module_from_path(script_path, name='r1_automatizacion')
    except Exception as e:
        return jsonify({'error': f'failed to load script: {e}'}), 500
    if not hasattr(mod, 'merge_bib_files'):
        return jsonify({'error': 'merge_bib_files not found'}), 500
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            mod.merge_bib_files(base_dir='descargas', output_file=bib_path, repetidos_file='descargas/repetidos.bib')
        return jsonify({'status': 'ok', 'output': buf.getvalue()})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e), 'output': buf.getvalue()}), 500


@app.route('/run/r2', methods=['GET', 'POST'])
def run_r2():
    """Run r2 comparisons. Supports GET (legacy a/b or keys param) and POST with JSON body:

    POST body example:
      {
        "bib": "descargas/unificado.bib",
        "limit": 50,
        "indices": [0,1,2],            # or
        "keys": ["ID1","ID2"],      # or
        "all": true
      }

    Returns per-algorithm NxN matrices for the selected entries.
    """
    data = {}
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        bib_path = data.get('bib', 'descargas/unificado.bib')
        raw_limit = data.get('limit', None)
    else:
        bib_path = request.args.get('bib', 'descargas/unificado.bib')
        raw_limit = request.args.get('limit', None)

    # parse optional 'limit' parameter; default is 50 for quick tests
    if raw_limit is not None:
        try:
            limit = int(raw_limit)
            if limit <= 0:
                raise ValueError()
        except Exception:
            return jsonify({'error': "Invalid 'limit' parameter (must be positive integer)."}), 400
    else:
        limit = 50

    # Extract entries via compare_abstracts loader later; also have a lightweight abstracts list for fallback
    # We will decide selection below based on request body (POST) or query params (GET).

    # Try to use the compare_abstracts script to produce the same outputs as its main()
    compare_path = os.path.join('src', 'r2 - bibliometria', 'compare_abstracts.py')
    if os.path.exists(compare_path):
        try:
            comp = load_module_from_path(compare_path, name='r2_compare_abstracts')
        except Exception as e:
            comp = None

        if comp is not None:
            # Load entries using the script's loader so we match behavior
            try:
                entries = comp.load_bib(bib_path)
            except Exception:
                entries = []

            if not entries:
                return jsonify({'error': 'No entries found in .bib', 'path': bib_path}), 400

            # build keys/titles
            keys = [e.get('ID', f'entry{i}') for i, e in enumerate(entries)]
            # determine chosen indices: support POST JSON 'indices' or 'keys' (list) or 'all'
            chosen = []
            if request.method == 'POST':
                # JSON form
                if data.get('all') in (True, 'true', '1'):
                    chosen = list(range(len(entries)))
                elif isinstance(data.get('indices'), list):
                    for v in data.get('indices'):
                        try:
                            iv = int(v)
                        except Exception:
                            continue
                        chosen.append(iv)
                elif isinstance(data.get('keys'), list):
                    for k in data.get('keys'):
                        if k in keys:
                            chosen.append(keys.index(k))
                        elif str(k).isdigit():
                            iv = int(k)
                            if 0 <= iv < len(entries):
                                chosen.append(iv)
                elif isinstance(data.get('keys'), str):
                    parts = [p.strip() for p in data.get('keys', '').split(',') if p.strip()]
                    for p in parts:
                        if p in keys:
                            chosen.append(keys.index(p))
                        elif p.isdigit():
                            iv = int(p)
                            if 0 <= iv < len(entries):
                                chosen.append(iv)
                else:
                    # fallback to first two
                    chosen = [0, 1]
            else:
                # GET legacy behavior: keys param (comma string) or all or a/b
                keys_param = request.args.get('keys')
                if request.args.get('all') == '1' or request.args.get('all') == 'true':
                    chosen = list(range(len(entries)))
                elif keys_param:
                    parts = [p.strip() for p in keys_param.split(',') if p.strip()]
                    for p in parts:
                        if p in keys:
                            chosen.append(keys.index(p))
                        elif p.isdigit():
                            idx = int(p)
                            if 0 <= idx < len(entries):
                                chosen.append(idx)
                else:
                    # fallback to a/b indices (if provided) or default 0,1
                    a_idx = request.args.get('a')
                    b_idx = request.args.get('b')
                    if a_idx is not None or b_idx is not None:
                        try:
                            a = int(a_idx) if a_idx is not None else 0
                            b = int(b_idx) if b_idx is not None else (a + 1)
                        except Exception:
                            return jsonify({'error': "Invalid article indices 'a' and 'b' (must be integers)."}), 400
                        chosen = [a, b]
                    else:
                        chosen = [0, 1]


            # validate chosen and dedupe while preserving order
            clean_chosen = []
            seen = set()
            for c in chosen:
                try:
                    ci = int(c)
                except Exception:
                    continue
                if 0 <= ci < len(entries) and ci not in seen:
                    seen.add(ci)
                    clean_chosen.append(ci)
            chosen = clean_chosen
            if not chosen:
                return jsonify({'error': 'No valid selections provided', 'n_available': len(entries)}), 400

            labels = [keys[i] for i in chosen]
            texts = [comp.get_text_for_entry(entries[i]) for i in chosen]

            # algorithms to run (match compare_abstracts)
            algs = [
                ('Cosine (TF-IDF)', 'cosine_similarity'),
                ('Jaccard (tokens)', 'jaccard_similarity'),
                ('Jaro-Winkler', 'jaro_winkler'),
                ('Sorensen–Dice', 'sorensen_Dice'),
                ('overlap_similarity', 'overlap_similarity'),
                ('Cosine (embeddings)', 'cosine_similarity_embeddings'),
            ]

            results = {}
            import statistics
            for pretty, attr in algs:
                mat = None
                try:
                    mod = getattr(comp, attr, None)
                    if mod is None:
                        # try to load module from file if not an attribute
                        mod_path = os.path.join('src', 'r2 - bibliometria', f'{attr}.py')
                        if os.path.exists(mod_path):
                            mod = load_module_from_path(mod_path, name=f'r2_{attr}')
                    if mod is None or not hasattr(mod, 'compare_texts'):
                        results[pretty] = {'skipped': 'module not available'}
                        continue
                    mat = mod.compare_texts(texts)
                    # compute summary
                    flat = []
                    n = len(mat)
                    for i in range(n):
                        for j in range(i + 1, n):
                            try:
                                flat.append(float(mat[i][j]))
                            except Exception:
                                pass
                    summary = {'n': n}
                    if flat:
                        summary['avg_pairwise'] = statistics.mean(flat)
                        summary['median_pairwise'] = statistics.median(flat)
                        summary['top_5'] = sorted(flat, reverse=True)[:5]
                    else:
                        summary['avg_pairwise'] = None
                        summary['top_5'] = []
                    # serialize matrix
                    matrix_list = []
                    for row in mat:
                        matrix_list.append([float(x) for x in row])
                    results[pretty] = {'status': 'ok', 'summary': summary, 'matrix': matrix_list}
                except Exception as e:
                    results[pretty] = {'error': str(e)}

            return jsonify({'status': 'ok', 'bib': bib_path, 'n_entries': len(entries), 'selected_indices': chosen, 'labels': labels, 'results': results})

    # Fallback: run per-module compare_texts on a selection of abstracts (legacy supports a,b via GET;
    # POST supports 'indices' list or 'all' but key-based selection requires compare_abstracts loader).
    # ensure we have plain abstracts for fallback
    abstracts = extract_abstracts(bib_path, limit=limit)

    # determine chosen indices for fallback (GET supports a/b, POST supports 'indices' or 'all')
    chosen = []
    if request.method == 'POST':
        if data.get('all') in (True, 'true', '1'):
            chosen = list(range(len(abstracts)))
        elif isinstance(data.get('indices'), list):
            for v in data.get('indices'):
                try:
                    iv = int(v)
                except Exception:
                    continue
                chosen.append(iv)
        else:
            # fallback to first two
            chosen = [0, 1]
    else:
        a_idx = request.args.get('a')
        b_idx = request.args.get('b')
        if a_idx is None and b_idx is None:
            chosen = [0, 1]
        else:
            try:
                a = int(a_idx) if a_idx is not None else 0
                b = int(b_idx) if b_idx is not None else (a + 1)
            except Exception:
                return jsonify({'error': "Invalid article indices 'a' and 'b' (must be integers)."}), 400
            chosen = [a, b]

    # validate and dedupe chosen
    clean_chosen = []
    seen = set()
    for c in chosen:
        try:
            ci = int(c)
        except Exception:
            continue
        if 0 <= ci < len(abstracts) and ci not in seen:
            seen.add(ci)
            clean_chosen.append(ci)
    chosen = clean_chosen
    if not chosen:
        return jsonify({'error': 'No valid selections provided', 'n_available': len(abstracts)}), 400

    docs_to_compare = [abstracts[i] for i in chosen]
    folder = os.path.join('src', 'r2 - bibliometria')
    if not os.path.exists(folder):
        return jsonify({'error': 'folder not found', 'path': folder}), 404
    results = {}
    for fname in sorted(os.listdir(folder)):
        if not fname.endswith('.py'):
            continue
        path = os.path.join(folder, fname)
        try:
            mod = load_module_from_path(path, name=f'r2_{os.path.splitext(fname)[0]}')
        except Exception as e:
            results[fname] = {'error': str(e)}
            continue
        if hasattr(mod, 'compare_texts'):
            try:
                mat = mod.compare_texts(docs_to_compare)
                flat = []
                n = len(mat)
                for i in range(n):
                    for j in range(i + 1, n):
                        try:
                            flat.append(float(mat[i][j]))
                        except Exception:
                            pass
                summary = {'n': n}
                if flat:
                    import statistics
                    summary['avg_pairwise'] = statistics.mean(flat)
                    summary['median_pairwise'] = statistics.median(flat)
                    summary['top_5'] = sorted(flat, reverse=True)[:5]
                else:
                    summary['avg_pairwise'] = None
                    summary['top_5'] = []
                # serialize matrix to lists for JSON transport
                try:
                    matrix_list = [list(map(float, row)) for row in mat]
                except Exception:
                    # fallback: try to convert via nested iteration
                    matrix_list = []
                    for row in mat:
                        matrix_list.append([float(x) for x in row])
                results[fname] = {'status': 'ok', 'summary': summary, 'matrix': matrix_list}
            except Exception as e:
                results[fname] = {'error': str(e)}
        else:
            results[fname] = {'skipped': 'no compare_texts'}
    return jsonify({'bib': bib_path, 'n_abstracts_used': len(abstracts), 'selected_indices': chosen, 'results': results})


@app.route('/run/r3', methods=['POST'])
def run_r3():
    """Run the r3 frequency analysis pipeline (src/r3 - frecuencia/analyze_frequency.py).

    JSON body (optional): {
      "bib": "path/to/unificado.bib",
      "seeds": "path/to/seeds.txt",
      "max_new": 15,
      "out": "output/dir"
    }
    """
    data = request.get_json(silent=True) or {}
    bib_path = data.get('bib', 'descargas/unificado.bib')
    seeds_path = data.get('seeds')
    out_dir = data.get('out', os.path.join('src', 'r3 - frecuencia', 'files'))
    try:
        max_new = int(data.get('max_new', 15))
    except Exception:
        max_new = 15

    script_path = os.path.join('src', 'r3 - frecuencia', 'analyze_frequency.py')
    if not os.path.exists(script_path):
        return jsonify({'error': 'r3 script not found', 'path': script_path}), 404

    try:
        mod = load_module_from_path(script_path, name='r3_frequency')
    except Exception as e:
        return jsonify({'error': f'failed to load r3 script: {e}'}), 500

    # read documents
    try:
        docs = mod.read_bib_abstracts(bib_path)
    except Exception as e:
        return jsonify({'error': f'failed to read .bib: {e}'}), 500

    # load seeds
    seeds = []
    # support multiple seed categories stored in a dedicated folder
    seeds_dir = os.path.join('src', 'r3 - frecuencia', 'seeds')
    default_seed_file = os.path.join('src', 'r3 - frecuencia', 'seeds_example.txt')

    # helper to safely read a seeds file under seeds_dir or an explicit path
    def _read_seed_file(path):
        try:
            with open(path, encoding='utf-8') as fh:
                return [line.strip() for line in fh if line.strip()]
        except Exception:
            return []

    # Priority: explicit 'seed_categories' param (comma separated names), then explicit 'seeds' path, then default builtin
    seed_cats_param = None
    if isinstance(data.get('seed_categories'), list):
        # client might POST JSON with list
        seed_cats_param = data.get('seed_categories')
    else:
        seed_cats_param = data.get('seed_categories')

    if seed_cats_param:
        # normalize to list
        if isinstance(seed_cats_param, str):
            parts = [p.strip() for p in seed_cats_param.split(',') if p.strip()]
        elif isinstance(seed_cats_param, list):
            parts = [str(p).strip() for p in seed_cats_param if str(p).strip()]
        else:
            parts = []

        # ensure seeds_dir exists
        try:
            os.makedirs(seeds_dir, exist_ok=True)
        except Exception:
            pass

        # special keyword 'all' loads all files in seeds_dir
        if len(parts) == 1 and parts[0].lower() == 'all':
            try:
                files = sorted([f for f in os.listdir(seeds_dir) if f.endswith('.txt')])
            except Exception:
                files = []
            for fname in files:
                full = os.path.join(seeds_dir, fname)
                seeds += _read_seed_file(full)
        else:
            for cat in parts:
                fname = cat if cat.endswith('.txt') else f"{cat}.txt"
                full = os.path.join(seeds_dir, fname)
                # if not found in seeds_dir, also try an explicit path provided by client
                if os.path.exists(full):
                    seeds += _read_seed_file(full)
                elif os.path.exists(cat):
                    seeds += _read_seed_file(cat)

        # dedupe while preserving order
        seen = set()
        uniq = []
        for s in seeds:
            if s not in seen:
                seen.add(s)
                uniq.append(s)
        seeds = uniq
    elif seeds_path and os.path.exists(seeds_path):
        try:
            with open(seeds_path, encoding='utf-8') as fh:
                seeds = [line.strip() for line in fh if line.strip()]
        except Exception as e:
            return jsonify({'error': f'failed to read seeds file: {e}'}), 500
    else:
        # same default used by the script
        if os.path.exists(default_seed_file):
            seeds = _read_seed_file(default_seed_file)
        else:
            seeds = [
                "generative", "generative ai", "generative artificial intelligence",
                "chatgpt", "large language model", "llm", "gpt",
                "prompt engineering", "ai-assisted", "ai", "education", "teaching", "learning"
            ]

    # ensure output dir
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception as e:
        return jsonify({'error': f'failed to create out dir: {e}'}), 500

    # count seeds
    try:
        seed_counts, doc_has_seed = mod.count_seed_occurrences(docs, seeds)
    except Exception as e:
        return jsonify({'error': f'failed counting seeds: {e}'}), 500

    # discover candidates
    try:
        candidates = mod.discover_candidates(docs, seeds, max_new=max_new)
    except Exception as e:
        return jsonify({'error': f'failed to discover candidates: {e}'}), 500

    # compute candidate stats
    try:
        rows = mod.compute_candidate_stats(docs, candidates, doc_has_seed)
    except Exception as e:
        return jsonify({'error': f'failed to compute candidate stats: {e}'}), 500

    # save outputs
    seeds_csv = os.path.join(out_dir, 'seeds_frequency.csv')
    candidates_csv = os.path.join(out_dir, 'candidates_frequency.csv')
    try:
        mod.save_csv_seed_counts(seed_counts, seeds_csv)
        mod.save_csv_candidates(rows, candidates_csv)
    except Exception as e:
        return jsonify({'error': f'failed to save csv outputs: {e}'}), 500

    # prepare small summary
    seed_list = sorted([(k, v) for k, v in seed_counts.items()], key=lambda x: x[1], reverse=True)
    return jsonify({
        'status': 'ok',
        'bib': bib_path,
        'n_docs': len(docs),
        'seeds_used': seeds,
        'seed_counts': [{'seed': k, 'count': v} for k, v in seed_list],
        'candidates': candidates,
        'candidate_stats': rows,
        'out_files': {'seeds_csv': seeds_csv, 'candidates_csv': candidates_csv}
    })


@app.route('/articles', methods=['GET'])
def list_articles():
    """List articles (titles/metadata) from a .bib file.

    Query params:
      - bib: path to .bib (default: descargas/unificado.bib)
      - limit: optional max number of articles to list
    """
    bib_path = request.args.get('bib', 'descargas/unificado.bib')
    try:
        limit = request.args.get('limit')
        limit = int(limit) if limit is not None else None
    except Exception:
        return jsonify({'error': "Invalid 'limit' parameter (must be integer)."}), 400
    items = list_bib_articles(bib_path, limit=limit)
    return jsonify({'bib': bib_path, 'n_available': len(items), 'articles': items})


@app.route('/seeds', methods=['GET'])
def list_seed_categories():
    """List available seed categories (filenames without .txt) found under src/r3 - frecuencia/seeds/.

    Also includes the default `seeds_example.txt` as 'default' if present.
    """
    seeds_dir = os.path.join('src', 'r3 - frecuencia', 'seeds')
    default_seed_file = os.path.join('src', 'r3 - frecuencia', 'seeds_example.txt')
    cats = []
    try:
        if os.path.exists(seeds_dir):
            for f in sorted(os.listdir(seeds_dir)):
                if f.endswith('.txt'):
                    cats.append(os.path.splitext(f)[0])
    except Exception:
        cats = []
    if os.path.exists(default_seed_file):
        if 'default' not in cats:
            cats.insert(0, 'default')
    return jsonify({'status': 'ok', 'seed_categories': cats})


@app.route('/download/unificado', methods=['GET'])
def download_unificado():
    """Download the unified .bib file (descargas/unificado.bib) as attachment."""
    path = os.path.join('descargas', 'unificado.bib')
    if not os.path.exists(path):
        return jsonify({'error': 'file not found', 'path': path}), 404
    try:
        # Flask 2.0+ supports download_name
        return send_file(path, as_attachment=True, download_name='unificado.bib', mimetype='text/plain')
    except TypeError:
        # older Flask versions
        return send_file(path, as_attachment=True, attachment_filename='unificado.bib', mimetype='text/plain')


@app.route('/download/repetidos', methods=['GET'])
def download_repetidos():
    """Download the duplicates .bib file (descargas/repetidos.bib) as attachment."""
    path = os.path.join('descargas', 'repetidos.bib')
    if not os.path.exists(path):
        return jsonify({'error': 'file not found', 'path': path}), 404
    try:
        return send_file(path, as_attachment=True, download_name='repetidos.bib', mimetype='text/plain')
    except TypeError:
        return send_file(path, as_attachment=True, attachment_filename='repetidos.bib', mimetype='text/plain')


@app.route('/seeds', methods=['POST'])
def upload_seeds():
    """Accept a JSON body with 'seeds': ["word1", "word2", ...] and optionally 'save_to' path.

    Writes the seeds (one per line) to the given path or the default seeds file used by r3.
    Returns the path written and the number of seeds.
    """
    data = request.get_json(silent=True)
    if not data or 'seeds' not in data:
        return jsonify({'error': "Request must be JSON with a 'seeds' array."}), 400
    seeds = data.get('seeds')
    if not isinstance(seeds, list) or not all(isinstance(s, str) for s in seeds):
        return jsonify({'error': "'seeds' must be an array of strings."}), 400
    # support optional category parameter to save categorized seed files under seeds_dir
    category = data.get('category')
    seeds_dir = os.path.join('src', 'r3 - frecuencia', 'seeds')
    default_seed_file = os.path.join('src', 'r3 - frecuencia', 'seeds_example.txt')

    if category:
        # sanitize simple category name (no path traversal)
        cat_name = os.path.basename(category)
        if not cat_name:
            return jsonify({'error': 'invalid category name'}), 400
        save_to = os.path.join(seeds_dir, f"{cat_name}.txt")
    else:
        save_to = data.get('save_to') or default_seed_file

    # ensure output dir exists
    try:
        os.makedirs(os.path.dirname(save_to), exist_ok=True)
        with open(save_to, 'w', encoding='utf-8') as fh:
            for s in seeds:
                fh.write(s.strip() + '\n')
    except Exception as e:
        return jsonify({'error': f'failed to write seeds file: {e}'}), 500
    return jsonify({'status': 'ok', 'n_seeds': len(seeds), 'path': save_to, 'category': category})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)