"""查询展开与重排工具。

本地 RAG 服务与线上 agentic-rag 保持同一套检索偏好：
1. 对用户 query 做意图词展开
2. 将查询词用于向量/数据库召回
3. 对召回结果按标题、分类、作者等字段做轻量重排
"""

from __future__ import annotations

import math
import re
from typing import Any, Iterable, List, Sequence


CATEGORY_ALIASES = {
    "健康": ["健康", "养生", "医疗", "免疫力", "中老年", "老人", "长辈", "保健"],
    "科普": ["科普", "科学", "知识", "百科"],
    "历史": ["历史", "党史", "地方史", "人物传记", "地方文化", "革命", "传记"],
    "计算机": ["计算机", "编程", "算法", "人工智能", "软件", "开发", "python", "java", "javascript"],
    "教育": ["教育", "教材", "教辅", "学习"],
    "文学": ["文学", "小说", "散文", "诗歌"],
    "旅游": ["旅游", "旅行", "城市", "地理"],
    "心理学": ["心理", "情绪", "心态", "心理学"],
    "政治": ["政治", "法律", "社会"],
    "经济": ["经济", "管理", "商业"],
    "哲学": ["哲学", "思想", "伦理"],
    "艺术": ["艺术", "美术", "设计", "摄影", "音乐"],
    "少儿": ["少儿", "儿童", "绘本", "亲子"],
    "金融": ["金融", "投资", "理财", "财务"],
    "成长": ["职场", "沟通", "演讲", "写作", "思维"],
    "棋牌": ["围棋", "象棋", "国际象棋", "五子棋"],
}

GENERIC_STOPWORDS = {
    "推荐",
    "书",
    "书籍",
    "书单",
    "适合",
    "相关",
    "一些",
    "一个",
    "一本",
    "给我",
    "来",
    "看看",
    "可以",
    "想要",
    "希望",
    "关于",
    "比较",
    "家里",
    "家人",
    "最好",
    "请",
    "帮我",
    "有哪些",
    "哪些",
}

SEARCH_INTENT_RULES = [
    {
        "terms": ["健康", "养生", "医疗", "免疫力", "中老年", "老人", "长辈", "保健", "科普"],
        "triggers": ["健康", "养生", "医疗", "免疫力", "中老年", "老人", "长辈", "保健"],
    },
    {"terms": ["科普", "科学", "知识", "百科"], "triggers": ["科普", "科学", "知识", "百科"]},
    {"terms": ["历史", "传记", "人物", "鲁迅"], "triggers": ["历史", "传记", "人物", "鲁迅"]},
    {"terms": ["旅游", "旅行", "城市", "文化", "人文", "地理"], "triggers": ["旅游", "旅行", "景点", "城市", "人文", "文化"]},
    {"terms": ["心理", "情绪", "心态", "心理学"], "triggers": ["心理", "情绪", "心态", "心理学"]},
    {"terms": ["职场", "沟通", "演讲", "写作", "思维"], "triggers": ["职场", "沟通", "演讲", "写作", "思维"]},
    {"terms": ["儿童", "少儿", "绘本", "亲子"], "triggers": ["儿童", "少儿", "绘本", "亲子"]},
    {"terms": ["象棋", "残局", "布局", "开局", "中局", "实战"], "triggers": ["象棋"]},
    {"terms": ["围棋", "定式", "死活", "布局", "实战"], "triggers": ["围棋"]},
    {"terms": ["国际象棋", "开局", "中局", "残局", "实战"], "triggers": ["国际象棋"]},
    {"terms": ["五子棋", "布局", "实战", "开局"], "triggers": ["五子棋"]},
]


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def unique(values: Iterable[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        if not value:
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def collect_intent_terms(normalized_query: str) -> List[str]:
    terms: List[str] = []
    for rule in SEARCH_INTENT_RULES:
        if any(trigger in normalized_query for trigger in rule["triggers"]):
            terms.extend(term.lower() for term in rule["terms"])
    return unique(terms)


def extract_terms(query: str) -> List[str]:
    normalized = normalize_text(query)
    if not normalized:
        return []

    raw_terms = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z0-9]{2,}", normalized)
    terms = [term.strip().lower() for term in raw_terms if term.strip() and term.strip() not in GENERIC_STOPWORDS]
    terms.extend(collect_intent_terms(normalized))
    return unique(terms)


def build_catalog_search_terms(query: str) -> List[str]:
    normalized = normalize_text(query)
    if not normalized:
        return []

    intent_terms = collect_intent_terms(normalized)
    if intent_terms:
        return intent_terms

    fallback_terms = extract_terms(query)
    return fallback_terms[:8]


def build_catalog_search_query(query: str) -> str:
    terms = build_catalog_search_terms(query)
    return " ".join(terms) if terms else normalize_text(query)


def _get_value(book: Any, key: str, default: Any = "") -> Any:
    if isinstance(book, dict):
        return book.get(key, default)
    return getattr(book, key, default)


def _set_value(book: Any, key: str, value: Any) -> None:
    if isinstance(book, dict):
        book[key] = value
    else:
        setattr(book, key, value)


def _contains_any(haystack: str, terms: Sequence[str]) -> bool:
    return any(term and term in haystack for term in terms)


def _match_categories(book: Any, normalized_query: str) -> List[str]:
    category = normalize_text(_get_value(book, "category", ""))
    title = normalize_text(_get_value(book, "title", ""))
    hits: List[str] = []

    for label, aliases in CATEGORY_ALIASES.items():
        matched = any(alias in normalized_query for alias in aliases)
        if not matched:
            continue
        if label.lower() == category or any(alias in category for alias in aliases):
            hits.append(label)
            continue
        if any(alias in title for alias in aliases):
            hits.append(label)

    return unique(hits)


def _match_count(haystack: str, terms: Sequence[str]) -> int:
    return sum(1 for term in terms if term and term in haystack)


def _compute_score(book: Any, query: str, index: int) -> float:
    normalized_query = normalize_text(query)
    query_terms = extract_terms(query)

    title = normalize_text(_get_value(book, "title", ""))
    author = normalize_text(_get_value(book, "author", ""))
    publisher = normalize_text(_get_value(book, "publisher", ""))
    category = normalize_text(_get_value(book, "category", ""))
    summary = normalize_text(_get_value(book, "summary", _get_value(book, "description", "")))
    semantic_description = normalize_text(_get_value(book, "semantic_description", ""))
    haystack = " ".join([title, author, publisher, category, summary, semantic_description]).strip()
    relevance = float(_get_value(book, "relevance_score", _get_value(book, "score", 0)) or 0)

    if not normalized_query or not query_terms:
        return relevance

    score = math.log1p(max(0.0, relevance)) * 0.35

    title_hits = _match_count(title, query_terms)
    author_hits = _match_count(author, query_terms)
    publisher_hits = _match_count(publisher, query_terms)
    category_hits = _match_count(category, query_terms)
    summary_hits = _match_count(summary, query_terms)
    query_category_hits = _match_categories(book, normalized_query)

    score += title_hits * 3.5
    score += category_hits * 2.6
    score += author_hits * 1.4
    score += publisher_hits * 0.8
    score += summary_hits * 0.6

    if query_category_hits:
        score += 4.5

    if title_hits > 0 and category_hits > 0:
        score += 1.25

    if title_hits > 0 and re.search(r"健康|养生|科普|医疗|免疫力|长辈|老人|中老年", normalized_query):
        score += 0.9

    lexical_overlap = title_hits + author_hits + publisher_hits + category_hits + summary_hits
    if lexical_overlap == 0:
        score -= 2.75

    if re.search(r"健康|养生|医疗|免疫力|长辈|老人|中老年", normalized_query) and re.search(
        r"健康|养生|医疗|免疫力|长辈|老人|中老年", haystack
    ):
        score += 2.2

    if re.search(r"科普|科学|知识", normalized_query) and re.search(r"科普|科学|知识", haystack):
        score += 1.8

    if "象棋" in normalized_query:
        if _contains_any(haystack, ["象棋"]):
            score += 4.5
        if _contains_any(haystack, ["围棋", "国际象棋", "五子棋"]):
            score -= 4.5

    if "围棋" in normalized_query:
        if _contains_any(haystack, ["围棋"]):
            score += 4.5
        if _contains_any(haystack, ["象棋", "国际象棋", "五子棋"]):
            score -= 4.5

    if "国际象棋" in normalized_query:
        if _contains_any(haystack, ["国际象棋"]):
            score += 4.5
        if _contains_any(haystack, ["象棋", "围棋", "五子棋"]):
            score -= 4.5

    if "五子棋" in normalized_query:
        if _contains_any(haystack, ["五子棋"]):
            score += 4.5
        if _contains_any(haystack, ["象棋", "围棋", "国际象棋"]):
            score -= 4.5

    if re.search(r"历史|传记|人物|鲁迅", normalized_query):
        if _contains_any(haystack, ["传记", "人物", "鲁迅"]):
            score += 2.8
        if "小说" in haystack:
            score -= 2.6

    if "鲁迅" in normalized_query:
        if "鲁迅" in haystack:
            score += 20
        else:
            score -= 4.5

    return score


def rerank_books(books: Sequence[Any], query: str) -> List[Any]:
    if not books:
        return []

    scored = []
    for index, book in enumerate(books):
        score = _compute_score(book, query, index)
        scored.append((index, score, book))

    scored.sort(key=lambda item: (-item[1], item[0]))

    ranked: List[Any] = []
    for _, score, book in scored:
        _set_value(book, "score", score)
        _set_value(book, "relevance_score", score)
        ranked.append(book)

    return ranked
