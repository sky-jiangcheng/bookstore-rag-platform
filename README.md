# BookStore Local Platform

这是 BookStore 的单服务平台仓库。生产形态由根目录 `Dockerfile` 构建，`main.py` 作为唯一对外入口，把前端和后端收敛到同一个 Railway `platform` 服务里。

## 生产形态

- `main.py` - 单入口平台，生产运行时直接启动它
- `Dockerfile` - 根目录统一镜像构建，包含前端构建产物和后端依赖
- `railway.toml` - 单服务 Railway 配置，指向根目录 `Dockerfile`

## 仓库内容

- `apps/bookstore-frontend` - 前端页面与静态资源
- `apps/bookstore-gateway` - 平台共享后端代码
- `apps/bookstore-auth` - 历史认证模块，保留为内部代码
- `apps/bookstore-rag` - 历史推荐模块，保留为内部代码
- `apps/bookstore-catalog` - 历史目录能力，保留为内部代码
- `apps/bookstore-ops` - 历史运营能力，保留为内部代码

## 运行原则

- 生产只保留一个对外入口和一个 Railway 服务
- 前端静态资源与后端 API 同域
- 旧模块只保留在仓库里，不再作为独立部署目标

## 本地启动

```bash
cd /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform
uvicorn main:app --reload --port 8000
```

## 与线上项目的关系

- 本仓库负责平台侧的登录、推荐、书单生成和导出
- 线上部署只暴露单一平台域名，不再依赖多服务转发
- `bookstore-agentic-rag` 仍可作为其他项目的独立消费端

## 数据导出

推荐通过文件导出，而不是直接共享数据库连接。

```bash
cd /Users/jiangcheng/Workspace/Python/BookStore/bookstore-local-platform
export LEGACY_DATABASE_URL="sqlite:////absolute/path/to/bookstore.db"
python3 scripts/export_books.py
```

默认输出文件：

- `scripts/output/books.json`
