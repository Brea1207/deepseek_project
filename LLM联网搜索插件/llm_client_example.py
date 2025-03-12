import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Union

# 加载环境变量
load_dotenv()

class LLMWebSearchClient:
    """
    连接本地LLM与网络搜索插件的客户端。
    这是一个示例实现，可以适配不同的LLM API。
    """
    
    def __init__(self, llm_api_url=None, search_api_url=None, model_name=None, temperature=0.7, max_tokens=2048, llm_type="ollama"):
        """初始化LLM Web搜索客户端"""
        # 默认API URL
        self.llm_api_url = llm_api_url or os.environ.get("LLM_API_URL", "http://localhost:5000/api/llm")
        self.search_api_url = search_api_url or os.environ.get("SEARCH_API_URL", "http://localhost:5005/search")
        self.ollama_api_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
        
        # LLM参数
        self.llm_type = llm_type  # 可以是 "api" 或 "ollama"
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 如果没有指定模型，自动检测并选择合适的模型
        if model_name is None:
            self.model_name = self._detect_best_model()
        else:
            self.model_name = model_name
        
        print(f"使用模型: {self.model_name}")
    
    def _detect_best_model(self):
        """检测并选择最佳可用模型"""
        if self.llm_type != "ollama":
            return "deepseek-r1:1.5b"  # 非Ollama模式下的默认模型
        
        try:
            # 获取Ollama可用模型列表
            response = requests.get(f"{self.ollama_api_url}/api/tags")
            if response.status_code != 200:
                print("无法获取Ollama模型列表，使用默认模型")
                return "deepseek-r1:1.5b"
            
            models = response.json().get("models", [])
            
            # 模型优先级列表（从高到低）
            preferred_models = [
                # 7B级别模型优先
                "deepseek-r1:7b", "qwen:7b", "llama3", "gemma:7b", "mistral:7b",
                # 其次是其他大小模型
                "deepseek-r1:67b", "qwen:14b", "qwen:72b", "yi:34b", "mixtral:8x7b",
                # 最后是小模型
                "deepseek-r1:1.5b", "gemma:2b"
            ]
            
            # 检查可用模型中是否有优先级列表中的模型
            available_models = [model["name"] for model in models]
            
            for preferred_model in preferred_models:
                # 完全匹配
                if preferred_model in available_models:
                    return preferred_model
                
                # 部分匹配（例如，如果有qwen:7b-chat，也可以匹配qwen:7b）
                for available_model in available_models:
                    if preferred_model in available_model:
                        return available_model
            
            # 如果没有找到任何优先级列表中的模型，但有其他模型可用
            if available_models:
                # 优先选择名称中包含7b的模型
                for model in available_models:
                    if "7b" in model.lower():
                        return model
                # 否则返回第一个可用模型
                return available_models[0]
            
            # 如果完全没有可用模型，返回默认模型
            return "deepseek-r1:1.5b"
        
        except Exception as e:
            print(f"检测模型时出错: {e}")
            return "deepseek-r1:1.5b"
    
    def search_web(self, query, num_results=5, fetch_content=True, search_engine="google"):
        """执行网络搜索并返回结果"""
        try:
            # 构建搜索请求
            search_request = {
                "query": query,
                "num_results": num_results,
                "fetch_content": fetch_content,
                "search_engine": search_engine
            }
            
            print(f"发送搜索请求到: {self.search_api_url}")
            # 发送搜索请求
            response = requests.post(
                self.search_api_url,
                json=search_request,
                headers={"Content-Type": "application/json"},
                timeout=30  # 添加超时设置
            )
            
            # 检查响应
            response.raise_for_status()  # 如果状态码不是200，会抛出异常
            search_data = response.json()
            
            # 从响应中提取搜索结果
            search_results = search_data.get("search_results", [])
            return {"search_results": search_results}
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"无法连接到搜索服务 ({self.search_api_url}): {str(e)}"
            print(error_msg)
            return {"search_results": [], "error": error_msg}
        except requests.exceptions.Timeout as e:
            error_msg = f"搜索请求超时: {str(e)}"
            print(error_msg)
            return {"search_results": [], "error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"搜索请求失败: {str(e)}"
            print(error_msg)
            return {"search_results": [], "error": error_msg}
        except json.JSONDecodeError as e:
            error_msg = f"无法解析搜索响应: {str(e)}"
            print(error_msg)
            return {"search_results": [], "error": error_msg}
        except Exception as e:
            error_msg = f"执行网络搜索时出错: {str(e)}"
            print(error_msg)
            return {"search_results": [], "error": error_msg}
    
    def query_llm(self, prompt, model=None, temperature=None, max_tokens=None):
        """直接查询LLM并返回响应"""
        try:
            # 使用提供的参数或默认参数
            model = model or self.model_name
            temperature = temperature if temperature is not None else self.temperature
            max_tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # 根据LLM类型选择不同的查询方法
            if self.llm_type == "ollama":
                # Ollama API调用
                try:
                    response = requests.post(
                        f"{self.ollama_api_url}/api/generate",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {
                                "temperature": temperature,
                                "num_predict": max_tokens
                            }
                        },
                        timeout=60
                    )
                    response.raise_for_status()  # 如果状态码不是200，会抛出异常
                    return response.json().get("response", "无法获取LLM回答")
                except requests.exceptions.RequestException as e:
                    if "404" in str(e):
                        return "抱歉，无法连接到Ollama服务。请确保Ollama已安装并运行在端口11434上。\n\n错误详情: 404 Not Found - Ollama服务未找到。"
                    else:
                        return f"抱歉，连接到Ollama服务时出错: {str(e)}"
            else:  # 默认使用API
                response = requests.post(
                    self.llm_api_url,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=60
                )
                response.raise_for_status()
                return response.json().get("choices", [{}])[0].get("message", {}).get("content", "无法获取LLM回答")
        except Exception as e:
            return f"查询LLM时出错: {str(e)}"
    
    def answer_with_web_search(self, query, num_results=5, fetch_content=True, search_engine="google"):
        """使用网络搜索增强LLM回答"""
        try:
            # 执行网络搜索
            search_result = self.search_web(query, num_results, fetch_content, search_engine)
            
            # 检查是否有错误信息
            if "error" in search_result:
                error_message = search_result.get("error", "未知错误")
                return {
                    "answer": f"抱歉，无法获取搜索结果。请检查网络连接或稍后再试。\n\n技术详情: {error_message}",
                    "search_results": []
                }
            
            # 检查搜索结果是否为空
            if not search_result["search_results"]:
                return {
                    "answer": "抱歉，无法获取搜索结果。请检查网络连接或稍后再试。",
                    "search_results": []
                }
            
            # 构建包含搜索结果的提示
            search_context = "\n".join([
                f"[{i}] {result.get('title', '无标题')}\n"
                f"链接: {result.get('url', result.get('link', '无链接'))}\n"
                f"摘要: {result.get('snippet', '无摘要')}\n"
                for i, result in enumerate(search_result["search_results"], 1)
            ])
            
            # 构建最终提示
            prompt = f"""请基于以下搜索结果回答问题。在回答中引用相关信息的来源，使用[数字]格式引用（例如[1]，[2]等）。

问题: {query}

搜索结果:
{search_context}

请提供详细、准确的回答，并确保引用相关信息的来源。如果搜索结果中没有足够的信息来回答问题，请说明这一点。"""
            
            # 查询LLM
            answer = self.query_llm(prompt)
            
            # 返回答案和搜索结果
            return {
                "answer": answer,
                "search_results": search_result["search_results"]
            }
        except Exception as e:
            error_message = str(e)
            print(f"使用网络搜索回答时出错: {error_message}")
            return {
                "answer": f"抱歉，处理您的请求时出错: {error_message}",
                "search_results": []
            }
    
def main():
    """LLMWebSearchClient的示例用法"""
    import argparse
    import time
    
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='LLM网络搜索客户端')
    parser.add_argument('--llm-type', type=str, default='ollama', choices=['ollama', 'api'],
                        help='LLM类型: ollama, api')
    parser.add_argument('--model-name', type=str, default=None,
                        help='模型名称，如deepseek-r1:7b, llama3等。不指定则自动检测最佳模型')
    parser.add_argument('--api-url', type=str, default=None,
                        help='LLM API URL (仅在llm-type为api时使用)')
    parser.add_argument('--search-api-url', type=str, default='http://localhost:5005/search',
                        help='搜索API URL')
    parser.add_argument('--search-engine', type=str, default='google', choices=['google', 'bing', 'baidu'],
                        help='搜索引擎: google, bing, baidu')
    parser.add_argument('--temperature', type=float, default=0.7,
                        help='生成文本的温度，控制随机性，值越高结果越多样')
    parser.add_argument('--max-tokens', type=int, default=2048,
                        help='生成的最大token数量')
    parser.add_argument('--interactive', action='store_true',
                        help='启用交互模式，可以连续提问')
    
    args = parser.parse_args()
    
    # 初始化客户端
    client = LLMWebSearchClient(
        search_api_url=args.search_api_url,
        llm_api_url=args.api_url,
        llm_type=args.llm_type,
        model_name=args.model_name,
        temperature=args.temperature,
        max_tokens=args.max_tokens
    )
    
    def process_query(query):
        # 使用网络搜索回答
        print(f"\n正在搜索网络并查询LLM ({args.llm_type}:{args.model_name})...")
        start_time = time.time()
        result = client.answer_with_web_search(query, search_engine=args.search_engine)
        processing_time = time.time() - start_time
        
        # 打印结果
        if "error" in result:
            print(f"错误: {result['error']}")
            return
            
        print("\n=== 搜索结果 ===")
        for i, res in enumerate(result["search_results"], 1):
            print(f"{i}. {res.get('title', '无标题')}")
            print(f"   {res.get('link', '无链接')}")
            snippet = res.get('snippet', '无摘要')
            if len(snippet) > 100:
                snippet = snippet[:100] + "..."
            print(f"   {snippet}")
        
        print(f"\n=== LLM回答 (处理时间: {processing_time:.2f}秒) ===")
        print(result["answer"])
    
    if args.interactive:
        print(f"进入交互模式 (使用 {args.llm_type}:{args.model_name})，输入'exit'或'quit'退出")
        while True:
            query = input("\n请输入您的问题: ")
            if query.lower() in ['exit', 'quit', '退出']:
                break
            process_query(query)
    else:
        # 获取用户查询
        query = input("请输入您的问题: ")
        process_query(query)


if __name__ == "__main__":
    main()
