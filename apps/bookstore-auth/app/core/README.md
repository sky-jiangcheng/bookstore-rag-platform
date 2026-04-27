# 核心模块索引

这个目录存放后端的基础设施层代码，当前主职责是提供常量、异常、日志、依赖注入和服务注册能力。

## 目录内容

| 文件 | 作用 |
|---|---|
| `constants.py` | 全局常量 |
| `exceptions.py` | 自定义异常 |
| `logging_config.py` | 日志配置 |
| `dependency_injection.py` | 依赖注入容器 |
| `service_registry.py` | 服务注册入口 |
| `startup_check.py` | 启动前检查 |
| `async_task_manager.py` | 异步任务管理 |
| `observability.py` | 可观测性支持 |
| `tracing.py` | 链路追踪支持 |

## 怎么看

- 想先了解项目整体结构，请看根目录 [README.md](../../../README.md)
- 想看重构演进，请看 [docs/refactor-history.md](../../../docs/refactor-history.md)
- 想看核心模块怎么组合，请先从 `service_registry.py` 和 `dependency_injection.py` 入手

## 使用约定

- 核心模块尽量只做基础设施，不承载具体业务逻辑
- 新服务优先通过依赖注入注册，而不是在业务代码里直接实例化
- 新异常优先继承 `BookStoreBaseException`

