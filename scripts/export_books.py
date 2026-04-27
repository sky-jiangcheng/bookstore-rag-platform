import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text


DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "books.json"


def build_engine():
    database_url = os.getenv("LEGACY_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Missing LEGACY_DATABASE_URL or DATABASE_URL")

    engine_kwargs = {"pool_pre_ping": True}
    if database_url.startswith("sqlite:"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(database_url, **engine_kwargs)


def build_query(database_url: str):
    if database_url.startswith("sqlite:"):
        return text(
            """
            SELECT
                id,
                title,
                author,
                publisher,
                COALESCE(price, 0) AS price,
                COALESCE(stock, 0) AS stock,
                COALESCE(summary, '') AS description,
                'general' AS category,
                0 AS popularity_score
            FROM t_book_info
            ORDER BY id
            """
        )

    return text(
        """
        SELECT
            id,
            title,
            author,
            publisher,
            COALESCE(price, 0) AS price,
            COALESCE(stock, 0) AS stock,
            COALESCE(
              JSON_UNQUOTE(JSON_EXTRACT(categories, '$[0]')),
              'general'
            ) AS category,
            COALESCE(semantic_description, summary, '') AS description,
            0 AS popularity_score
        FROM t_book_info
        ORDER BY id
        """
    )


def export_books(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    database_url = os.getenv("LEGACY_DATABASE_URL") or os.getenv("DATABASE_URL")
    engine = build_engine()
    query = build_query(database_url)

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    books = [
        {
            "id": int(row["id"]),
            "title": row["title"],
            "author": row["author"],
            "publisher": row["publisher"],
            "price": float(row["price"] or 0),
            "stock": int(row["stock"] or 0),
            "category": row["category"] or "general",
            "description": row["description"] or "",
            "popularity_score": float(row["popularity_score"] or 0),
        }
        for row in rows
    ]

    output_path.write_text(
        json.dumps({"books": books}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Exported {len(books)} books to {output_path}")


if __name__ == "__main__":
    target = Path(os.getenv("EXPORT_BOOKS_OUTPUT", str(DEFAULT_OUTPUT))).resolve()
    export_books(target)
