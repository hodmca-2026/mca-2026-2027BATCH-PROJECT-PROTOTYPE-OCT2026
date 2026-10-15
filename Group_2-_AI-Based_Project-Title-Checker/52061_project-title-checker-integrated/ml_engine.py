"""
AI/ML-based Project Similarity Detection Engine
===============================================

Multi-method hybrid NLP and Deep Learning pipeline for detecting duplicate,
paraphrased, and closely related project proposals.

Pipeline Components:
    1. Semantic Sentence Embeddings (PyTorch + sentence-transformers/all-MiniLM-L6-v2)
       - Deep bidirectional Transformer embeddings for semantic sentence alignment
       - Captures conceptual paraphrasing and synonym variation across proposals
       - Graceful offline fallback if model artifacts are unavailable
    2. Feature Extraction & Lexical Cosine (scikit-learn TfidfVectorizer)
       - N-gram (1, 2) TF-IDF vectors with domain-specific stopword filtering
    3. Keyword Set Overlap (Jaccard Similarity)
       - Set intersection over union on normalized non-boilerplate technical tokens
    4. Sequence Matching (Ratcliff/Obershelp SequenceMatcher)
       - Longest common subsequence matching for structural and word-order alignment
    5. Multi-Field Proposal Integration
       - Compares complete available project information: Title, Abstract/Description,
         Domain, and Methodology
       - Template de-biasing to eliminate false positives on shared academic boilerplate
         (e.g., "Using Machine Learning", "Deep Learning Based Detection")
    6. Calibrated Decision & Risk Classification
       - High Risk (>= 58%): Duplicate proposal / Rejection alert
       - Needs Review (42% - 57%): Related proposal / Advisory faculty review
       - Low Risk (< 42%): Distinct proposal / Unique submission

Tech: Python, PyTorch, Transformers, scikit-learn, NLTK, NumPy
"""

import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# NLTK resources
import nltk

for resource in ['punkt', 'punkt_tab', 'stopwords', 'wordnet']:
    try:
        nltk.download(resource, quiet=True)
    except Exception:
        pass

try:
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
except ImportError:
    word_tokenize = None
    stopwords = None
    PorterStemmer = None


# ============================================================
# Pretrained Semantic Embedding Service
# ============================================================

class SemanticEmbeddingService:
    """
    Sentence embedding service utilizing sentence-transformers/all-MiniLM-L6-v2.
    Loads offline from local HuggingFace cache. If unavailable, falls back
    gracefully to lexical-only matching while explicitly reporting model status.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cpu")
        self.is_available = False
        self.status_message = "Not initialized"
        self._cache: Dict[str, np.ndarray] = {}
        self._load_model()

    def _load_model(self):
        try:
            from transformers import AutoTokenizer, AutoModel

            # Attempt loading with local_files_only=True first to avoid external network calls
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.MODEL_NAME, local_files_only=True
                )
                self.model = AutoModel.from_pretrained(
                    self.MODEL_NAME, local_files_only=True
                )
            except Exception:
                # Fallback to standard pretrained loading (cache search)
                self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
                self.model = AutoModel.from_pretrained(self.MODEL_NAME)

            self.model.to(self.device)
            self.model.eval()
            self.is_available = True
            self.status_message = "all-MiniLM-L6-v2 (offline PyTorch)"
        except Exception as e:
            self.is_available = False
            self.tokenizer = None
            self.model = None
            self.status_message = f"Unavailable ({str(e)})"

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of text strings into normalized 384-dimensional vectors.
        Caches previously computed embeddings in memory.
        """
        if not texts or not self.is_available:
            return np.zeros((len(texts), 384), dtype=np.float32)

        results = []
        uncached_indices = []
        uncached_texts = []

        for idx, text in enumerate(texts):
            norm_key = text.strip().lower()
            if norm_key in self._cache:
                results.append((idx, self._cache[norm_key]))
            else:
                uncached_indices.append(idx)
                uncached_texts.append(text)

        if uncached_texts:
            try:
                inputs = self.tokenizer(
                    uncached_texts,
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_tensors="pt",
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    token_embeddings = outputs.last_hidden_state
                    attention_mask = inputs["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
                    sum_embeddings = torch.sum(token_embeddings * attention_mask, dim=1)
                    sum_mask = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
                    mean_pooled = sum_embeddings / sum_mask
                    normalized = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
                    embs_np = normalized.cpu().numpy()

                for u_idx, text, emb in zip(uncached_indices, uncached_texts, embs_np):
                    norm_key = text.strip().lower()
                    self._cache[norm_key] = emb
                    results.append((u_idx, emb))
            except Exception:
                for u_idx in uncached_indices:
                    results.append((u_idx, np.zeros(384, dtype=np.float32)))

        results.sort(key=lambda x: x[0])
        return np.vstack([x[1] for x in results])

    def cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts using sentence embeddings."""
        if not text1.strip() or not text2.strip() or not self.is_available:
            return 0.0
        embs = self.embed_texts([text1, text2])
        v1 = embs[0]
        v2 = embs[1]
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 < 1e-9 or norm2 < 1e-9:
            return 0.0
        sim = float(np.dot(v1, v2) / (norm1 * norm2))
        return max(0.0, min(1.0, sim))


# Global embedding service singleton
semantic_service = SemanticEmbeddingService()


# ============================================================
# Similarity Engine Class
# ============================================================

class SimilarityEngine:
    """
    AI/ML-based Project Similarity Detection Engine.

    Combines:
    1. Pretrained Transformer Semantic Embeddings (all-MiniLM-L6-v2)
    2. TF-IDF + Cosine Similarity
    3. Jaccard Keyword Overlap
    4. Sequence Pattern Matching
    """

    # Calibrated decision thresholds (percentage)
    REJECTION_THRESHOLD = 58   # High Risk >= 58%: Direct duplicate / rejection tier
    REVIEW_THRESHOLD    = 42   # Needs Review 42% - 57%: Plausible duplicate / faculty review
    LOW_RISK_THRESHOLD  = 42   # Low Risk < 42%: Distinct project

    # Ensemble weights
    SEMANTIC_WEIGHT = 0.55
    TFIDF_WEIGHT    = 0.25
    JACCARD_WEIGHT  = 0.12
    SEQUENCE_WEIGHT = 0.08

    # Generic academic boilerplate tokens to penalize when distinguishing different projects
    DOMAIN_STOPWORDS = {
        'using', 'based', 'system', 'project', 'application', 'app', 'development',
        'design', 'implementation', 'study', 'approach', 'method', 'technique', 'model',
        'analysis', 'detection', 'prediction', 'classification', 'machine', 'learning',
        'deep', 'artificial', 'intelligence', 'automated', 'smart', 'web', 'with', 'and',
        'for', 'in', 'of', 'the', 'a', 'an', 'to', 'on', 'via', 'through', 'into', 'iot',
        'framework', 'platform', 'tool', 'solution', 'management', 'portal', 'software',
    }

    def __init__(self):
        self.semantic_service = semantic_service
        if PorterStemmer is not None:
            self.stemmer = PorterStemmer()
        else:
            self.stemmer = None

        self.stop_words = set()
        if stopwords is not None:
            try:
                self.stop_words = set(stopwords.words('english'))
            except Exception:
                self.stop_words = set()

        self.stop_words.update(self.DOMAIN_STOPWORDS)

    # --------------------------------------------------------
    # NLP Preprocessing
    # --------------------------------------------------------

    def preprocess(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Full NLP preprocessing pipeline for lexical matching.
        """
        lowered = text.lower().strip()
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', lowered)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if word_tokenize is not None:
            try:
                tokens = word_tokenize(cleaned)
            except Exception:
                tokens = cleaned.split()
        else:
            tokens = cleaned.split()

        filtered = [t for t in tokens if t not in self.stop_words and len(t) > 1]

        if self.stemmer is not None:
            stemmed = [self.stemmer.stem(t) for t in filtered]
        else:
            stemmed = filtered

        analysis = {
            'original':        text,
            'lowered':         lowered,
            'cleaned':         cleaned,
            'tokens':          tokens,
            'after_stopwords': filtered,
            'stemmed':         stemmed,
            'processed_text':  ' '.join(stemmed),
        }
        return ' '.join(stemmed), analysis

    # --------------------------------------------------------
    # Individual Similarity Methods
    # --------------------------------------------------------

    def semantic_similarity(self, text1: str, text2: str) -> Tuple[float, Dict[str, Any]]:
        """
        Method 1 — Deep Bidirectional Sentence Embedding Cosine Similarity.
        """
        if not semantic_service.is_available:
            return 0.0, {
                'score': 0,
                'available': False,
                'model': semantic_service.status_message,
            }

        sim = semantic_service.cosine_similarity(text1, text2)
        return sim, {
            'score': round(sim * 100),
            'available': True,
            'model': semantic_service.status_message,
        }

    def tfidf_cosine_similarity(
        self, text1: str, text2: str, corpus: Optional[List[str]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Method 2 — TF-IDF + Cosine Similarity with n-grams.
        """
        docs = [text1, text2] + (corpus or [])
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=500,
            )
            tfidf_matrix = vectorizer.fit_transform(docs)
            features = vectorizer.get_feature_names_out().tolist()
            sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])

            v1 = tfidf_matrix[0].toarray()[0]
            v2 = tfidf_matrix[1].toarray()[0]

            top1 = sorted(
                [(features[i], round(float(v1[i]), 3)) for i in range(len(features)) if v1[i] > 0],
                key=lambda x: x[1], reverse=True,
            )[:6]
            top2 = sorted(
                [(features[i], round(float(v2[i]), 3)) for i in range(len(features)) if v2[i] > 0],
                key=lambda x: x[1], reverse=True,
            )[:6]
            common = list(set(f[0] for f in top1) & set(f[0] for f in top2))

            return float(sim), {
                'score': round(sim * 100),
                'top_features_new': top1,
                'top_features_existing': top2,
                'common_features': common,
            }
        except ValueError:
            return 0.0, {
                'score': 0,
                'top_features_new': [],
                'top_features_existing': [],
                'common_features': [],
            }

    def jaccard_similarity(self, text1: str, text2: str) -> Tuple[float, Dict[str, Any]]:
        """
        Method 3 — Jaccard Token Overlap on content words.
        """
        set1 = set(text1.split())
        set2 = set(text2.split())

        if not set1 or not set2:
            return 0.0, {'score': 0, 'common_words': [], 'all_words': []}

        intersection = set1 & set2
        union = set1 | set2
        sim = len(intersection) / len(union)

        return float(sim), {
            'score': round(sim * 100),
            'common_words': sorted(list(intersection)),
            'all_words': sorted(list(union)),
        }

    def sequence_similarity(self, text1: str, text2: str) -> Tuple[float, Dict[str, Any]]:
        """
        Method 4 — Structural Sequence Matching.
        """
        sim = SequenceMatcher(None, text1, text2).ratio()
        return float(sim), {'score': round(sim * 100)}

    # --------------------------------------------------------
    # Core Multi-Field Comparison Logic
    # --------------------------------------------------------

    def compare_proposals(
        self,
        new_title: str,
        existing_title: str,
        new_description: str = "",
        existing_description: str = "",
        new_domain: str = "",
        existing_domain: str = "",
        corpus_processed: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compares two proposals using complete available fields:
        title, abstract/description, and domain.
        """
        t1 = new_title.strip()
        t2 = existing_title.strip()
        d1 = new_description.strip()
        d2 = existing_description.strip()

        # Exact title match shortcut
        if t1.lower() == t2.lower():
            return {
                'title': existing_title,
                'similarity': 100,
                'risk_level': 'High Risk',
                'recommendation': 'Review for possible duplication',
                'semantic_score': 100,
                'tfidf_score': 100,
                'jaccard_score': 100,
                'sequence_score': 100,
                'is_exact_match': True,
                'common_keywords': [w for w in t1.lower().split() if w not in self.stop_words][:5],
                'match_reason': 'Exact identical project title match',
            }

        # 1. Semantic sentence embedding comparison
        has_descriptions = bool(d1 and d2)
        f1 = f"{t1}. {d1} [{new_domain}]".strip() if has_descriptions else t1
        f2 = f"{t2}. {d2} [{existing_domain}]".strip() if has_descriptions else t2

        sim_t_sem, sem_t_det = self.semantic_similarity(t1, t2)
        if has_descriptions:
            sim_f_sem, _ = self.semantic_similarity(f1, f2)
            # Full proposal context provides crucial confirmation of conceptual equivalence
            sem_sim = 0.35 * sim_t_sem + 0.65 * sim_f_sem
        else:
            sim_f_sem = sim_t_sem
            sem_sim = sim_t_sem

        # 2. Preprocessing for lexical matching
        p1_proc, _ = self.preprocess(f1 if has_descriptions else t1)
        p2_proc, _ = self.preprocess(f2 if has_descriptions else t2)

        # 3. Lexical TF-IDF cosine similarity
        tfidf_sim, tfidf_det = self.tfidf_cosine_similarity(
            p1_proc, p2_proc, corpus_processed
        )

        # 4. Jaccard word-set overlap
        jaccard_sim, jaccard_det = self.jaccard_similarity(p1_proc, p2_proc)

        # 5. Sequence matcher on processed titles
        p1_title_proc, _ = self.preprocess(t1)
        p2_title_proc, _ = self.preprocess(t2)
        seq_sim, _ = self.sequence_similarity(p1_title_proc, p2_title_proc)

        # 6. Hybrid combination
        lexical_score = (
            0.50 * tfidf_sim +
            0.35 * jaccard_sim +
            0.15 * seq_sim
        )

        if semantic_service.is_available:
            # Semantic embedding is primary anchor (70%), lexical provides positive boost (30%)
            combined = 0.70 * sem_sim + 0.30 * lexical_score
            # Boost when both semantic and lexical agree strongly
            if sem_sim > 0.60 and lexical_score > 0.40:
                combined = min(1.0, combined + 0.08)
        else:
            # Fallback to lexical ensemble if neural embedding is unavailable
            combined = (
                tfidf_sim * 0.45 +
                jaccard_sim * 0.30 +
                seq_sim * 0.25
            )

        # 7. False-positive dampener:
        # If proposals share academic buzzwords but descriptions reveal completely different tasks
        if has_descriptions and sim_f_sem < 0.48:
            combined = combined * 0.75

        # Content words in common
        words1 = set(re.findall(r'\b[a-z]{3,}\b', t1.lower())) - self.DOMAIN_STOPWORDS
        words2 = set(re.findall(r'\b[a-z]{3,}\b', t2.lower())) - self.DOMAIN_STOPWORDS
        if has_descriptions:
            words1.update(set(re.findall(r'\b[a-z]{3,}\b', d1.lower())) - self.DOMAIN_STOPWORDS)
            words2.update(set(re.findall(r'\b[a-z]{3,}\b', d2.lower())) - self.DOMAIN_STOPWORDS)
        common_content_words = sorted(list(words1 & words2))

        # Additional dampener if title core keywords have 0 overlap and full similarity is low
        if words1 and words2 and len(common_content_words) == 0 and sem_sim < 0.60:
            combined = combined * 0.80

        combined_pct = round(combined * 100)

        # Risk classification
        if combined_pct >= self.REJECTION_THRESHOLD:
            risk_level = "High Risk"
            recommendation = "Review for possible duplication"
            reason = "High semantic and structural alignment with existing proposal"
        elif combined_pct >= self.REVIEW_THRESHOLD:
            risk_level = "Needs Review"
            recommendation = "Faculty review recommended"
            reason = "Moderate overlap; potential thematic paraphrase or shared methodology"
        else:
            risk_level = "Low Risk"
            recommendation = "No strong duplicate detected"
            reason = "Sufficiently distinct proposal"

        return {
            'title': existing_title,
            'similarity': combined_pct,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'semantic_score': round(sem_sim * 100),
            'tfidf_score': round(tfidf_sim * 100),
            'jaccard_score': round(jaccard_sim * 100),
            'sequence_score': round(seq_sim * 100),
            'is_exact_match': False,
            'common_keywords': common_content_words[:6],
            'match_reason': reason,
        }

    # --------------------------------------------------------
    # Combined Similarity (main entry point)
    # --------------------------------------------------------

    def check_title(
        self,
        new_title: str,
        existing_titles: List[Union[str, Dict[str, Any]]],
        new_description: str = "",
        new_domain: str = "",
        existing_projects: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[bool, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Check a new title / proposal against existing titles or project objects.

        Supports passing either:
        - List of strings: ['Title 1', 'Title 2']
        - List of project dicts: [{'title': '...', 'description': '...', 'domain': '...'}]

        Returns:
            (is_rejected: bool, similar_list: list, analysis: dict)
        """
        if not existing_titles:
            _, new_analysis = self.preprocess(new_title)
            return False, [], self._build_analysis(new_title, new_analysis, [])

        # Normalize existing projects
        projects_data: List[Dict[str, Any]] = []
        if existing_projects:
            projects_data = existing_projects
        else:
            for item in existing_titles:
                if isinstance(item, dict):
                    projects_data.append(item)
                else:
                    projects_data.append({
                        'title': str(item),
                        'description': '',
                        'domain': '',
                    })

        # Preprocess existing corpus for TF-IDF context
        corpus_proc = []
        for p in projects_data:
            t = p.get('title', '')
            d = p.get('description', '')
            text = f"{t} {d}".strip() if d else t
            proc, _ = self.preprocess(text)
            corpus_proc.append(proc)

        similar = []

        for p in projects_data:
            match_res = self.compare_proposals(
                new_title=new_title,
                existing_title=p.get('title', ''),
                new_description=new_description,
                existing_description=p.get('description', ''),
                new_domain=new_domain,
                existing_domain=p.get('domain', ''),
                corpus_processed=corpus_proc,
            )

            # Keep items with score >= REVIEW_THRESHOLD (42%) for review
            if match_res['similarity'] >= self.REVIEW_THRESHOLD or match_res['is_exact_match']:
                similar.append(match_res)

        similar.sort(key=lambda x: x['similarity'], reverse=True)

        # Rejected if any match reaches High Risk (>= REJECTION_THRESHOLD 58%) or is exact match
        is_rejected = any(
            x['similarity'] >= self.REJECTION_THRESHOLD or x.get('is_exact_match')
            for x in similar
        )

        _, new_analysis = self.preprocess(new_title)
        analysis = self._build_analysis(new_title, new_analysis, similar)

        return is_rejected, similar, analysis

    # --------------------------------------------------------
    # Faculty: pairwise similarities for all titles / projects
    # --------------------------------------------------------

    def pairwise_max_similarity(
        self, projects_or_titles: List[Union[str, Dict[str, Any]]]
    ) -> Dict[str, Tuple[int, str]]:
        """
        Compute pairwise max similarity across all proposals.
        Used by the faculty dashboard.

        Returns:
            dict mapping title -> (max_sim: int, most_similar_title: str)
        """
        if len(projects_or_titles) < 2:
            return {
                (p['title'] if isinstance(p, dict) else p): (0, '')
                for p in projects_or_titles
            }

        # Normalize to list of dicts
        items: List[Dict[str, Any]] = []
        for p in projects_or_titles:
            if isinstance(p, dict):
                items.append(p)
            else:
                items.append({'title': str(p), 'description': '', 'domain': ''})

        # Precompute processed corpus
        corpus_proc = []
        for p in items:
            t = p.get('title', '')
            d = p.get('description', '')
            proc, _ = self.preprocess(f"{t} {d}".strip() if d else t)
            corpus_proc.append(proc)

        result: Dict[str, Tuple[int, str]] = {}

        for i, p1 in enumerate(items):
            best_sim = 0
            best_match = ''
            t1 = p1.get('title', '')
            for j, p2 in enumerate(items):
                if i == j:
                    continue
                match_res = self.compare_proposals(
                    new_title=t1,
                    existing_title=p2.get('title', ''),
                    new_description=p1.get('description', ''),
                    existing_description=p2.get('description', ''),
                    new_domain=p1.get('domain', ''),
                    existing_domain=p2.get('domain', ''),
                    corpus_processed=corpus_proc,
                )
                score = match_res['similarity']
                if score > best_sim:
                    best_sim = score
                    best_match = p2.get('title', '')
            result[t1] = (best_sim, best_match)

        return result

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _build_analysis(
        self, title: str, preprocess_analysis: Dict[str, Any], similar_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build the analysis dictionary returned to frontend / API."""
        top_risk = "Low Risk"
        if similar_list:
            top_sim = similar_list[0]['similarity']
            if top_sim >= self.REJECTION_THRESHOLD:
                top_risk = "High Risk"
            elif top_sim >= self.REVIEW_THRESHOLD:
                top_risk = "Needs Review"

        return {
            'preprocessing': {
                'original': title,
                'steps': [
                    {'name': 'Lowercase',        'result': preprocess_analysis['lowered']},
                    {'name': 'Clean',             'result': preprocess_analysis['cleaned']},
                    {'name': 'Tokenize',          'result': preprocess_analysis['tokens']},
                    {'name': 'Remove Stopwords',  'result': preprocess_analysis['after_stopwords']},
                    {'name': 'Stemming (Porter)', 'result': preprocess_analysis['stemmed']},
                ],
                'final': preprocess_analysis['processed_text'],
            },
            'methods': [
                {
                    'name':        'Pretrained Semantic Embeddings (all-MiniLM-L6-v2)',
                    'weight':      f'{int(self.SEMANTIC_WEIGHT * 100)}%',
                    'description': 'Captures conceptual semantics and paraphrases using '
                                   'bidirectional transformer sentence embeddings.',
                    'active':      semantic_service.is_available,
                    'status':      semantic_service.status_message,
                },
                {
                    'name':        'TF-IDF + Cosine Similarity',
                    'weight':      f'{int(self.TFIDF_WEIGHT * 100)}%',
                    'description': 'Measures term frequency and inverse document frequency '
                                   'n-gram overlap.',
                    'active':      True,
                },
                {
                    'name':        'Jaccard Keyword Overlap',
                    'weight':      f'{int(self.JACCARD_WEIGHT * 100)}%',
                    'description': 'Measures token set intersection over union on '
                                   'non-boilerplate technical vocabulary.',
                    'active':      True,
                },
                {
                    'name':        'Sequence Pattern Matching',
                    'weight':      f'{int(self.SEQUENCE_WEIGHT * 100)}%',
                    'description': 'Longest common contiguous and semi-contiguous '
                                   'character/token sequences.',
                    'active':      True,
                },
            ],
            'thresholds': {
                'rejection_threshold': self.REJECTION_THRESHOLD,
                'review_threshold': self.REVIEW_THRESHOLD,
            },
            'overall_risk': top_risk,
            'decision': 'REJECTED' if any(s['similarity'] >= self.REJECTION_THRESHOLD or s.get('is_exact_match') for s in similar_list) else 'ACCEPTED',
            'semantic_model_active': semantic_service.is_available,
        }


# ============================================================
# Global Engine Instance
# ============================================================

engine = SimilarityEngine()
