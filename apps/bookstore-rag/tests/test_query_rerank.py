import unittest

from app.utils.query_rerank import build_catalog_search_query, build_catalog_search_terms, rerank_books


class QueryRerankTest(unittest.TestCase):
    def test_expand_health_queries(self):
        terms = build_catalog_search_terms("推荐一些适合家里长辈看的健康养生和免疫力科普书。")
        self.assertIn("健康", terms)
        self.assertIn("养生", terms)
        self.assertIn("免疫力", terms)
        self.assertIn("科普", terms)
        self.assertIn("长辈", terms)
        self.assertIn("健康", build_catalog_search_query("推荐一些适合家里长辈看的健康养生和免疫力科普书。"))

    def test_keep_chess_query_focused_on_xiangqi(self):
        terms = build_catalog_search_terms("我想提升象棋残局和布局能力，有没有偏实战一点的书？")
        self.assertIn("象棋", terms)
        self.assertIn("残局", terms)
        self.assertIn("布局", terms)
        self.assertIn("实战", terms)
        self.assertNotIn("围棋", terms)
        self.assertNotIn("国际象棋", terms)

    def test_prioritize_named_people(self):
        books = [
            {
                "book_id": "1",
                "title": "历史人物纵横谈:清代人物",
                "author": "张三",
                "publisher": "某出版社",
                "category": "历史",
                "summary": "",
                "relevance_score": 99,
            },
            {
                "book_id": "2",
                "title": "鲁迅散文诗歌集",
                "author": "鲁迅",
                "publisher": "文学出版社",
                "category": "文学",
                "summary": "",
                "relevance_score": 1,
            },
        ]

        ranked = rerank_books(books, "有没有适合普通读者看的历史人物传记，最好是鲁迅相关的。")
        self.assertEqual(ranked[0]["book_id"], "2")


if __name__ == "__main__":
    unittest.main()
