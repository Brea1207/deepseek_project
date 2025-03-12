#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM联网搜索插件交互式测试工具
"""

from test_utils import test_search_engine, test_llm_response, compare_search_engines
import os
import sys

def clear_screen():
    """清除终端屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印工具标题"""
    print("\n" + "=" * 50)
    print("       LLM联网搜索插件交互式测试工具")
    print("=" * 50)

def interactive_menu():
    """显示交互式菜单并处理用户输入"""
    clear_screen()
    print_header()
    print("\n请选择功能:")
    print("1. 测试搜索引擎 - 测试不同搜索引擎的搜索结果")
    print("2. 测试LLM响应 - 测试LLM对搜索结果的处理能力")
    print("3. 比较搜索引擎 - 比较不同搜索引擎的结果差异")
    print("0. 退出程序")
    
    try:
        choice = input("\n请输入选项 (0-3): ")
        
        if choice == "1":
            test_search_engine_interactive()
        elif choice == "2":
            test_llm_response_interactive()
        elif choice == "3":
            compare_search_engines_interactive()
        elif choice == "0":
            print("\n谢谢使用，再见！")
            return False
        else:
            print("\n无效选择，请输入0-3之间的数字")
            input("\n按Enter键继续...")
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        input("\n按Enter键继续...")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        input("\n按Enter键继续...")
    
    return True

def test_search_engine_interactive():
    """交互式测试搜索引擎"""
    clear_screen()
    print_header()
    print("\n=== 测试搜索引擎 ===")
    
    try:
        query = input("\n请输入搜索查询 (默认: 量子计算最新进展): ").strip() or "量子计算最新进展"
        
        print("\n可选搜索引擎:")
        print("1. baidu  - 百度搜索")
        print("2. google - 谷歌搜索")
        print("3. bing   - 必应搜索")
        engine_choice = input("\n请选择搜索引擎 (1-3, 默认: 1): ").strip() or "1"
        
        search_engine_map = {"1": "baidu", "2": "google", "3": "bing"}
        search_engine = search_engine_map.get(engine_choice, "baidu")
        
        num_results = input("\n请输入结果数量 (默认: 3): ").strip()
        num_results = int(num_results) if num_results.isdigit() else 3
        
        fetch_content = input("\n是否获取详细内容 (y/n, 默认: y): ").lower() != "n"
        verbose = input("\n是否显示详细信息 (y/n, 默认: n): ").lower() == "y"
        
        print("\n开始测试搜索引擎...")
        test_search_engine(
            query=query,
            search_engine=search_engine,
            num_results=num_results,
            fetch_content=fetch_content,
            verbose=verbose
        )
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n测试搜索引擎时出错: {str(e)}")

def test_llm_response_interactive():
    """交互式测试LLM响应"""
    clear_screen()
    print_header()
    print("\n=== 测试LLM响应 ===")
    
    try:
        query = input("\n请输入搜索查询 (默认: 量子计算最新进展): ").strip() or "量子计算最新进展"
        
        print("\n可选搜索引擎:")
        print("1. baidu  - 百度搜索")
        print("2. google - 谷歌搜索")
        print("3. bing   - 必应搜索")
        engine_choice = input("\n请选择搜索引擎 (1-3, 默认: 1): ").strip() or "1"
        
        search_engine_map = {"1": "baidu", "2": "google", "3": "bing"}
        search_engine = search_engine_map.get(engine_choice, "baidu")
        
        num_results = input("\n请输入结果数量 (默认: 3): ").strip()
        num_results = int(num_results) if num_results.isdigit() else 3
        
        use_mock_data = input("\n是否使用模拟数据 (y/n, 默认: n): ").lower() == "y"
        
        print("\n可选LLM模型:")
        print("1. deepseek-r1:1.5b - 轻量级模型")
        print("2. llama3:8b        - 中等大小模型")
        print("3. qwen:14b         - 较大模型")
        print("4. 自定义模型")
        model_choice = input("\n请选择LLM模型 (1-4, 默认: 1): ").strip() or "1"
        
        model_map = {
            "1": "deepseek-r1:1.5b",
            "2": "llama3:8b",
            "3": "qwen:14b"
        }
        
        if model_choice in model_map:
            model = model_map[model_choice]
        else:
            model = input("\n请输入自定义模型名称: ").strip() or "deepseek-r1:1.5b"
        
        api_url = input("\n请输入API URL (默认: http://localhost:5003): ").strip() or "http://localhost:5003"
        
        temperature = input("\n请输入温度参数 (0.0-1.0, 默认: 0.7): ").strip() or "0.7"
        temperature = float(temperature)
        
        max_tokens = input("\n请输入最大生成长度 (默认: 2048): ").strip()
        max_tokens = int(max_tokens) if max_tokens.isdigit() else 2048
        
        verbose = input("\n是否显示详细信息 (y/n, 默认: n): ").lower() == "y"
        
        print("\n开始测试LLM响应...")
        test_llm_response(
            query=query,
            search_engine=search_engine,
            num_results=num_results,
            use_mock_data=use_mock_data,
            model=model,
            api_url=api_url,
            temperature=temperature,
            max_tokens=max_tokens,
            verbose=verbose
        )
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n测试LLM响应时出错: {str(e)}")

def compare_search_engines_interactive():
    """交互式比较搜索引擎"""
    clear_screen()
    print_header()
    print("\n=== 比较搜索引擎 ===")
    
    try:
        query = input("\n请输入搜索查询 (默认: 量子计算最新进展): ").strip() or "量子计算最新进展"
        
        print("\n可选搜索引擎:")
        print("1. google - 谷歌搜索")
        print("2. bing   - 必应搜索")
        print("3. baidu  - 百度搜索")
        
        engines_input = input("\n请选择要比较的搜索引擎编号，用空格分隔 (默认: 1 2 3): ").strip() or "1 2 3"
        engine_choices = engines_input.split()
        
        engine_map = {"1": "google", "2": "bing", "3": "baidu"}
        engines = [engine_map.get(choice, "baidu") for choice in engine_choices]
        
        num_results = input("\n请输入每个引擎的结果数量 (默认: 3): ").strip()
        num_results = int(num_results) if num_results.isdigit() else 3
        
        print("\n开始比较搜索引擎...")
        compare_search_engines(
            query=query,
            engines=engines,
            num_results=num_results
        )
    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n比较搜索引擎时出错: {str(e)}")

if __name__ == "__main__":
    try:
        print("欢迎使用LLM联网搜索插件交互式测试工具！")
        
        running = True
        while running:
            running = interactive_menu()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n程序发生错误: {str(e)}")
        sys.exit(1)
