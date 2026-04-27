"""
大语言模型服务 - 支持多种LLM提供商
"""
import json
import os
from typing import Any, Dict, List, Optional

import logging
import requests
from abc import ABC, abstractmethod

try:
    import google.genai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


class LLMProviderInterface(ABC):
    """LLM提供商接口"""

    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """聊天完成"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass


class LLMProvider(LLMProviderInterface):
    """LLM提供商抽象基类"""

    pass


class OpenAIProvider(LLMProvider):
    """OpenAI提供商"""

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """OpenAI聊天完成"""
        try:
            url = f"{self.base_url}/chat/completions"

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }

            response = requests.post(
                url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "openai",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class QwenProvider(LLMProvider):
    """通义千问提供商 (阿里云)"""

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "qwen-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        self.base_url = config.get(
            "base_url",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """通义千问聊天完成"""
        try:
            url = f"{self.base_url}/chat/completions"

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }

            response = requests.post(
                url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "qwen",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class ErnieProvider(LLMProvider):
    """文心一言提供商 (百度)"""

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.secret_key = config.get("secret_key", "")
        self.model = config.get("model", "ERNIE-Bot-turbo")
        self.temperature = config.get("temperature", 0.7)

    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if not self.api_key or not self.secret_key:
            raise ValueError("API key and secret key are required for Ernie provider")

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result["access_token"]

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """文心一言聊天完成"""
        try:
            access_token = self._get_access_token()
            url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.model}?access_token={access_token}"

            # 转换消息格式为文心一言格式
            ernie_messages = []
            for msg in messages:
                ernie_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            payload = {
                "messages": ernie_messages,
                "temperature": kwargs.get("temperature", self.temperature),
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result["result"]

        except Exception as e:
            logger.error(f"Ernie API error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "ernie",
            "model": self.model,
            "temperature": self.temperature,
        }


class ZhipuProvider(LLMProvider):
    """智谱GLM提供商 (智谱AI)"""

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "glm-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        self.base_url = config.get(
            "base_url",
            "https://open.bigmodel.cn/api/paas/v4"
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """智谱GLM聊天完成"""
        try:
            url = f"{self.base_url}/chat/completions"

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }

            response = requests.post(
                url, headers=self.headers, json=payload, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Zhipu API error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "zhipu",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


class LocalLLMProvider(LLMProvider):
    """本地LLM提供商（支持Ollama等）"""

    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.model = config.get("model", "llama2")
        self.temperature = config.get("temperature", 0.7)

        self.headers = {"Content-Type": "application/json"}

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """本地LLM聊天完成"""
        try:
            url = f"{self.base_url}/api/generate"

            # 构建prompt
            prompt = self._build_prompt(messages)

            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": kwargs.get("temperature", self.temperature),
                "stream": False,
            }

            response = requests.post(
                url, headers=self.headers, json=payload, timeout=60
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            raise

    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """构建prompt"""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            prompt_parts.append(f"{role}: {content}")

        return "\n".join(prompt_parts)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "local",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
        }


class GeminiProvider(LLMProvider):
    """Gemini提供商"""

    def __init__(self, config: Dict[str, Any]):
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gemini-pro")
        self.temperature = config.get("temperature", 0.7)
        self.max_output_tokens = config.get("max_output_tokens", 2000)

        self.genai = genai
        self.gemini_model = None

        if self.genai and self.api_key:
            try:
                self.client = self.genai.Client(api_key=self.api_key)
                self.gemini_model = self.client.models
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {str(e)}")

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Gemini聊天完成"""
        try:
            if not self.gemini_model:
                raise Exception("Gemini model not initialized")

            # 构建Gemini格式的消息
            gemini_messages = []
            for message in messages:
                role = message.get("role", "user")
                content = message.get("content", "")
                gemini_messages.append(f"{role}: {content}")

            prompt = "\n".join(gemini_messages)

            # 生成响应
            response = self.gemini_model.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "temperature": kwargs.get("temperature", self.temperature),
                    "max_output_tokens": kwargs.get(
                        "max_output_tokens", self.max_output_tokens
                    ),
                },
            )

            return response.text

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "gemini",
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
        }


class MockLLMProvider(LLMProvider):
    """模拟LLM提供商 - 用于测试"""

    def __init__(self, config: Dict[str, Any]):
        self.model = config.get("model", "mock-gpt")

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """模拟聊天完成"""
        # 检查是否是需求解析的对话请求
        is_demand_analysis = False
        user_message = ""
        
        # 检查所有消息，包括系统消息和用户消息
        for msg in messages:
            msg_content = msg.get("content", "")
            if "需求解析" in msg_content or "用户画像" in msg_content or "屏蔽词类别" in msg_content or "书单分类" in msg_content:
                is_demand_analysis = True
            if msg.get("role") == "user":
                user_message = msg_content
        
        # 也检查用户消息中是否包含常见的需求表达
        if "我想为" in user_message or "生成一份" in user_message or "书单" in user_message:
            is_demand_analysis = True

        if is_demand_analysis:
            # 解析用户消息中的需求
            user_needs = user_message
            
            # 生成需求解析结果
            return json.dumps(
                {
                    "type": "analysis",
                    "content": "我已经了解了您的需求，为大学生生成一份包含军事、历史、传记的书单。请确认以下信息是否正确：\n1. 目标读者：大学生\n2. 分类及比例：军事(34%)、历史(33%)、传记(33%)\n3. 书单总数：20本\n4. 比例误差范围：5%",
                    "updated_context": {
                        "user_profile": {
                            "occupation": "学生",
                            "age_group": "18-25岁",
                            "domain_scope": "大学教育",
                            "reading_preferences": ["军事", "历史", "传记"]
                        },
                        "filter_category": {
                            "category_name": "默认",
                            "needs_new_category": False,
                            "new_category_name": None
                        },
                        "book_categories": [
                            {"category": "军事", "percentage": 34, "count": 7},
                            {"category": "历史", "percentage": 33, "count": 7},
                            {"category": "传记", "percentage": 33, "count": 6}
                        ],
                        "constraints": {
                            "proportion_error_range": 5.0,
                            "total_book_count": 20,
                            "other_constraints": []
                        },
                        "completed": True
                    }
                },
                ensure_ascii=False,
            )

        # 简单的规则回复
        if "分类" in user_message or "category" in user_message.lower():
            return json.dumps(
                {"categories": ["文学", "历史", "科技"], "confidence": 0.8},
                ensure_ascii=False,
            )

        if "推荐" in user_message or "recommend" in user_message.lower():
            return json.dumps(
                {
                    "recommendations": [
                        {"title": "示例书籍1", "author": "作者A"},
                        {"title": "示例书籍2", "author": "作者B"},
                    ]
                },
                ensure_ascii=False,
            )

        if "分析" in user_message or "analyze" in user_message.lower():
            return json.dumps(
                {
                    "analysis": "这是一个模拟的分析结果",
                    "sentiment": "positive",
                    "topics": ["主题1", "主题2"],
                },
                ensure_ascii=False,
            )

        return "这是模拟LLM的回复"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {"provider": "mock", "model": self.model, "purpose": "testing"}


class LLMServiceInterface(ABC):
    """LLM服务接口"""

    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """聊天完成"""
        pass

    @abstractmethod
    def switch_provider(self, provider_type: str) -> LLMProviderInterface:
        """切换LLM提供商"""
        pass

    @abstractmethod
    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pass


class LLMService(LLMServiceInterface):
    """LLM服务主类"""

    def __init__(self, config_loader=None):
        """
        初始化LLM服务

        Args:
            config_loader: 配置加载器实例
        """
        # 使用传入的配置加载器或默认的配置加载器
        if config_loader is None:
            from app.utils.config_loader import config_loader as default_config_loader

            self.config_loader = default_config_loader
        else:
            self.config_loader = config_loader

        # 加载LLM配置
        self.llm_config = self.config_loader.get_llm_config()
        self.default_service = self.config_loader.get_default_ai_service()
        self.service_priority = self.config_loader.get_service_priority()

        # 初始提供商类型
        self.provider_type = self.default_service
        self.provider = self._create_provider()

    def _create_provider(self) -> LLMProvider:
        """创建LLM提供商"""
        provider_type = self.provider_type.lower()

        if provider_type == "openai":
            openai_config = self.config_loader.get_openai_config()
            if not openai_config.get("api_key"):
                logger.warning("No OpenAI API key found, using mock provider")
                return MockLLMProvider(openai_config)
            return OpenAIProvider(openai_config)

        elif provider_type == "gemini":
            gemini_config = self.config_loader.get_gemini_config()
            if not gemini_config.get("api_key"):
                logger.warning("No Gemini API key found, using mock provider")
                return MockLLMProvider(gemini_config)
            try:
                return GeminiProvider(gemini_config)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}, using mock provider")
                return MockLLMProvider(gemini_config)

        elif provider_type == "qwen":
            qwen_config = self.config_loader.get_qwen_config()
            if not qwen_config.get("api_key"):
                logger.warning("No Qwen API key found, using mock provider")
                return MockLLMProvider(qwen_config)
            return QwenProvider(qwen_config)

        elif provider_type == "ernie":
            ernie_config = self.config_loader.get_ernie_config()
            if not ernie_config.get("api_key") or not ernie_config.get("secret_key"):
                logger.warning("No Ernie API key or secret key found, using mock provider")
                return MockLLMProvider(ernie_config)
            return ErnieProvider(ernie_config)

        elif provider_type == "zhipu":
            zhipu_config = self.config_loader.get_zhipu_config()
            if not zhipu_config.get("api_key"):
                logger.warning("No Zhipu API key found, using mock provider")
                return MockLLMProvider(zhipu_config)
            return ZhipuProvider(zhipu_config)

        elif provider_type == "local":
            local_config = self.config_loader.get_local_llm_config()
            return LocalLLMProvider(local_config)

        elif provider_type == "mock":
            return MockLLMProvider({})

        else:
            logger.warning(f"Unknown provider type: {provider_type}, using mock")
            return MockLLMProvider({})

    def switch_provider(self, provider_type: str) -> LLMProvider:
        """切换LLM提供商"""
        self.provider_type = provider_type
        self.provider = self._create_provider()
        return self.provider

    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return ["openai", "gemini", "qwen", "ernie", "zhipu", "local", "mock"]

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """聊天完成"""
        try:
            return self.provider.chat_completion(messages, **kwargs)
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            # 降级到mock回复
            mock_provider = MockLLMProvider({})
            return mock_provider.chat_completion(messages, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """聊天完成（别名方法，保持向后兼容）"""
        return self.chat_completion(messages, **kwargs)

    def parse_user_request(self, user_input: str) -> Dict[str, Any]:
        """解析用户请求（用于定制书单）"""
        try:
            prompt = f"""
请解析以下用户的书单请求，提取关键信息并以JSON格式返回：

用户请求：{user_input}

请提取以下信息：
1. target_audience: 目标读者群体（如：大学生、职场新人、儿童等）
2. categories: 各类别及其比例要求（如：{{"文学": 0.3, "科技": 0.2, "历史": 0.5}}）
3. cognitive_level: 认知水平要求（如：入门、进阶、高等、专业）
4. difficulty_range: 难度范围（如：[3, 7]）
5. book_count: 推荐书籍数量
6. special_requirements: 特殊要求（如：必须适合初学者、偏好经典著作等）

如果没有明确提及某些字段，请基于上下文合理推断或省略。

返回格式：
{
    "target_audience": "...",
    "categories": {"类别": 比例, ...},
    "cognitive_level": "...",
    "difficulty_range": [最小难度, 最大难度],
    "book_count": 数量,
    "special_requirements": ["要求1", "要求2", ...]
}
"""

            messages = [
                {"role": "system", "content": "你是一个专业的书单分析助手，擅长理解用户需求并提取结构化信息。"},
                {"role": "user", "content": prompt},
            ]

            response = self.chat_completion(messages, temperature=0.3)
            logger.info(f"LLM response: {response}")

            try:
                # 尝试解析JSON
                result = json.loads(response)
                logger.info(f"Parsed LLM result: {result}")
                return result
            except json.JSONDecodeError as e:
                logger.warning(
                    f"Failed to parse LLM response as JSON: {e}, response: {response}"
                )
                # 手动解析
                return self._manual_parse_request(user_input)
        except Exception as e:
            logger.error(f"Error in parse_user_request: {e}")
            # 直接返回手动解析结果
            return self._manual_parse_request(user_input)

    def classify_book_categories(self, book_info: Dict[str, Any]) -> List[str]:
        """分类书籍"""
        title = book_info.get("title", "")
        description = book_info.get("semantic_description", "")
        author = book_info.get("author", "")

        prompt = f"""
请为以下书籍分类，选择最合适的1-3个类别：

书名：{title}
作者：{author}
描述：{description}

可选类别：
- 文学（小说、散文、诗歌、戏剧等）
- 历史（历史著作、传记、文明史等）
- 科技（计算机、工程、自然科学等）
- 艺术（艺术理论、绘画、音乐、摄影等）
- 哲学（哲学思想、逻辑学、伦理学等）
- 教育（教育理论、学习方法、教材等）
- 商业（经济、管理、营销、投资等）
- 心理学（心理学理论、应用心理学等）
- 社会科学（社会学、政治学、法学等）
- 生活（健康、美食、旅游、家居等）

请以JSON数组格式返回最合适的类别，按相关度排序：
["类别1", "类别2", "类别3"]
"""

        messages = [
            {"role": "system", "content": "你是一个专业的图书分类专家，擅长准确判断书籍的类别。"},
            {"role": "user", "content": prompt},
        ]

        response = self.chat_completion(messages, temperature=0.2)

        try:
            result = json.loads(response)
            # 处理MockLLMProvider返回的字典格式
            if isinstance(result, dict) and "categories" in result:
                return result["categories"]
            # 处理正常的列表格式
            elif isinstance(result, list):
                return result
            else:
                # 基于关键词的简单分类
                return self._simple_classify(title + " " + description)
        except json.JSONDecodeError:
            # 基于关键词的简单分类
            return self._simple_classify(title + " " + description)

    def analyze_reading_level(self, book_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析书籍阅读水平"""
        title = book_info.get("title", "")
        description = book_info.get("semantic_description", "")

        prompt = f"""
请分析以下书籍的阅读水平：

书名：{title}
描述：{description}

请分析以下维度：
1. cognitive_level: 认知水平（入门、进阶、高等、专业）
2. difficulty_level: 难度等级（1-10分）
3. target_audience: 目标读者群体
4. prerequisites: 必备的前置知识

返回JSON格式：
{{
    "cognitive_level": "入门/进阶/高等/专业",
    "difficulty_level": 1-10,
    "target_audience": ["读者群体1", "读者群体2"],
    "prerequisites": ["知识1", "知识2"]
}}
"""

        messages = [
            {"role": "system", "content": "你是一个教育专家，擅长评估书籍的阅读难度和适合的读者群体。"},
            {"role": "user", "content": prompt},
        ]

        response = self.chat_completion(messages, temperature=0.2)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 默认值
            return {
                "cognitive_level": "进阶",
                "difficulty_level": 5,
                "target_audience": ["一般读者"],
                "prerequisites": [],
            }

    def generate_book_description(self, book_info: Dict[str, Any]) -> str:
        """生成书籍语义描述"""
        title = book_info.get("title", "")
        author = book_info.get("author", "")
        publisher = book_info.get("publisher", "")

        prompt = f"""
请为以下书籍生成一个详细的语义描述，用于智能推荐和查重：

书名：{title}
作者：{author}
出版社：{publisher}

请生成一个100-200字的描述，包括：
1. 书籍的主要内容和主题
2. 适合的读者群体
3. 知识水平和认知要求
4. 与其他书籍可能的关系

描述要求：
- 准确反映书籍内容
- 突出特色和价值
- 便于系统理解和匹配
- 使用正式、客观的语言
"""

        messages = [
            {"role": "system", "content": "你是一个图书专家，擅长为书籍撰写准确、有用的描述。"},
            {"role": "user", "content": prompt},
        ]

        return self.chat_completion(messages, temperature=0.4)

    def _manual_parse_request(self, user_input: str) -> Dict[str, Any]:
        """手动解析请求（备用方案）"""
        result = {}

        # 简单的关键词匹配
        if "大学" in user_input:
            result["target_audience"] = "大学生"
        elif "职场" in user_input or "工作" in user_input:
            result["target_audience"] = "职场新人"
        elif "儿童" in user_input or "少儿" in user_input:
            result["target_audience"] = "儿童"

        # 解析比例（简单实现）
        if "%" in user_input:
            import re

            percentages = re.findall(r"(\w+)(\d+)%", user_input)
            if percentages:
                categories = {}
                for category, percent in percentages:
                    categories[category] = int(percent) / 100.0
                result["categories"] = categories

        return result

    def _simple_classify(self, text: str) -> List[str]:
        """简单分类（备用方案）"""
        categories = []

        # 关键词映射
        category_keywords = {
            "文学": ["小说", "散文", "诗歌", "文学", "故事", "名著"],
            "历史": ["历史", "传记", "古代", "朝代", "战争史"],
            "科技": ["编程", "计算机", "技术", "科学", "工程"],
            "艺术": ["艺术", "绘画", "音乐", "美术", "摄影"],
            "哲学": ["哲学", "思想", "逻辑", "伦理"],
            "教育": ["教育", "学习", "教材", "教辅", "考试"],
        }

        text_lower = text.lower()
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)

        return categories[:3] if categories else ["文学"]  # 默认分类

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return self.provider.get_model_info()


# 全局LLM服务实例（向后兼容）
from app.utils.config_loader import config_loader

llm_service = LLMService(config_loader=config_loader)
