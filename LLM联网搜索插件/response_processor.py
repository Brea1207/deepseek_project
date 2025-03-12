import json
import re
import textwrap
from datetime import datetime
from typing import List, Dict, Optional, Any

class ResponseProcessor:
    """处理和格式化搜索结果供LLM使用。
    Process and format search results for LLM consumption."""
    
    def __init__(self, max_tokens=4000, max_content_per_source=1500):
        self.max_tokens = max_tokens
        self.max_content_per_source = max_content_per_source
    
    def format_search_results(self, query: str, search_results: List[Dict[str, Any]], 
                              detailed_content: Optional[Dict[str, str]] = None) -> str:
        """
        将搜索结果格式化为结构化的LLM响应。
        Format search results into a structured response for the LLM.
        
        参数 | Args:
            query: 原始搜索查询 | The original search query
            search_results: 搜索结果字典列表 | List of search result dictionaries
            detailed_content: 特定网址的详细内容字典 | Dictionary of detailed content from specific URLs
            
        返回 | Returns:
            格式化的LLM响应 | Formatted response for the LLM
        """
        # 获取当前日期和时间 | Get current date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 开始构建响应 | Start building the response
        response = f"# Search Results for: \"{query}\"\n"
        response += f"*Search performed at: {current_time}*\n\n"
        
        # 添加搜索结果摘要 | Add search result summaries
        response += "## Search Result Summaries\n\n"
        
        if not search_results:
            response += "*No search results found*\n\n"
        else:
            for i, result in enumerate(search_results, 1):
                response += f"### {i}. {result['title']}\n"
                response += f"**Source**: [{result['link']}]({result['link']})\n"
                response += f"**Summary**: {result['snippet']}\n\n"
        
        # 如果可用，添加详细内容 | Add detailed content if available
        if detailed_content and len(detailed_content) > 0:
            response += "## Detailed Content\n\n"
            
            for url, content in detailed_content.items():
                # Find the corresponding search result to get the title
                title = next((r['title'] for r in search_results if r['link'] == url), "Content")
                
                # 清理和格式化内容 | Clean and format the content
                cleaned_content = self._clean_content(content)
                formatted_content = self._format_content_extract(cleaned_content)
                
                response += f"### {title}\n"
                response += f"**Source**: [{url}]({url})\n"
                response += f"**Content**:\n```\n{formatted_content}\n```\n\n"
        
        # 为LLM添加提示 | Add a prompt for the LLM
        response += "## Instructions for LLM\n\n"
        response += "Based on the search results above, please provide a comprehensive answer to the query. "
        response += "Include relevant information from the search results and cite sources appropriately using the source numbers. "
        response += "If the search results don't contain sufficient information to answer the query, "
        response += "please acknowledge the limitations and provide the best possible answer based on available information."
        
        return response
    
    def _clean_content(self, content) -> str:
        """清理和标准化网页内容。 | Clean and normalize content from web pages."""
        if not content:
            return ""
            
        # 确保内容是字符串类型
        if not isinstance(content, str):
            try:
                content = str(content)
            except:
                return "无法处理的内容类型"
            
        # 移除过多的空白符 | Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # 移除常见的网页人工制品 | Remove common web page artifacts
        content = re.sub(r'Cookie Policy|Privacy Policy|Terms of Service|\d+ comments', '', content)
        
        # 移除电子邮件地址 | Remove email addresses
        content = re.sub(r'[\w.+-]+@[\w-]+\.[\w.-]+', '[EMAIL]', content)
        
        return content.strip()
    
    def _format_content_extract(self, content: str) -> str:
        """将内容提取格式化为合理的长度。 | Format a content extract to a reasonable length."""
        if not content:
            return "No content available"
            
        # 将内容截断到最大长度 | Truncate content to maximum length
        if len(content) > self.max_content_per_source:
            # 尝试在句子边界处截断 | Try to truncate at a sentence boundary
            truncation_point = content[:self.max_content_per_source].rfind('.')
            if truncation_point == -1 or truncation_point < self.max_content_per_source * 0.8:
                # 如果没有找到合适的句子边界，就在最大长度处截断 | If no good sentence boundary found, just truncate at max length
                truncated_content = content[:self.max_content_per_source]
            else:
                truncated_content = content[:truncation_point+1]
            
            formatted_content = truncated_content + "\n[Content truncated...]"
        else:
            formatted_content = content
        
        # 对长行进行换行以提高可读性 | Wrap long lines for better readability
        formatted_content = '\n'.join(textwrap.wrap(formatted_content, width=100, 
                                                    break_long_words=False, 
                                                    replace_whitespace=False))
        
        return formatted_content
    
    def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """从内容提取中提取关键点。 | Extract key points from a content extract."""
        if not content:
            return []
            
        # 将内容分割成句子 | Split the content into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # 过滤掉非常短的句子或没有多少内容的句子 | Filter out very short sentences or sentences without much content
        valid_sentences = [s for s in sentences if len(s) > 20 and re.search(r'\w', s)]
        
        # 选择一部分句子作为关键点（简单方法 - 可以增强） | Select a subset of sentences as key points (simple approach - could be enhanced)
        key_points = []
        if valid_sentences:
            # 选取分布在整个内容中的句子 | Take sentences distributed throughout the content
            step = max(1, len(valid_sentences) // max_points)
            key_points = [valid_sentences[i] for i in range(0, len(valid_sentences), step)][:max_points]
        
        return key_points
    
    def create_prompt_with_search_results(self, user_query: str, search_results: List[Dict[str, Any]],
                                          detailed_content: Optional[Dict[str, str]] = None,
                                          system_prompt: Optional[str] = None) -> str:
        """
        创建一个将用户查询与搜索结果结合的提示词。
        Create a prompt that combines the user's query with search results.
        
        参数 | Args:
            user_query: 用户的原始查询 | The user's original query
            search_results: 搜索结果字典列表 | List of search result dictionaries
            detailed_content: 特定网址的详细内容字典 | Dictionary of detailed content from specific URLs
            system_prompt: 可选的自定义系统提示词 | Optional custom system prompt to use
            
        返回 | Returns:
            包含用户查询和搜索结果的LLM提示词 | A prompt for the LLM that includes the user query and search results
        """
        formatted_results = self.format_search_results(user_query, search_results, detailed_content)
        
        # 如果未提供，使用默认系统提示词 | Default system prompt if none provided
        if not system_prompt:
            system_prompt = (
                "You are an AI assistant with access to web search results. "
                "You specialize in providing accurate information based on recent web content. "
                "When responding, always cite your sources by referring to the search result numbers. "
                "If the search results contain contradictory information, acknowledge this and explain why. "
                "If the search results don't provide sufficient information to fully answer the query, be transparent about these limitations."
            )
        
        prompt = (
            f"{system_prompt}\n\n"
            f"The user asked: \"{user_query}\"\n\n"
            "I've searched the web and found the following information to help answer this question:\n\n"
            f"{formatted_results}\n\n"
            "Based on these search results, provide a comprehensive, accurate, and helpful response to the user's question. "
            "Cite specific sources by their numbers when drawing information from them. "
            "Format your response in a clear, structured way with appropriate headings and lists where helpful."
        )
        
        return prompt
