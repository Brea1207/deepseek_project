# LLM 联网搜索插件 (LLM Web Search Plugin)

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.7%2B-blue" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License: MIT">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange" alt="Version: 1.0.0">
</div>

## 📖 简介 (Introduction)

这个项目是一个为本地部署的大语言模型（LLM）提供联网搜索功能的插件。由于本地部署的大模型通常无法直接联网搜索，这个插件可以帮助模型获取最新的互联网信息，从而提供更准确和及时的回答。

This project is a plugin that provides web search capabilities for locally deployed Large Language Models (LLMs). Since locally deployed LLMs typically cannot directly search the internet, this plugin helps models obtain the latest internet information, enabling more accurate and timely responses.

## ✨ 功能特点 (Features)

- 🔍 支持多种搜索引擎（目前支持 Google、Bing 和百度）
- 📝 可以获取搜索结果摘要
- 📄 可以抓取网页详细内容
- 🤖 自动格式化搜索结果为适合 LLM 处理的提示词
- 🔌 提供简单的 API 接口，易于与各种 LLM 集成
- 📚 包含示例客户端代码，展示如何与本地 LLM 集成
- 🇨🇳 针对中文搜索优化，特别是使用百度搜索引擎
- ⏰ 支持获取实时时间信息
- 🛠️ 提供可配置的 Web 界面，方便调整各项参数

## 🔧 系统要求 (System Requirements)

- Python 3.7+
- 网络连接
- 本地部署的 LLM（推荐使用 Ollama、llama.cpp 等）

## 📦 安装步骤 (Installation)

1. 克隆或下载本仓库

```bash
```

2. 安装依赖包

```bash
pip install -r requirements.txt
```

3. 创建 `.env` 文件（可选）

```
DEBUG=True
PORT=5005
SEARCH_ENGINE=google  # 可选值: google, bing, baidu
```

## 🚀 使用方法 (Usage)

### 启动搜索 API 服务

```bash
python run_server.py
```

服务将在 http://localhost:5005 启动（除非在 .env 文件中指定了其他端口）。

也可以通过环境变量指定搜索引擎：

```bash
SEARCH_ENGINE=baidu python run_server.py
```

### 访问 Web 界面

启动服务后，可以通过浏览器访问以下页面：

- 主页: http://localhost:5005/
- LLM 交互页面: http://localhost:5005/llm
- 配置页面: http://localhost:5005/config

### API 端点

#### POST /search

执行网络搜索并返回格式化的结果。

请求示例：

```json
{
    "query": "你的搜索查询",
    "num_results": 5,
    "fetch_content": false,
    "search_engine": "baidu",
    "llm_model": "deepseek-r1:1.5b",
    "temperature": 0.7,
    "max_tokens": 2048
}
```

参数说明：
- `query`: 搜索查询（必需）
- `num_results`: 返回结果数量（可选，默认为 5）
- `fetch_content`: 是否获取详细网页内容（可选，默认为 false）
- `search_engine`: 使用的搜索引擎，"google"、"bing" 或 "baidu"（可选，默认为 "google"）
- `llm_model`: 使用的 LLM 模型（可选）
- `temperature`: 生成温度（可选）
- `max_tokens`: 最大生成 token 数（可选）

响应示例：

```json
{
    "query": "你的搜索查询",
    "search_results": [
        {
            "title": "结果标题",
            "link": "https://example.com",
            "snippet": "结果摘要..."
        },
        ...
    ],
    "detailed_content": {
        "https://example.com": "网页内容..."
    },
    "formatted_response": "格式化后的提示词，可直接发送给 LLM",
    "llm_config": {
        "model": "deepseek-r1:1.5b",
        "temperature": 0.7,
        "max_tokens": 2048
    }
}
```

#### GET /current_time

获取当前时间信息。

响应示例：

```json
{
    "time": "2025-03-11 17:00:55",
    "timezone": "Asia/Shanghai",
    "source": "system"
}
```

## 🔄 与本地 LLM 集成 (Integration with Local LLMs)

`llm_client_example.py` 文件提供了一个示例客户端，已经内置支持 Ollama、llama.cpp 等多种本地模型。您可以直接使用命令行运行客户端，也可以在自己的代码中导入并使用客户端类。

### 命令行运行示例

```bash
# 使用默认设置（Ollama 和 llama3 模型）
python llm_client_example.py

# 指定不同的模型
python llm_client_example.py --model-name qwen:7b

# 指定不同的搜索引擎
python llm_client_example.py --search-engine baidu

# 指定不同的温度参数
python llm_client_example.py --temperature 0.5
```

### 在自己的代码中使用示例

```python
from llm_client_example import LLMWebSearchClient

# 初始化客户端（默认使用 Ollama 和 llama3 模型）
client = LLMWebSearchClient()

# 或者指定不同的模型
# client = LLMWebSearchClient(llm_type="ollama", model_name="qwen:7b")

# 使用网络搜索回答问题
result = client.answer_with_web_search("最新的 AI 技术进展是什么？")

# 打印 LLM 的回答
print(result["llm_response"])
```

## 🧪 测试工具 (Testing Tools)

项目中包含一个综合测试工具 `test_utils.py`，提供了多种测试功能：

1. 测试搜索引擎的搜索结果
2. 测试LLM对搜索结果的利用情况
3. 比较不同搜索引擎的结果差异

### 使用方法

```bash
# 测试搜索引擎
python test_utils.py --mode search --query "量子计算" --search-engine baidu

# 测试LLM响应
python test_utils.py --mode llm --query "人工智能应用" --model "qwen:7b" --temperature 0.5

# 比较搜索引擎
python test_utils.py --mode compare --query "深度学习框架对比"
```

### 参数说明

- `--mode`: 测试模式，可选值为 "search"(测试搜索引擎)、"llm"(测试LLM响应)、"compare"(比较搜索引擎)
- `--query`: 要测试的查询（如果不提供，将使用默认查询"量子计算最新进展"）
- `--verbose`: 显示详细信息，包括完整提示词
- `--search-engine`: 使用的搜索引擎，可选值为 "google"、"bing" 或 "baidu"（默认为 "baidu"）
- `--engines`: 比较模式下要比较的搜索引擎列表（默认为 "google bing baidu"）
- `--mock`: 使用模拟搜索数据，不进行实际搜索
- `--model`: 指定使用的 LLM 模型名称（默认为 "deepseek-r1:1.5b"）
- `--api-url`: 指定搜索 API 的 URL（默认为 "http://localhost:5005/search"）
- `--temperature`: LLM 生成的温度参数（默认为 0.7）
- `--num-results`: 搜索结果数量（默认为 5）
- `--fetch-content`: 获取详细网页内容

## 🌐 支持的 LLM 模型 (Supported LLM Models)

最新版本的客户端已经内置支持多种本地模型，包括：

### Ollama 支持的模型

- llama3 (推荐)
- deepseek-r1:1.5b / 7b / 671b
- qwen:7b / 14b / 72b
- yi:34b
- gemma:7b / 2b
- mistral:7b
- mixtral:8x7b
- ...以及其他 Ollama 支持的模型

### 如何使用 Ollama

Ollama 是一个流行的本地模型部署工具，可以轻松运行各种开源大语言模型。我们的插件默认支持 Ollama。

1. 首先，确保您已经安装了 Ollama，安装指南可以在 [Ollama 官方网站](https://ollama.ai) 找到。

2. 下载您想要使用的模型，例如：

```bash
ollama pull llama3
# 或者其他模型，如
# ollama pull qwen:7b
# ollama pull gemma:7b
```

3. 使用我们的客户端连接到 Ollama：

```bash
python llm_client_example.py --llm-type ollama --model-name llama3
```

## ⚙️ 配置选项 (Configuration Options)

通过访问配置页面 (http://localhost:5005/config)，您可以调整以下配置选项：

### 搜索设置
- 默认搜索引擎 (Google, Bing, Baidu)
- 默认结果数量
- 是否默认获取详细内容
- 最大内容长度

### 时间获取设置
- 默认时区
- 时间源 URL

### LLM 模型设置
- 默认 LLM 模型
- 默认温度参数
- 默认最大 token 数

### 高级设置
- User Agent
- 是否启用详细日志记录

## 🤝 贡献 (Contributing)

欢迎贡献代码、报告问题或提出改进建议！您可以通过以下方式参与：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启一个 Pull Request

## 📄 许可证 (License)

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 📞 联系方式 (Contact)

如有任何问题或建议，请通过以下方式联系我们：

- 项目主页: [GitHub 仓库](https://github.com/yourusername/llm-web-search-plugin)
- 电子邮件: 1692775560@qq.com

---

<div align="center">
  <p>Made with ❤️ for LLM enthusiasts</p>
</div>
