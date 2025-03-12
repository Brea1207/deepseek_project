from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import os
import requests
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from search_engine import WebSearch
from response_processor import ResponseProcessor
import traceback
import time

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 全局配置变量
config = {
    'default_search_engine': 'google',
    'default_num_results': 5,
    'default_fetch_content': False,
    'time_sources': [
        "https://www.timeanddate.com/worldclock/china/beijing",
        "https://www.worldtimeserver.com/current_time_in_CN.aspx",
        "https://time.is/Beijing"
    ],
    'default_timezone': 'Asia/Shanghai',
    'enable_detailed_logging': False,
    'max_content_length': 1000,
    'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # LLM配置
    'default_llm_model': 'deepseek-r1:1.5b',
    'default_temperature': 0.7,
    'default_max_tokens': 2048
}

# 初始化组件
# 从环境变量获取搜索引擎设置，默认为 google
search_engine_name = os.environ.get('SEARCH_ENGINE', config['default_search_engine']).lower()
if search_engine_name not in ['google', 'bing', 'baidu']:
    print(f"警告：不支持的搜索引擎 '{search_engine_name}'，使用默认的 'google'")
    search_engine_name = 'google'

search_engine = WebSearch(search_engine=search_engine_name)
response_processor = ResponseProcessor()

def get_system_time():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    timezone_name = current_time.astimezone().tzname()
    return f"当前系统时间是：{formatted_time} {timezone_name}"

@app.route('/search', methods=['POST'])
def search():
    """基于查询执行网络搜索并返回格式化结果的端点"""
    try:
        data = request.json
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing required parameter: query"}), 400
        
        query = data['query']
        num_results = data.get('num_results', config.get('default_num_results', 5))
        fetch_content = data.get('fetch_content', config.get('default_fetch_content', False))
        search_engine_name = data.get('search_engine', config.get('default_search_engine', 'google'))
        
        # 获取LLM配置
        llm_model = data.get('llm_model', config.get('default_llm_model', 'deepseek-r1:1.5b'))
        temperature = data.get('temperature', config.get('default_temperature', 0.7))
        max_tokens = data.get('max_tokens', config.get('default_max_tokens', 2048))
        
        # 如果需要，更新搜索引擎
        if search_engine.search_engine != search_engine_name:
            search_engine.search_engine = search_engine_name
        
        # 执行搜索
        try:
            search_results = search_engine.search(query, num_results)
        except Exception as e:
            return jsonify({"error": f"搜索时出错: {str(e)}"}), 500
        
        # 如果请求，获取详细内容
        detailed_content = {}
        if fetch_content and search_results:
            # 获取所有搜索结果的详细内容，而不是限制为前3个
            for result in search_results:
                url = result['link']
                
                # 检查是否为模拟 URL (example.com)
                if 'example.com' in url:
                    # 为模拟 URL 创建模拟内容
                    if 'search-results' in url:
                        detailed_content[url] = f"这是关于 '{query}' 的模拟搜索结果页面。"
                    elif 'weather' in url:
                        detailed_content[url] = f"模拟天气信息：无法提供 '{query}' 的准确天气信息。"
                    elif 'time' in url:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        detailed_content[url] = f"当前时间是 {current_time}。"
                    else:
                        detailed_content[url] = f"这是一个模拟内容页面。查询: {query}"
                else:
                    # 正常获取实际 URL 的内容
                    try:
                        content = search_engine.fetch_content(url)
                        detailed_content[url] = content
                    except Exception as e:
                        detailed_content[url] = f"无法获取内容: {str(e)}"
        
        # 格式化结果供LLM使用
        try:
            formatted_response = response_processor.create_prompt_with_search_results(
                query, search_results, detailed_content if fetch_content else None
            )
        except Exception as e:
            return jsonify({"error": f"格式化结果时出错: {str(e)}"}), 500
        
        return jsonify({
            "query": query,
            "search_results": search_results,
            "detailed_content": detailed_content if fetch_content else {},
            "formatted_response": formatted_response,
            "llm_config": {
                "model": llm_model,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/current_time', methods=['GET'])
def get_current_time():
    """获取当前时间的端点"""
    try:
        # 使用配置中的时间源
        time_sources = config.get('time_sources', [
            "https://www.timeanddate.com/worldclock/china/beijing",
            "https://www.worldtimeserver.com/current_time_in_CN.aspx",
            "https://time.is/Beijing"
        ])
        
        current_time_info = {}
        
        # 尝试从第一个可用的源获取时间
        for source in time_sources:
            try:
                headers = {
                    "User-Agent": config.get('user_agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                }
                response = requests.get(source, headers=headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 针对不同的时间源使用不同的解析逻辑
                    if "timeanddate" in source:
                        time_element = soup.select_one('#qlook')
                        if time_element:
                            # 清理时间文本，移除"Fullscreen"等额外文本
                            time_text = time_element.get_text().strip()
                            # 分割时间文本，提取有用部分
                            time_parts = time_text.split('Fullscreen')
                            clean_time = time_parts[0].strip()
                            
                            # 使用字典映射星期
                            weekdays = {
                                "Monday": "一",
                                "Tuesday": "二",
                                "Wednesday": "三",
                                "Thursday": "四",
                                "Friday": "五",
                                "Saturday": "六",
                                "Sunday": "日"
                            }
                            
                            weekday = ""
                            weekday_cn = ""
                            for day, day_cn in weekdays.items():
                                if day in clean_time:
                                    weekday = day
                                    weekday_cn = day_cn
                                    break
                            
                            current_time_info['source'] = "timeanddate.com"
                            current_time_info['time'] = clean_time
                            current_time_info['url'] = source
                            if weekday:
                                current_time_info['weekday'] = weekday
                                current_time_info['weekday_cn'] = weekday_cn
                            break
                    elif "worldtimeserver" in source:
                        time_element = soup.select_one('#theTime')
                        if time_element:
                            time_text = time_element.get_text().strip()
                            # 清理时间文本
                            current_time_info['source'] = "worldtimeserver.com"
                            current_time_info['time'] = time_text
                            current_time_info['url'] = source
                            break
                    elif "time.is" in source:
                        time_element = soup.select_one('#clock')
                        if time_element:
                            time_text = time_element.get_text().strip()
                            current_time_info['source'] = "time.is"
                            current_time_info['time'] = time_text
                            current_time_info['url'] = source
                            break
            except Exception as e:
                print(f"Error fetching time from {source}: {e}")
                continue
        
        # 如果无法从在线源获取时间，使用系统时间作为后备
        if not current_time_info:
            current_time_info = {
                'source': 'system',
                'time': get_system_time(),
                'note': '无法从在线源获取时间，使用系统时间作为后备'
            }
        
        return jsonify(current_time_info)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """简单的健康检查端点"""
    return jsonify({"status": "healthy"})

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    """配置页面，允许用户调整搜索和时间获取参数"""
    global config
    
    # 处理表单提交
    if request.method == 'POST':
        # 更新配置
        config['default_search_engine'] = request.form.get('default_search_engine', 'google')
        config['default_num_results'] = int(request.form.get('default_num_results', 5))
        config['default_fetch_content'] = request.form.get('default_fetch_content') == 'on'
        config['default_timezone'] = request.form.get('default_timezone', 'Asia/Shanghai')
        config['enable_detailed_logging'] = request.form.get('enable_detailed_logging') == 'on'
        config['max_content_length'] = int(request.form.get('max_content_length', 1000))
        config['user_agent'] = request.form.get('user_agent', config['user_agent'])
        
        # 更新LLM配置
        config['default_llm_model'] = request.form.get('default_llm_model', 'deepseek-r1:1.5b')
        config['default_temperature'] = float(request.form.get('default_temperature', 0.7))
        config['default_max_tokens'] = int(request.form.get('default_max_tokens', 2048))
        
        # 处理时间源
        time_sources = request.form.get('time_sources', '').strip().split('\n')
        config['time_sources'] = [source.strip() for source in time_sources if source.strip()]
        
        return redirect(url_for('config_page'))
    
    # 准备时区列表
    timezones = [
        'Asia/Shanghai', 'America/New_York', 'Europe/London', 'Australia/Sydney', 
        'Pacific/Auckland', 'Europe/Paris', 'America/Los_Angeles', 'Asia/Tokyo'
    ]
    
    # 准备LLM模型列表
    llm_models = [
        'deepseek-r1:1.5b', 'deepseek-r1:7b', 'deepseek-r1:67b', 
        'llama3:8b', 'llama3:70b', 
        'qwen:7b', 'qwen:14b', 'qwen:72b',
        'mistral:7b', 'mixtral:8x7b'
    ]
    
    # 渲染配置页面，使用新的模板文件
    return render_template('config.html', config=config, timezones=timezones, llm_models=llm_models, current_year=datetime.now().year)

@app.route('/llm', methods=['GET', 'POST'])
def llm_page():
    query = ""
    response_text = ""
    error_message = ""
    processing_time = 0
    search_results = []
    
    # 默认参数
    model = config.get('default_llm_model', 'deepseek-r1:1.5b')
    temperature = config.get('default_temperature', 0.7)
    max_tokens = config.get('default_max_tokens', 2048)
    use_web_search = False
    num_results = config.get('default_num_results', 5)
    search_engine = config.get('default_search_engine', 'google')
    llm_type = "ollama"  # 默认使用Ollama
    
    # 获取可用的LLM模型
    api_models = ["gpt-3.5-turbo", "gpt-4", "claude-instant-1", "claude-2", "gemini-pro"]
    ollama_models = ["deepseek-r1:1.5b"]
    
    if request.method == 'POST':
        try:
            query = request.form.get('query', '')
            model = request.form.get('model', 'gpt-3.5-turbo')
            temperature = float(request.form.get('temperature', 0.7))
            max_tokens = int(request.form.get('max_tokens', 2048))
            use_web_search = 'use_web_search' in request.form
            num_results = int(request.form.get('num_results', 5))
            search_engine = request.form.get('search_engine', 'google')
            llm_type = request.form.get('llm_type', 'api')
            
            if not query:
                error_message = "请输入查询内容 | Please enter a query"
                return render_template('llm.html', response_text=response_text, query=query, error_message=error_message, 
                                     api_models=api_models, ollama_models=ollama_models, model=model, temperature=temperature, max_tokens=max_tokens, 
                                     processing_time=processing_time, use_web_search=use_web_search, 
                                     num_results=num_results, search_engine=search_engine, llm_type=llm_type,
                                     search_results=search_results, current_year=datetime.now().year)
            
            # 处理时间查询的特殊情况
            time_keywords = ["current time", "current date", "what time", "what date", "今天日期", "现在时间", "当前时间"]
            if any(keyword in query.lower() for keyword in time_keywords):
                # 尝试通过网络获取时间
                try:
                    # 使用百度搜索获取时间
                    from llm_client_example import LLMWebSearchClient
                    client = LLMWebSearchClient(llm_type=llm_type)
                    time_search_results = client.search_web("current time and date", 3, True, "baidu")
                    
                    if time_search_results and len(time_search_results) > 0:
                        # 从搜索结果中提取时间信息
                        time_info = "\n".join([
                            f"{result['title']}: {result['snippet']}"
                            for result in time_search_results
                            if "title" in result and "snippet" in result
                        ])
                        
                        response_text = f"根据网络搜索结果，当前的时间和日期信息如下：\n\n{time_info}"
                        processing_time = 1.0
                    else:
                        # 如果网络搜索失败，回退到系统时间
                        response_text = get_system_time()
                        processing_time = 0.5
                except Exception as e:
                    # 如果出现异常，回退到系统时间
                    response_text = get_system_time()
                    processing_time = 0.5
            else:
                # 常规查询处理
                start_time = time.time()
                
                from llm_client_example import LLMWebSearchClient
                # 如果model为None或为空字符串，将使用自动检测的最佳模型
                if not model:
                    client = LLMWebSearchClient(temperature=temperature, max_tokens=max_tokens, llm_type=llm_type)
                    print(f"使用自动检测的模型: {client.model_name}")
                else:
                    client = LLMWebSearchClient(model_name=model, temperature=temperature, max_tokens=max_tokens, llm_type=llm_type)
                    print(f"使用指定的模型: {model}")
                
                if use_web_search:
                    # 使用网络搜索增强回答
                    result = client.answer_with_web_search(query, num_results=num_results, fetch_content=True, search_engine=search_engine)
                    response_text = result.get('answer', '')
                    search_results = result.get('search_results', [])
                else:
                    # 直接使用LLM回答
                    response_text = client.query_llm(query)
                
                processing_time = time.time() - start_time
                
        except Exception as error:
            error_message = f"发生错误 | An error occurred: {str(error)}"
            print(error_message)
            print(traceback.format_exc())
    
    return render_template('llm.html', response_text=response_text, query=query, error_message=error_message, 
                         api_models=api_models, ollama_models=ollama_models, model=model, temperature=temperature, max_tokens=max_tokens, 
                         processing_time=processing_time, use_web_search=use_web_search, 
                         num_results=num_results, search_engine=search_engine, llm_type=llm_type,
                         search_results=search_results, current_year=datetime.now().year)

@app.route('/search_demo', methods=['GET', 'POST'])
def search_demo():
    """搜索演示页面，允许用户尝试搜索功能"""
    search_results = None
    query = ""
    error_message = None
    processing_time = 0
    
    if request.method == 'POST':
        try:
            query = request.form.get('query', '').strip()
            
            if not query:
                error_message = "请输入搜索查询 | Please enter a search query"
            else:
                # 记录开始时间
                start_time = time.time()
                
                # 执行搜索
                search_results = search_engine.search(query, config.get('default_num_results', 5))
                
                # 计算处理时间
                processing_time = time.time() - start_time
                
        except Exception as e:
            import traceback
            error_message = f"搜索时出错: {str(e)}"
            print(error_message)
            print(traceback.format_exc())
    
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>搜索演示 | Search Demo</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        <style>
            :root {
                --primary-color: #4a6fa5;
                --secondary-color: #6f8ab7;
                --accent-color: #e67e22;
                --background-color: #f5f7fa;
                --card-background: #ffffff;
                --text-color: #333333;
                --text-light: #6c757d;
                --border-color: #e1e4e8;
                --success-color: #27ae60;
                --error-color: #e74c3c;
                --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: var(--text-color);
                background-color: var(--background-color);
                margin: 0;
                padding: 0;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            
            header {
                background-color: var(--primary-color);
                color: white;
                padding: 1rem 0;
                box-shadow: var(--shadow);
            }
            
            header .container {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                display: flex;
                align-items: center;
                font-size: 1.5rem;
                font-weight: bold;
            }
            
            .logo i {
                margin-right: 10px;
                font-size: 1.8rem;
            }
            
            nav ul {
                display: flex;
                list-style: none;
                margin: 0;
                padding: 0;
            }
            
            nav li {
                margin-left: 20px;
            }
            
            nav a {
                color: white;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.3s;
            }
            
            nav a:hover {
                color: var(--accent-color);
            }
            
            .card {
                background-color: var(--card-background);
                border-radius: 8px;
                box-shadow: var(--shadow);
                padding: 20px;
                margin-bottom: 20px;
            }
            
            .search-form {
                margin-bottom: 20px;
            }
            
            .search-form input {
                width: calc(100% - 120px);
                padding: 12px;
                border: 2px solid var(--border-color);
                border-radius: 4px 0 0 4px;
                font-size: 1rem;
            }
            
            .search-form button {
                width: 120px;
                background-color: var(--primary-color);
                color: white;
                border: none;
                padding: 12px;
                border-radius: 0 4px 4px 0;
                cursor: pointer;
                font-size: 1rem;
                transition: background-color 0.3s;
            }
            
            .search-form button:hover {
                background-color: var(--secondary-color);
            }
            
            .search-results {
                margin-top: 20px;
            }
            
            .result-item {
                padding: 15px;
                border-bottom: 1px solid var(--border-color);
            }
            
            .result-item:last-child {
                border-bottom: none;
            }
            
            .result-title {
                color: var(--primary-color);
                font-size: 1.2rem;
                margin-bottom: 5px;
            }
            
            .result-link {
                color: #1a0dab;
                text-decoration: none;
                display: block;
                margin-bottom: 5px;
                word-break: break-all;
            }
            
            .result-link:hover {
                text-decoration: underline;
            }
            
            .result-snippet {
                color: #545454;
                font-size: 0.9rem;
            }
            
            .error-message {
                background-color: #ffebee;
                color: var(--error-color);
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
            }
            
            .stats {
                display: flex;
                justify-content: space-between;
                margin-top: 10px;
                font-size: 0.9rem;
                color: #666;
            }
            
            footer {
                background-color: var(--primary-color);
                color: white;
                text-align: center;
                padding: 1rem 0;
                margin-top: 2rem;
            }
            
            .btn-group {
                margin-top: 20px;
                display: flex;
                gap: 10px;
            }
            
            .btn {
                display: inline-block;
                background-color: var(--primary-color);
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                text-decoration: none;
                font-weight: 500;
                transition: background-color 0.3s;
            }
            
            .btn:hover {
                background-color: var(--secondary-color);
            }
            
            .btn-secondary {
                background-color: var(--accent-color);
            }
            
            .btn-secondary:hover {
                background-color: #d35400;
            }
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <div class="logo">
                    <i class="fas fa-robot"></i>
                    <span>LLM Web Search Plugin</span>
                </div>
                <nav>
                    <ul>
                        <li><a href="/"><i class="fas fa-home"></i> 首页 | Home</a></li>
                        <li><a href="/llm"><i class="fas fa-robot"></i> LLM交互 | LLM Chat</a></li>
                        <li><a href="/config"><i class="fas fa-cog"></i> 配置 | Config</a></li>
                    </ul>
                </nav>
            </div>
        </header>
        
        <div class="container">
            <div class="card">
                <h2><i class="fas fa-search"></i> 搜索演示 | Search Demo</h2>
                
                {% if error_message %}
                <div class="error-message">
                    {{ error_message }}
                </div>
                {% endif %}
                
                <form class="search-form" method="POST" action="/search_demo">
                    <div style="display: flex;">
                        <input type="text" name="query" placeholder="输入搜索查询... | Enter search query..." value="{{ query }}">
                        <button type="submit"><i class="fas fa-search"></i> 搜索</button>
                    </div>
                </form>
                
                {% if search_results %}
                <div class="search-results">
                    <h3>搜索结果 | Search Results</h3>
                    
                    {% for result in search_results %}
                    <div class="result-item">
                        <div class="result-title">{{ result.title }}</div>
                        <a href="{{ result.link }}" class="result-link" target="_blank">{{ result.link }}</a>
                        <div class="result-snippet">{{ result.snippet }}</div>
                    </div>
                    {% endfor %}
                    
                    <div class="stats">
                        <span>找到 {{ search_results|length }} 个结果</span>
                        <span>处理时间: {{ "%.2f"|format(processing_time) }} 秒</span>
                    </div>
                    
                    <div class="btn-group">
                        <a href="/llm" class="btn btn-secondary"><i class="fas fa-robot"></i> 使用LLM分析结果 | Analyze with LLM</a>
                        <a href="/config" class="btn"><i class="fas fa-cog"></i> 调整配置 | Adjust Config</a>
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
        
        <footer>
            <div class="container">
                <p>&copy; {{ current_year }} LLM Web Search Plugin</p>
            </div>
        </footer>
    </body>
    </html>
    """, search_results=search_results, query=query, error_message=error_message, 
       processing_time=processing_time, current_year=datetime.now().year)

@app.route('/', methods=['GET'])
def home():
    """包含基本信息的主页"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="LLM Web Search Plugin - Enhance your LLM with web search capabilities">
        <title>LLM Web Search Plugin</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔍</text></svg>">
        <meta name="theme-color" content="#4361ee">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            :root {
                --primary-color: #4361ee;
                --primary-light: #4895ef;
                --secondary-color: #3f37c9;
                --accent-color: #560bad;
                --background-color: #f0f4f8;
                --card-color: #ffffff;
                --text-color: #2b2d42;
                --text-light: #6c757d;
                --border-color: #e9ecef;
                --success-color: #4caf50;
                --warning-color: #ff9800;
                --error-color: #f44336;
                --gradient-primary: linear-gradient(135deg, #4361ee, #3a0ca3);
                --shadow-sm: 0 2px 8px rgba(0,0,0,0.05);
                --shadow-md: 0 5px 15px rgba(0,0,0,0.07);
                --shadow-lg: 0 10px 25px rgba(0,0,0,0.1);
                --transition: all 0.3s ease;
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Poppins', sans-serif;
                line-height: 1.6;
                color: var(--text-color);
                background-color: var(--background-color);
                padding: 0;
                margin: 0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            
            .container {
                max-width: 1140px;
                margin: 0 auto;
                padding: 0 20px;
                width: 100%;
            }
            
            header {
                background: var(--gradient-primary);
                color: white;
                padding: 1.2rem 0;
                box-shadow: var(--shadow-md);
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            header .container {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                font-size: 1.4rem;
            }
            
            .logo i {
                font-size: 1.8rem;
            }
            
            nav ul {
                display: flex;
                list-style: none;
                gap: 25px;
            }
            
            nav ul li a {
                color: white;
                text-decoration: none;
                font-weight: 500;
                transition: var(--transition);
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            nav ul li a:hover {
                color: rgba(255, 255, 255, 0.8);
                transform: translateY(-2px);
            }
            
            main {
                flex: 1;
                padding: 40px 0;
            }
            
            .card {
                background-color: var(--card-color);
                border-radius: 12px;
                box-shadow: var(--shadow-sm);
                padding: 30px;
                margin-bottom: 30px;
                transition: var(--transition);
                border: 1px solid var(--border-color);
            }
            
            .card:hover {
                box-shadow: var(--shadow-md);
                transform: translateY(-5px);
            }
            
            .card-header {
                margin: -30px -30px 25px;
                padding: 20px 30px;
                background: var(--gradient-primary);
                color: white;
                border-radius: 12px 12px 0 0;
            }
            
            .card-header h2 {
                color: white;
                margin: 0;
                padding: 0;
                border: none;
            }
            
            h1, h2, h3 {
                color: var(--accent-color);
                margin-bottom: 20px;
                font-weight: 600;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            h2 {
                font-size: 1.6rem;
                position: relative;
                padding-bottom: 15px;
                margin-top: 30px;
            }
            
            h2::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 60px;
                height: 3px;
                background: var(--primary-light);
                border-radius: 3px;
            }
            
            .section-title {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 25px;
            }
            
            .section-title i {
                font-size: 1.4rem;
                color: var(--primary-color);
            }
            
            pre {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 20px 0;
                border-left: 4px solid var(--primary-color);
                font-size: 14px;
                box-shadow: var(--shadow-sm);
            }
            
            code {
                font-family: 'Fira Code', 'Courier New', Courier, monospace;
                color: #333;
            }
            
            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                background: var(--gradient-primary);
                color: white;
                text-decoration: none;
                padding: 14px 24px;
                border-radius: 8px;
                font-weight: 600;
                transition: var(--transition);
                box-shadow: var(--shadow-sm);
            }
            
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: var(--shadow-md);
            }
            
            .btn:active {
                transform: translateY(-1px);
            }
            
            .hero {
                text-align: center;
                padding: 40px 0;
            }
            
            .hero h1 {
                font-size: 2.5rem;
                margin-bottom: 20px;
                background: var(--gradient-primary);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: inline-block;
            }
            
            .hero p {
                font-size: 1.2rem;
                color: var(--text-light);
                max-width: 700px;
                margin: 0 auto 30px;
            }
            
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin: 40px 0;
            }
            
            .feature-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                padding: 20px;
            }
            
            .feature-icon {
                font-size: 2.5rem;
                color: var(--primary-color);
                margin-bottom: 15px;
            }
            
            .feature-title {
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 10px;
            }
            
            .endpoint {
                margin-bottom: 30px;
            }
            
            .endpoint-header {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
            }
            
            .endpoint-method {
                background-color: var(--primary-color);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 0.9rem;
            }
            
            .endpoint-path {
                font-family: 'Fira Code', monospace;
                font-weight: 500;
            }
            
            footer {
                text-align: center;
                padding: 30px 0;
                color: var(--text-light);
                font-size: 14px;
                border-top: 1px solid var(--border-color);
                margin-top: 60px;
                background-color: white;
                box-shadow: var(--shadow-sm);
            }
            
            footer a {
                color: var(--primary-color);
                text-decoration: none;
                transition: var(--transition);
            }
            
            footer a:hover {
                color: var(--accent-color);
                text-decoration: underline;
            }
            
            @media (max-width: 768px) {
                .feature-grid {
                    grid-template-columns: 1fr;
                }
                
                header .container {
                    flex-direction: column;
                    text-align: center;
                }
                
                nav ul {
                    margin-top: 15px;
                    justify-content: center;
                }
                
                .hero h1 {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <div class="logo">
                    <i class="fas fa-search"></i>
                    <span>LLM Web Search Plugin</span>
                </div>
                <nav>
                    <ul>
                        <li><a href="/"><i class="fas fa-home"></i> Home</a></li>
                        <li><a href="/llm"><i class="fas fa-robot"></i> LLM交互 | LLM Chat</a></li>
                        <li><a href="/config"><i class="fas fa-cog"></i> Configuration</a></li>
                    </ul>
                </nav>
            </div>
        </header>
        
        <main>
            <div class="container">
                <div class="hero">
                    <h1>Enhance Your LLM with Web Search</h1>
                    <p>A powerful plugin that allows locally deployed LLMs to perform web searches and retrieve accurate time information.</p>
                    <a href="/config" class="btn"><i class="fas fa-cog"></i> Configure Settings</a>
                </div>
                
                <div class="feature-grid">
                    <div class="feature-item">
                        <div class="feature-icon"><i class="fas fa-search"></i></div>
                        <div class="feature-title">Web Search</div>
                        <p>Search the web with Google, Bing or Baidu and get formatted results for your LLM.</p>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon"><i class="far fa-clock"></i></div>
                        <div class="feature-title">Time Retrieval</div>
                        <p>Get accurate current time from authoritative online sources.</p>
                    </div>
                    <div class="feature-item">
                        <div class="feature-icon"><i class="fas fa-cogs"></i></div>
                        <div class="feature-title">Customizable</div>
                        <p>Adjust settings to fit your specific needs and preferences.</p>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2><i class="fas fa-code"></i> API Endpoints</h2>
                    </div>
                    
                    <div class="endpoint">
                        <div class="endpoint-header">
                            <span class="endpoint-method">POST</span>
                            <span class="endpoint-path">/search</span>
                        </div>
                        <p>Perform a web search and get formatted results for your LLM.</p>
                        <pre><code>POST /search
Content-Type: application/json

{
    "query": "Your search query here",
    "num_results": 5,
    "fetch_content": false,
    "search_engine": "google",
    "llm_model": "deepseek-r1:1.5b",
    "temperature": 0.7,
    "max_tokens": 2048
}</code></pre>
                    </div>
                    
                    <div class="endpoint">
                        <div class="endpoint-header">
                            <span class="endpoint-method">GET</span>
                            <span class="endpoint-path">/current_time</span>
                        </div>
                        <p>Get the current time from authoritative online sources.</p>
                        <pre><code>GET /current_time</code></pre>
                    </div>
                    
                    <div class="endpoint">
                        <div class="endpoint-header">
                            <span class="endpoint-method">GET</span>
                            <span class="endpoint-path">/health</span>
                        </div>
                        <p>Check if the API is running.</p>
                        <pre><code>GET /health</code></pre>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <h2><i class="fas fa-laptop-code"></i> Example Usage</h2>
                    </div>
                    <pre><code>import requests

# Search example
response = requests.post(
    "http://localhost:5005/search",
    json={
        "query": "latest advancements in AI",
        "num_results": 5,
        "fetch_content": True,
        "llm_model": "deepseek-r1:1.5b",
        "temperature": 0.7,
        "max_tokens": 2048
    }
)

data = response.json()
llm_prompt = data["formatted_prompt"]

# Time retrieval example
time_response = requests.get("http://localhost:5005/current_time")
time_data = time_response.json()
print(f"Current time: {time_data['time']}")</code></pre>
                </div>
            </div>
        </main>
        
        <footer>
            <div class="container">
                <p>LLM Web Search Plugin &copy; 2025. Developed with <i class="fas fa-heart" style="color: #ff6b6b;"></i> for LLM enthusiasts.</p>
                <p><small>Version 1.0.0 | <a href="https://github.com" target="_blank"><i class="fab fa-github"></i> GitHub</a></small></p>
            </div>
        </footer>
    </body>
    </html>
    """

if __name__ == '__main__':
    # 确保从.env文件加载环境变量
    port = 5005  # 固定使用5005端口
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting server on port {port} with debug={debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)
