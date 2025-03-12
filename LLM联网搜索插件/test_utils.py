#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM联网搜索插件测试工具集

该文件整合了多个测试功能，包括：
1. 测试不同搜索引擎的搜索结果
2. 测试LLM对搜索结果的利用情况
3. 比较不同搜索引擎的结果差异

使用方法:
    python test_utils.py --mode [search|llm|compare] --query "你的查询" --search-engine baidu

示例:
    # 测试搜索引擎
    python test_utils.py --mode search --query "量子计算" --search-engine baidu
    
    # 测试LLM响应
    python test_utils.py --mode llm --query "人工智能应用" --model "qwen:7b" --temperature 0.5
    
    # 比较搜索引擎
    python test_utils.py --mode compare --query "深度学习框架对比"
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
import pytz
import random
import requests
from llm_client_example import LLMWebSearchClient
from search_engine import WebSearch
from response_processor import ResponseProcessor

def is_time_query(query):
    """判断是否为时间查询"""
    # 简单的时间查询关键词
    time_keywords = ["几点", "时间", "日期", "current time", "what time", "date"]
    
    # 排除词，这些词虽然包含时间相关词汇，但不是询问当前时间
    exclude_keywords = ["时间管理", "时间复杂度", "时间序列", "时间轴", "时间旅行", "时间简史", 
                       "时间规划", "时间胶囊", "日期选择", "日期格式", "日期范围"]
    
    # 检查是否包含时间查询关键词
    contains_time_keyword = any(keyword in query.lower() for keyword in time_keywords)
    
    # 检查是否包含排除词
    contains_exclude_keyword = any(keyword in query.lower() for keyword in exclude_keywords)
    
    # 如果包含时间查询关键词但不包含排除词，则认为是时间查询
    if contains_time_keyword and not contains_exclude_keyword:
        # 进一步检查是否是明确询问当前时间的查询
        explicit_time_queries = ["现在几点", "现在是几点", "现在时间", "当前时间", "现在日期", "今天日期", 
                               "what time is it", "current time", "what is the time now"]
        for explicit_query in explicit_time_queries:
            if explicit_query in query.lower():
                return True
        
        # 如果查询很短并且只包含时间关键词，也认为是时间查询
        if len(query) < 15 and ("时间" in query or "几点" in query or "日期" in query):
            return True
    
    return False

def get_current_time():
    """获取当前时间，格式化为易读的字符串"""
    # 获取北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(beijing_tz)
    
    # 格式化时间字符串
    time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日"
    }
    weekday = weekday_map[now.weekday()]
    
    return f"{time_str} {weekday}"

def generate_mock_search_results(query):
    """生成模拟的搜索结果数据"""
    # 检查是否是天气相关查询
    weather_keywords = ["天气", "气温", "下雨", "晴天", "阴天", "雨天", "雪", "温度", "气候"]
    is_weather_query = any(keyword in query for keyword in weather_keywords)
    
    if is_weather_query:
        # 获取当前日期
        from datetime import datetime
        current_date = datetime.now().strftime("%Y年%m月%d日")
        
        # 为天气查询生成更真实的模拟数据
        mock_results = {
            "query": query,
            "search_results": [
                {
                    "title": f"【上海天气预报】上海今日天气 {current_date}",
                    "link": "https://example.com/shanghai-weather",
                    "snippet": f"{current_date} 上海天气：晴转多云，气温18-25℃，东南风3-4级，空气质量良好，紫外线强度中等。建议穿着薄外套或长袖衬衫。"
                },
                {
                    "title": f"全国天气预报_中国天气网",
                    "link": "https://example.com/china-weather",
                    "snippet": f"今日全国天气：北方地区多云转晴，南方地区有小到中雨。华北、东北地区气温回升，西南地区有强对流天气，注意防范。"
                },
                {
                    "title": f"天气预报查询_未来一周天气预报",
                    "link": "https://example.com/weather-forecast",
                    "snippet": f"未来一周天气预报：周三至周四全国大部地区天气晴好，周五开始南方将有一次降水过程，华南地区有中到大雨，局部暴雨。"
                }
            ],
            "detailed_content": {
                "https://example.com/shanghai-weather": f"""
{current_date} 上海天气详情：
今日天气：晴转多云
气温：18-25℃
风向风力：东南风3-4级
空气质量：良好，AQI 65
紫外线强度：中等
生活指数：
- 穿衣指数：建议穿薄外套或长袖衬衫
- 洗车指数：较适宜
- 感冒指数：低发期，无明显降温
- 运动指数：适宜户外运动
未来三天预报：
- 明天：多云，19-26℃
- 后天：多云转小雨，17-23℃
- 大后天：小雨，16-21℃
                """,
                "https://example.com/china-weather": f"""
{current_date} 全国天气概况：
北方地区：
- 华北：晴到多云，14-25℃，空气质量良
- 东北：多云，早晚温差大，8-20℃
- 西北：晴，气温回升，12-28℃

南方地区：
- 华东：多云有阵雨，18-26℃
- 华南：小到中雨，局部大雨，22-29℃
- 西南：多云转阴，有阵雨或雷雨，15-24℃

主要城市天气：
- 北京：晴，15-27℃
- 上海：晴转多云，18-25℃
- 广州：小雨，23-28℃
- 深圳：中雨，22-27℃
- 成都：多云，16-22℃
- 武汉：多云，17-25℃
                """,
                "https://example.com/weather-forecast": f"""
未来一周全国天气预报（{current_date}起）：

第1天：全国大部地区天气晴好，华北、东北气温回升，西南地区多云。
第2天：华北、东北继续晴好，华南地区云量增多。
第3天：南方将有一次降水过程开始，华南地区有小到中雨。
第4天：降水范围扩大，华南、华东南部有中到大雨，局部暴雨。
第5天：降水减弱，华南仍有小到中雨，其他地区多云。
第6天：全国大部地区转为多云或晴，气温回升。
第7天：新一轮冷空气将影响北方地区，带来降温和大风天气。

温馨提示：
1. 南方地区公众需关注强降水天气，注意防范城市内涝和山洪地质灾害。
2. 北方地区公众需关注气温变化，适时调整着装。
3. 雷雨天气出行请携带雨具，注意交通安全。
                """
            }
        }
    else:
        # 为非天气查询生成通用模拟数据
        mock_results = {
            "query": query,
            "search_results": [
                {
                    "title": f"关于 {query} 的最新研究",
                    "link": "https://example.com/research",
                    "snippet": f"这是关于 {query} 的最新研究成果，包含了最新的进展和发现..."
                },
                {
                    "title": f"{query} 的基本概念和应用",
                    "link": "https://example.com/concepts",
                    "snippet": f"本文介绍了 {query} 的基本概念、原理以及在各个领域的应用..."
                },
                {
                    "title": f"{query} 的历史发展",
                    "link": "https://example.com/history",
                    "snippet": f"{query} 的发展历程可以追溯到几十年前，经历了多个重要的里程碑..."
                }
            ],
            "detailed_content": {
                "https://example.com/research": f"这是一篇关于 {query} 的详细研究报告，包含了最新的研究方法、数据分析和结论...",
                "https://example.com/concepts": f"本文详细介绍了 {query} 的核心概念、基本原理、技术实现以及在不同行业的应用案例...",
                "https://example.com/history": f"本文回顾了 {query} 的完整发展历程，从早期的理论构想到现代的实际应用，包括关键人物、重要事件和技术突破..."
            }
        }
    
    # 添加格式化的提示词
    processor = ResponseProcessor()
    formatted_prompt = processor.format_search_results(
        query=query,
        search_results=mock_results["search_results"],
        detailed_content=mock_results["detailed_content"]
    )
    mock_results["formatted_prompt"] = formatted_prompt
    
    return mock_results

def test_search_engine(query=None, search_engine="baidu", num_results=5, fetch_content=True, verbose=False):
    """测试搜索引擎的搜索结果"""
    # 如果没有提供查询，使用默认查询
    if query is None:
        query = "量子计算最新进展"
    
    print(f"查询: {query}")
    print(f"\n搜索引擎: {search_engine}")
    
    # 创建搜索引擎实例
    engine = WebSearch(search_engine=search_engine)
    
    # 执行搜索
    print("\n正在搜索...\n")
    search_results = engine.search(query, num_results=num_results)
    
    # 显示搜索结果
    print("=== 搜索结果 ===")
    for i, result in enumerate(search_results, 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['link']}")
        print(f"   {result['snippet'][:100]}...\n" if len(result['snippet']) > 100 else f"   {result['snippet']}\n")
    
    # 如果需要获取详细内容
    detailed_content = {}
    if fetch_content:
        print("\n正在获取详细内容...\n")
        try:
            # 只获取前两个结果的详细内容
            for i, result in enumerate(search_results[:2]):
                try:
                    content = engine.fetch_content(result['link'])
                    if content:
                        content_preview = content[:500] + "..." if len(content) > 500 else content
                        detailed_content[result['link']] = content
                        print(f"获取内容成功: {result['link']}")
                except Exception as e:
                    print(f"Error fetching content from {result['link']}: {str(e)}")
                    # 不添加失败的内容到detailed_content
        except Exception as e:
            print(f"获取详细内容时出错: {str(e)}")
    
    # 使用响应处理器格式化结果
    processor = ResponseProcessor()
    formatted_prompt = processor.format_search_results(
        query=query,
        search_results=search_results,
        detailed_content=detailed_content
    )
    
    # 如果需要显示详细信息
    if verbose:
        print("\n=== 格式化的提示词 ===")
        print(formatted_prompt)
    
    return {
        "query": query,
        "search_results": search_results,
        "detailed_content": detailed_content,
        "formatted_prompt": formatted_prompt
    }

def test_llm_response(query=None, search_engine="baidu", num_results=5, fetch_content=False, 
                      model=None, api_url="http://localhost:5005/search", 
                      temperature=0.7, max_tokens=2048, verbose=False, mock=False):
    """测试LLM对搜索结果的利用情况"""
    start_time = time.time()
    
    # 检查是否为时间查询
    if is_time_query(query):
        current_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n这是一个时间查询。当前时间是: {current_time}")
        return
    
    print(f"\n正在测试LLM对搜索结果的利用情况...")
    print(f"查询: {query}")
    print(f"搜索引擎: {search_engine}")
    print(f"结果数量: {num_results}")
    if model:
        print(f"使用指定模型: {model}")
    else:
        print("使用自动检测的最佳模型")
    
    # 初始化LLM客户端
    client = LLMWebSearchClient(
        search_api_url=api_url,
        model_name=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    # 检查是否使用模拟数据
    if mock:
        print("\n使用模拟搜索数据...\n")
        search_data = generate_mock_search_results(query)
    else:
        # 使用真实搜索结果
        print("\n正在进行网络搜索...\n")
        try:
            # 直接使用test_search_engine函数获取搜索结果
            search_data = test_search_engine(
                query=query, 
                search_engine=search_engine, 
                num_results=num_results, 
                fetch_content=fetch_content, 
                verbose=False
            )
            
            # 检查是否有错误
            if "error" in search_data:
                print(f"搜索出错: {search_data['error']}")
                return {
                    "query": query,
                    "error": search_data['error'],
                    "llm_response": f"搜索出错: {search_data['error']}"
                }
        except Exception as e:
            error_msg = f"搜索出错: {str(e)}"
            print(error_msg)
            return {
                "query": query,
                "error": error_msg,
                "llm_response": f"搜索出错: {str(e)}"
            }
    
    # 显示搜索结果
    print("=== 搜索结果 ===")
    for i, result in enumerate(search_data["search_results"], 1):
        print(f"{i}. {result['title']}")
        print(f"   {result['link']}")
        if "snippet" in result:
            snippet = result["snippet"]
            print(f"   {snippet[:100]}..." if len(snippet) > 100 else f"   {snippet}")
        print()  # 添加空行增加可读性
    
    # 显示格式化的提示词
    if verbose:
        print("\n=== 提示词 ===")
        print(search_data["formatted_prompt"])
    else:
        print("\n=== 提示词 ===")
        print("(使用 --verbose 参数查看完整提示词)")
    
    # 查询LLM
    print("\n正在查询LLM...\n")
    try:
        # 添加超时处理
        import time
        start_time = time.time()
        llm_response = client.query_local_llm(search_data["formatted_prompt"])
        end_time = time.time()
        
        print("=== LLM回答 ===")
        print(llm_response)
        print(f"\n响应时间: {end_time - start_time:.2f}秒")
        
        return {
            "query": query,
            "search_data": search_data,
            "llm_response": llm_response,
            "response_time": end_time - start_time
        }
    except Exception as e:
        error_msg = f"查询LLM时出错: {str(e)}"
        print(error_msg)
        print("=== LLM回答 ===")
        print(f"错误: {str(e)}")
        print("\n可能的原因:")
        print("1. LLM服务器未启动或无法访问")
        print("2. API地址不正确")
        print("3. 模型名称不正确或模型未下载")
        print("4. 网络连接问题")
        print("\n建议:")
        print(f"- 确认LLM服务器已启动并运行在 {api_url}")
        print(f"- 确认模型 '{model}' 已正确安装")
        print("- 检查网络连接")
        
        return {
            "query": query,
            "search_data": search_data,
            "error": error_msg,
            "llm_response": f"错误: {str(e)}"
        }

def compare_search_engines(query=None, engines=None, num_results=5):
    """比较不同搜索引擎的结果"""
    if query is None:
        query = "量子计算最新进展"
    
    if engines is None:
        engines = ["google", "bing", "baidu"]
    
    print(f"查询: {query}")
    print(f"比较搜索引擎: {', '.join(engines)}")
    
    results = {}
    
    for engine in engines:
        print(f"\n正在使用 {engine} 搜索...\n")
        try:
            search_engine = WebSearch(search_engine=engine)
            search_results = search_engine.search(query, num_results=num_results)
            
            results[engine] = search_results
            
            print(f"=== {engine.capitalize()} 搜索结果 ===")
            for i, result in enumerate(search_results, 1):
                print(f"{i}. {result['title']}")
                print(f"   {result['link']}")
                print(f"   {result['snippet'][:100]}...\n")
        except Exception as e:
            print(f"{engine} 搜索出错: {str(e)}")
            results[engine] = {"error": str(e)}
    
    # 比较结果
    print("\n=== 结果比较 ===")
    print(f"查询: {query}")
    
    for engine in engines:
        if isinstance(results[engine], list):
            print(f"{engine.capitalize()}: 返回 {len(results[engine])} 个结果")
        else:
            print(f"{engine.capitalize()}: 搜索出错 - {results[engine]['error']}")
    
    return {
        "query": query,
        "results": results
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM联网搜索插件测试工具")
    parser.add_argument("--mode", type=str, default="search", choices=["search", "llm", "compare"],
                        help="测试模式: search(测试搜索引擎), llm(测试LLM响应), compare(比较搜索引擎)")
    parser.add_argument("--query", type=str, default="量子计算最新进展",
                        help="要测试的查询 (默认: 量子计算最新进展)")
    parser.add_argument("--verbose", action="store_true", help="显示详细信息，包括完整提示词")
    parser.add_argument("--search-engine", type=str, default="baidu", choices=["google", "bing", "baidu"],
                        help="使用的搜索引擎 (默认: baidu)")
    parser.add_argument("--engines", type=str, nargs="+", default=["google", "bing", "baidu"],
                        help="比较模式下要比较的搜索引擎列表 (默认: google bing baidu)")
    parser.add_argument("--mock", action="store_true", help="使用模拟搜索数据，不进行实际搜索")
    parser.add_argument("--model", type=str, default=None, 
                        help="指定使用的LLM模型名称 (默认: 自动检测最佳模型)")
    parser.add_argument("--api-url", type=str, default="http://localhost:5005/search", 
                        help="指定搜索API的URL (默认: http://localhost:5005/search)")
    parser.add_argument("--temperature", type=float, default=0.7, 
                        help="LLM生成的温度参数 (默认: 0.7)")
    parser.add_argument("--num-results", type=int, default=5, 
                        help="搜索结果数量 (默认: 5)")
    parser.add_argument("--fetch-content", action="store_true", help="获取详细网页内容")
    parser.add_argument("--max-tokens", type=int, default=2048, 
                        help="LLM生成的最大长度 (默认: 2048)")
    args = parser.parse_args()
    
    if args.mode == "search":
        test_search_engine(
            query=args.query,
            search_engine=args.search_engine,
            num_results=args.num_results,
            fetch_content=args.fetch_content,
            verbose=args.verbose
        )
    elif args.mode == "llm":
        test_llm_response(
            query=args.query, 
            search_engine=args.search_engine, 
            num_results=args.num_results, 
            fetch_content=args.fetch_content, 
            model=args.model,
            api_url=args.api_url,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            verbose=args.verbose,
            mock=args.mock
        )
    elif args.mode == "compare":
        compare_search_engines(
            query=args.query,
            engines=args.engines,
            num_results=args.num_results
        )
