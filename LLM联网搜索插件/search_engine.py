import requests
from bs4 import BeautifulSoup
import json
import os
import re
import nltk
from urllib.parse import quote_plus, urlparse
import time
import random
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime

# 在首次导入时下载所需的NLTK资源 | Download required NLTK resources on first import
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class WebSearch:
    """
    提供互联网搜索功能的类。
    Class that provides internet search capabilities.
    """
    
    def __init__(self, search_engine="google", timeout=10):
        """
        初始化 WebSearch 类。
        Initialize the WebSearch class.
        
        参数 | Args:
            search_engine (str): 要使用的搜索引擎 ("google", "bing", "baidu") | Search engine to use ("google", "bing", "baidu")
            timeout (int): 请求超时时间（秒） | Request timeout in seconds
        """
        self.search_engine = search_engine.lower()
        self.timeout = timeout
        
        if self.search_engine not in ["google", "bing", "baidu"]:
            raise ValueError(f"不支持的搜索引擎: {search_engine}。支持的引擎: google, bing, baidu")
        
        # 设置默认请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
    
    def search(self, query, num_results=5):
        """
        执行给定查询的网络搜索。
        Perform a web search for the given query.
        
        参数 | Args:
            query (str): 搜索查询 | The search query
            num_results (int): 返回结果的数量 | Number of results to return
            
        返回 | Returns:
            list: 包含搜索结果的字典列表 | List of dictionaries containing search results
        """
        if self.search_engine == "google":
            return self._google_search(query, num_results)
        elif self.search_engine == "bing":
            return self._bing_search(query, num_results)
        elif self.search_engine == "baidu":
            return self._baidu_search(query, num_results)
        else:
            raise ValueError(f"Unsupported search engine: {self.search_engine}")
    
    def _google_search(self, query, num_results=5):
        """
        执行Google搜索。
        Perform a Google search.
        
        注意：这是一个简单实现，由于Google的反爬取措施，可能不能可靠地工作。
        在生产使用中，考虑使用官方的Google搜索API。
        Note: This is a simple implementation and might not work reliably due to Google's 
        anti-scraping measures. For production use, consider using official Google Search API.
        """
        search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}&hl=zh-CN"
        
        # 尝试不同的用户代理
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]
        
        # 最多尝试3次
        max_retries = 3
        for retry in range(max_retries):
            try:
                # 每次尝试使用不同的用户代理
                current_headers = self.headers.copy()
                current_headers["User-Agent"] = user_agents[retry % len(user_agents)]
                
                print(f"尝试搜索 (尝试 {retry+1}/{max_retries}): {search_url}")
                print(f"使用用户代理: {current_headers['User-Agent'][:30]}...")
                
                response = requests.get(search_url, headers=current_headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = []
                
                # 保存HTML以便调试
                debug_file = f"google_search_debug_{retry+1}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"已保存响应HTML到 {debug_file}")
                
                # 更全面的选择器列表
                selectors = [
                    'div.g',                # 传统选择器
                    'div.Gx5Zad',           # 新版选择器
                    'div.tF2Cxc',           # 另一种可能的选择器
                    'div[jscontroller]',    # 更通用的选择器
                    'div.MjjYud',           # 2023年版选择器
                    'div.v7W49e',           # 另一个可能的容器
                    'div.srKDX',            # 2024年版可能的选择器
                    'div.N54PNb'            # 另一个可能的容器
                ]
                
                # 标题选择器列表
                title_selectors = [
                    'h3',
                    'h3.LC20lb',
                    'div.vvjwJb',
                    'div.DKV0Md',
                    'h3.zBAuLc',
                    'h3.DKV0Md'
                ]
                
                # 链接选择器列表
                link_selectors = [
                    'a',
                    'a[href]',
                    'div.yuRUbf > a',
                    'div.Z26q7c > a',
                    'div.eKjLze > div > div > a'
                ]
                
                # 摘要选择器列表
                snippet_selectors = [
                    'div.VwiC3b',
                    'div.lEBKkf',
                    'span.aCOpRe',
                    'div.s3v9rd',
                    'div.VwiC3b.yXK7lf',
                    'span.s3v9rd'
                ]
                
                results_found = False
                
                # 首先尝试使用选择器找到结果容器
                for selector in selectors:
                    results = soup.select(selector)
                    if results:
                        print(f"找到结果使用选择器: {selector}, 数量: {len(results)}")
                        results_found = True
                        
                        for result in results:
                            # 尝试找到标题
                            title_element = None
                            for title_selector in title_selectors:
                                title_element = result.select_one(title_selector)
                                if title_element:
                                    break
                            
                            # 尝试找到链接
                            link_element = None
                            for link_selector in link_selectors:
                                link_element = result.select_one(link_selector)
                                if link_element and link_element.has_attr('href'):
                                    break
                            
                            # 尝试找到摘要
                            snippet_element = None
                            for snippet_selector in snippet_selectors:
                                snippet_element = result.select_one(snippet_selector)
                                if snippet_element:
                                    break
                            
                            if title_element and link_element:
                                title = title_element.get_text().strip()
                                link = link_element['href']
                                if link.startswith('/url?q='):
                                    link = link.split('/url?q=')[1].split('&')[0]
                                
                                # 如果找不到摘要，使用默认文本
                                snippet = snippet_element.get_text().strip() if snippet_element else "未找到摘要"
                                
                                # 过滤掉不相关的结果
                                if not any(x in link for x in ['google.com/search', 'accounts.google', 'support.google']):
                                    search_results.append({
                                        'title': title,
                                        'link': link,
                                        'snippet': snippet
                                    })
                                
                                # 只有当我们收集了足够多的结果时才退出循环
                                if len(search_results) >= num_results:
                                    break
                        
                        if search_results:
                            break
                
                # 如果找到了搜索结果，返回它们
                if search_results:
                    print(f"成功找到 {len(search_results)} 个搜索结果")
                    # 确保只返回请求的结果数量
                    return search_results[:num_results]
                
                # 如果没有找到结果，尝试下一次重试
                print("未找到搜索结果，尝试不同的方法...")
                
            except Exception as e:
                print(f"搜索时出错 (尝试 {retry+1}/{max_retries}): {e}")
                # 如果不是最后一次尝试，继续下一次
                if retry < max_retries - 1:
                    print("将在1秒后重试...")
                    import time
                    time.sleep(1)
        
        # 如果所有尝试都失败，使用模拟结果
        print("所有搜索尝试均失败，使用模拟结果")
        return self._mock_search_results(query, num_results)
    
    def _mock_search_results(self, query, num_results=5):
        """
        当实际搜索失败时，生成模拟搜索结果。
        Generate mock search results when actual search fails.
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 基本模拟结果
        mock_results = [
            {
                'title': f'关于 "{query}" 的搜索结果 - 模拟数据',
                'link': 'https://example.com/search-results',
                'snippet': f'这是一个模拟的搜索结果。由于无法连接到搜索引擎，系统生成了这个占位符。当前时间: {current_time}'
            },
            {
                'title': '搜索功能暂时不可用',
                'link': 'https://example.com/search-unavailable',
                'snippet': '搜索引擎可能暂时阻止了来自此IP的请求，或者网络连接存在问题。请稍后再试。'
            }
        ]
        
        # 根据查询类型添加特定的模拟结果
        
        # 时间相关查询
        time_keywords = ["时间", "日期", "几点", "what time", "current time", "date", "today", "now", "当前时间"]
        if any(keyword in query.lower() for keyword in time_keywords):
            weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][datetime.now().weekday()]
            weekday_en = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][datetime.now().weekday()]
            
            mock_results.append({
                'title': '当前时间信息',
                'link': 'https://example.com/current-time',
                'snippet': f'当前系统时间是 {current_time}，星期{weekday_cn} ({weekday_en})。这是由系统生成的时间信息。'
            })
        
        # 天气相关查询
        weather_keywords = ["天气", "气温", "weather", "temperature", "forecast", "雨", "雪", "晴", "阴"]
        location_keywords = ["北京", "上海", "广州", "深圳", "杭州", "成都", "重庆", "武汉", "西安", "南京", 
                            "beijing", "shanghai", "guangzhou", "shenzhen"]
        
        if any(keyword in query.lower() for keyword in weather_keywords):
            # 检查是否包含位置信息
            location = "未知位置"
            for loc in location_keywords:
                if loc in query.lower():
                    location = loc
                    break
            
            mock_results.append({
                'title': f'{location}天气信息 - 模拟数据',
                'link': 'https://example.com/weather-unavailable',
                'snippet': f'由于无法连接到天气服务，无法获取{location}的实时天气信息。这是一个模拟的天气信息占位符。'
            })
        
        # 新闻相关查询
        news_keywords = ["新闻", "资讯", "头条", "news", "headlines", "最新消息", "报道"]
        if any(keyword in query.lower() for keyword in news_keywords):
            mock_results.append({
                'title': '最新新闻 - 模拟数据',
                'link': 'https://example.com/news',
                'snippet': f'由于无法连接到新闻服务，无法获取关于"{query}"的最新新闻。这是一个模拟的新闻信息占位符。'
            })
        
        # 返回请求数量的结果
        return mock_results[:num_results]
    
    def _baidu_search(self, query, num_results=5):
        """
        执行百度搜索。
        Perform a Baidu search.
        
        注意：这是一个简单实现。在生产使用中，考虑使用官方的百度搜索API。
        Note: This is a simple implementation. For production use, consider using 
        official Baidu Search API.
        """
        search_url = f"https://www.baidu.com/s?wd={quote_plus(query)}&rn={num_results}"
        
        # 尝试不同的用户代理
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]
        
        # 最多尝试3次
        max_retries = 3
        for retry in range(max_retries):
            try:
                # 每次尝试使用不同的用户代理
                current_headers = self.headers.copy()
                current_headers["User-Agent"] = user_agents[retry % len(user_agents)]
                
                print(f"尝试百度搜索 (尝试 {retry+1}/{max_retries}): {search_url}")
                print(f"使用用户代理: {current_headers['User-Agent'][:30]}...")
                
                response = requests.get(search_url, headers=current_headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = []
                
                # 保存HTML以便调试
                debug_file = f"baidu_search_debug_{retry+1}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"已保存响应HTML到 {debug_file}")
                
                # 百度搜索结果容器选择器
                result_containers = soup.select('div.result.c-container')
                if not result_containers:
                    result_containers = soup.select('div.result-op.c-container')
                if not result_containers:
                    result_containers = soup.select('div.c-container')
                
                if result_containers:
                    print(f"找到 {len(result_containers)} 个百度搜索结果")
                    
                    for container in result_containers:
                        # 提取标题
                        title_element = container.select_one('h3.t') or container.select_one('h3.c-title')
                        if not title_element:
                            continue
                            
                        title = title_element.get_text().strip()
                        
                        # 提取链接
                        link_element = title_element.select_one('a')
                        if not link_element or not link_element.has_attr('href'):
                            continue
                            
                        link = link_element['href']
                        
                        # 百度搜索结果链接通常是重定向链接，需要进一步处理
                        if link.startswith('http'):
                            pass  # 已经是完整URL
                        else:
                            # 如果是相对链接，转换为绝对链接
                            link = f"https://www.baidu.com{link}"
                        
                        # 提取摘要 - 尝试多种选择器
                        snippet = ""
                        
                        # 尝试方法1：查找内容类
                        snippet_element = container.select_one('div.c-abstract') or container.select_one('div.c-span-last')
                        if snippet_element:
                            snippet = snippet_element.get_text().strip()
                        
                        # 尝试方法2：查找内容包装器
                        if not snippet:
                            content_wrappers = container.select('.pure-test-wrap_T03sY .content-right_1THTn')
                            if content_wrappers:
                                snippet = content_wrappers[0].get_text().strip()
                        
                        # 尝试方法3：查找任何文本内容
                        if not snippet:
                            # 排除标题和链接元素
                            for text_element in container.find_all(text=True, recursive=True):
                                parent = text_element.parent
                                if parent and parent.name not in ['h3', 'a', 'script', 'style']:
                                    text = text_element.strip()
                                    if text and len(text) > 20:  # 只考虑较长的文本
                                        snippet = text
                                        break
                        
                        # 如果仍然没有找到摘要，使用占位符
                        if not snippet:
                            snippet = "百度搜索结果摘要不可用"
                        
                        search_results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                        
                        if len(search_results) >= num_results:
                            break
                    
                    if search_results:
                        print(f"成功找到 {len(search_results)} 个百度搜索结果")
                        # 确保只返回请求的结果数量
                        return search_results[:num_results]
                
                print("未找到百度搜索结果，尝试不同的方法...")
                
            except Exception as e:
                print(f"百度搜索时出错 (尝试 {retry+1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    print("将在1秒后重试...")
                    import time
                    time.sleep(1)
        
        # 如果所有尝试都失败，使用模拟结果
        print("所有百度搜索尝试均失败，使用模拟结果")
        return self._mock_search_results(query, num_results)
    
    def _bing_search(self, query, num_results=5):
        """
        执行Bing搜索。
        Perform a Bing search.
        
        注意：这是一个简单实现。在生产使用中，考虑使用官方的Bing搜索API。
        Note: This is a simple implementation. For production use, consider using 
        official Bing Search API.
        """
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={num_results}"
        
        try:
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = []
            
            # 提取搜索结果 | Extract search results
            for result in soup.select('li.b_algo'):
                title_element = result.select_one('h2 a')
                snippet_element = result.select_one('div.b_caption p')
                
                if title_element and snippet_element:
                    title = title_element.get_text()
                    link = title_element['href']
                    snippet = snippet_element.get_text()
                    
                    search_results.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet
                    })
                    
                    if len(search_results) >= num_results:
                        break
            
            # 确保只返回请求的结果数量
            return search_results[:num_results]
            
        except Exception as e:
            print(f"Error during Bing search: {e}")
            return []
    
    def fetch_content(self, url: str, summarize: bool = False, max_length: int = 5000) -> Dict[str, Any]:
        """
        获取并提取网页的主要内容，可选择生成摘要。
        Fetch and extract the main content from a webpage with optional summarization.
        
        参数 | Args:
            url: 要获取的网页URL | URL of the webpage to fetch
            summarize: 是否生成内容摘要 | Whether to generate a summary of the content
            max_length: 返回内容的最大长度 | Maximum length of the content to return
            
        返回 | Returns:
            包含从网页提取的内容和元数据的字典 | Dictionary containing extracted content and metadata from the webpage
        """
        try:
            # 添加小延迟以避免速率限制 | Add a small delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            
            # 获取域名以供后续使用 | Get the domain for later use
            domain = urlparse(url).netloc
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # 尝试检测编码 | Try to detect the encoding
            if 'charset' in response.headers.get('Content-Type', ''):
                response.encoding = response.headers.get_content_charset()
            else:
                # BeautifulSoup可以帮助检测编码 | BeautifulSoup can help with encoding detection
                soup = BeautifulSoup(response.content, 'html.parser')
                meta_charset = soup.find('meta', charset=True)
                if meta_charset:
                    response.encoding = meta_charset.get('charset')
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试获取标题 | Try to get title
            title = self._extract_title(soup)
            
            # 尝试提取发布日期 | Try to extract publish date
            publish_date = self._extract_publish_date(soup)
            
            # 尝试提取作者 | Try to extract author
            author = self._extract_author(soup)
            
            # 移除不需要的元素 | Remove unwanted elements
            for element in soup.select('nav, footer, header, aside, .ad, .ads, .advert, .cookie, .sidebar, .comments, .related'):
                element.extract()
            
            # 移除脚本和样式元素 | Remove script and style elements
            for script in soup(["script", "style", "svg", "noscript", "iframe"]):
                script.extract()
            
            # Focus on main content area if possible
            main_content = None
            for selector in ['main', 'article', '.post-content', '.article-content', '.entry-content', '#content', '.content']:
                main = soup.select_one(selector)
                if main and len(main.get_text(strip=True)) > 200:
                    main_content = main
                    break
            
            # If no main content area was found, use the body
            if not main_content:
                main_content = soup.body if soup.body else soup
            
            # Get text
            text = main_content.get_text(' ', strip=True)
            
            # Clean up the text
            text = self._clean_text(text)
            
            # Create a result dictionary
            result = {
                "url": url,
                "domain": domain,
                "title": title,
                "author": author,
                "publish_date": publish_date,
                "content": text[:max_length] + "..." if len(text) > max_length else text,
                "content_length": len(text)
            }
            
            # Generate a summary if requested
            if summarize and text:
                summary = self._generate_summary(text)
                key_points = self._extract_key_points(text)
                result["summary"] = summary
                result["key_points"] = key_points
                
            return result
            
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return {
                "url": url,
                "domain": urlparse(url).netloc,
                "error": str(e),
                "content": f"Failed to fetch content from {url}: {str(e)}",
                "content_length": 0
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title of the webpage."""
        # Try to get title from og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
            
        # Try to get title from twitter:title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content']
            
        # Use the standard title tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()
            
        # Try to find the first h1
        h1 = soup.find('h1')
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)
            
        return "Unknown Title"
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the publication date from the webpage."""
        # Try to get date from meta tags
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '').lower()
            name = meta.get('name', '').lower()
            if 'published_time' in prop or 'publication_date' in name or 'publish-date' in name:
                if meta.get('content'):
                    return meta['content']
                    
        # Look for time tags with datetime attribute
        time_tag = soup.find('time')
        if time_tag and time_tag.get('datetime'):
            return time_tag['datetime']
            
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the author from the webpage."""
        # Try to get author from meta tags
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '').lower()
            name = meta.get('name', '').lower()
            if 'author' in prop or 'author' in name:
                if meta.get('content'):
                    return meta['content']
                    
        # Look for structured data with author information
        author_elements = soup.select('.author, .byline, .meta-author')
        if author_elements:
            for element in author_elements:
                author_text = element.get_text(strip=True)
                if author_text and len(author_text) < 100:  # Avoid getting long text that's not actually an author
                    return author_text
                    
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean the extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common message patterns
        patterns_to_remove = [
            r'Cookie Policy',
            r'Privacy Policy',
            r'Terms of Service',
            r'Accept Cookies',
            r'\d+ comments',
            r'Share on (Facebook|Twitter|LinkedIn)',
            r'Click here to subscribe',
            r'Sign up for our newsletter',
            r'Copyright \d{4}',
            r'All rights reserved',
            r'Please enable JavaScript'
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Split by newlines and filter out very short lines that are likely menu items or ads
        lines = [line.strip() for line in text.split('\n')]
        filtered_lines = [line for line in lines if len(line) > 20 or (len(line) > 0 and line[-1] not in '.,:;')]
        
        return '\n'.join(filtered_lines).strip()
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """Generate a simple extractive summary of the content."""
        if not text:
            return ""
            
        # Tokenize into sentences
        sentences = nltk.sent_tokenize(text)
        
        if not sentences:
            return ""
            
        # Simple case - if there's only a few sentences, use them all
        if len(sentences) <= 3:
            return ' '.join(sentences)
        
        # Tokenize words and create frequency distribution
        words = nltk.word_tokenize(text.lower())
        stop_words = set(nltk.corpus.stopwords.words('english'))
        words = [word for word in words if word.isalnum() and word not in stop_words]
        
        word_freq = Counter(words)
        
        # Score sentences based on word frequency
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_words = nltk.word_tokenize(sentence.lower())
            sentence_words = [word for word in sentence_words if word.isalnum()]
            
            # Prefer sentences that aren't too short or too long
            length_factor = min(1.0, len(sentence_words) / 20.0) if len(sentence_words) < 20 else min(1.0, 40.0 / len(sentence_words))
            
            # Position bias - earlier sentences more likely to be important
            position_factor = 1.0 if i < 5 else 0.8
            
            for word in sentence_words:
                if word in word_freq:
                    score += word_freq[word]
            
            # Normalize by sentence length to avoid favoring very long sentences
            if len(sentence_words) > 0:
                sentence_scores[i] = (score / len(sentence_words)) * length_factor * position_factor
        
        # Get top sentences
        top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:3]
        top_sentence_indices = sorted(top_sentence_indices)  # Sort by position in text
        
        summary = ' '.join([sentences[i] for i in top_sentence_indices])
        
        # Truncate if necessary
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
            
        return summary
    
    def _extract_key_points(self, text: str, max_points: int = 5) -> List[str]:
        """Extract key points from the content."""
        if not text:
            return []
            
        # Tokenize into sentences
        sentences = nltk.sent_tokenize(text)
        
        if not sentences or len(sentences) <= max_points:
            return sentences
        
        # Similar scoring approach as summary generation
        words = nltk.word_tokenize(text.lower())
        stop_words = set(nltk.corpus.stopwords.words('english'))
        words = [word for word in words if word.isalnum() and word not in stop_words]
        
        word_freq = Counter(words)
        
        # Score sentences
        sentence_scores = {}
        for i, sentence in enumerate(sentences):
            # Skip very short sentences
            if len(sentence) < 30:
                continue
                
            score = 0
            sentence_words = nltk.word_tokenize(sentence.lower())
            sentence_words = [word for word in sentence_words if word.isalnum() and word not in stop_words]
            
            # Look for indicator phrases for key points
            indicator_bonus = 0
            indicators = ['importantly', 'significantly', 'notably', 'key', 'crucial', 'essential', 'primary']
            for indicator in indicators:
                if indicator in sentence_words:
                    indicator_bonus += 0.5
            
            for word in sentence_words:
                if word in word_freq:
                    score += word_freq[word]
            
            if len(sentence_words) > 0:
                sentence_scores[i] = (score / len(sentence_words)) + indicator_bonus
        
        # Get top scoring sentences
        top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_points]
        top_sentence_indices = sorted(top_sentence_indices)  # Sort by position in text
        
        return [sentences[i] for i in top_sentence_indices]
