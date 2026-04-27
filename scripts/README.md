# Scripts

本目录用于本地平台向外提供稳定的脚本接口。

当前约定：

- `export_books.py`: 将旧库中的图书导出为 `books.json`

目标是让 `bookstore-local-platform` 和 `bookstore-agentic-rag` 通过文件协议协作，而不是共享运行时。
