# tfidf_index.py
"""
Robust TF-IDF index for demo-size dataset.
Rebuilds vectorizer safely when items are added. Uses cosine similarity for ranking.
"""

import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_lock = threading.Lock()
vectorizer = None
tfidf_matrix = None
resources_cache = []   # store SQLAlchemy resource objects

def _texts_from_resources(resources):
    texts = []
    for r in resources:
        title = getattr(r, "title", "") or ""
        desc  = getattr(r, "description", "") or ""
        tags  = getattr(r, "tags", "") or ""
        texts.append(f"{title} {desc} {tags}")
    return texts

def build_index(resources):
    """Full rebuild of TF-IDF from a resource list."""
    global vectorizer, tfidf_matrix, resources_cache
    with _lock:
        resources_cache = list(resources)
        texts = _texts_from_resources(resources_cache)
        if not texts:
            vectorizer = None
            tfidf_matrix = None
            return
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(texts)

def update_index(new_resource, all_resources=None):
    """
    Update the index after adding a new resource.
    If all_resources is provided, rebuild from that list (safer).
    """
    global vectorizer, tfidf_matrix, resources_cache
    with _lock:
        if all_resources is not None:
            build_index(all_resources)
            return
        if vectorizer is None or tfidf_matrix is None:
            build_index([new_resource])
            return
        # append and rebuild (rebuilding keeps vocab consistent)
        resources_cache.append(new_resource)
        texts = _texts_from_resources(resources_cache)
        v_new = TfidfVectorizer(stop_words='english')
        tfidf_new = v_new.fit_transform(texts)
        vectorizer = v_new
        tfidf_matrix = tfidf_new

def search_index(query, topn=50, type_filter=None):
    """Return list of tuples (resource_obj, score) ordered by score desc."""
    global vectorizer, tfidf_matrix, resources_cache
    if vectorizer is None or tfidf_matrix is None:
        return []
    if not query or not query.strip():
        return []
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    ranked_idx = scores.argsort()[::-1]
    results = []
    for idx in ranked_idx:
        sc = float(scores[idx])
        if sc <= 0:
            continue
        res = resources_cache[idx]
        if type_filter and getattr(res, "type", None) != type_filter:
            continue
        results.append((res, sc))
        if len(results) >= topn:
            break
    return results

# debugging helpers
def index_size():
    return len(resources_cache)

def vocab_sample(n=10):
    if vectorizer is None:
        return {}
    items = list(vectorizer.vocabulary_.items())[:n]
    return dict(items)
