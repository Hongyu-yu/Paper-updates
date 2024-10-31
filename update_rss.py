# 配置参数
RSS_FEEDS = [
    'http://feeds.aps.org/rss/tocsec/PRL-CondensedMatterStructureetc.xml',
    'http://feeds.aps.org/rss/tocsec/PRL-CondensedMatterElectronicPropertiesetc.xml',
    'http://feeds.aps.org/rss/recent/prlsuggestions.xml',
    'https://phys.org/rss-feed/physics-news/',
    'https://www.pnas.org/rss/Physics.xml',
    'https://www.pnas.org/rss/Applied_Physical_Sciences.xml',
    'https://phys.org/rss-feed/physics-news/physics/',
    'http://export.arxiv.org/rss/cond-mat',
    'https://www.nature.com/nature.rss',
    'http://feeds.feedburner.com/acs/nalefd',
    'http://feeds.nature.com/npjcompumats/rss/current',
    'https://onlinelibrary.wiley.com/action/showFeed?jc=15214095&type=etoc&feed=rss',
    'https://onlinelibrary.wiley.com/action/showFeed?jc=16163028&type=etoc&feed=rss',
    'http://export.arxiv.org/rss/cond-mat.mtrl-sci',
    'http://export.arxiv.org/rss/cond-mat.other',
    'http://export.arxiv.org/rss/cond-mat.dis-nn',
    'http://export.arxiv.org/rss/cond-mat.stat-mech',
    'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv',
    'http://export.arxiv.org/rss/physics',
    'https://aip.scitation.org/action/showFeed?type=etoc&feed=rss&jc=jcp',
    'http://feeds.aps.org/rss/recent/prx.xml',
    'http://feeds.aps.org/rss/recent/rmp.xml',
    'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science',
    'http://feeds.feedburner.com/acs/achre4',
    'https://chemrxiv.org/engage/rss/chemrxiv',
    'https://onlinelibrary.wiley.com/action/showFeed?jc=21983844&type=etoc&feed=rss',
    "https://www.researchsquare.com/rss.xml",
    # 添加更多RSS源
]

KEYWORDS = [
    "learning",
    "ferro",
    "network",
    "neural",
    'machine',
    # 可以添加更多关键词
]
import feedparser
import os
from datetime import datetime
import re
from github import Github
import pytz
import translators as ts
import time

# 配置参数

# GitHub配置
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')  # 从环境变量获取token
REPO_NAME = "Hongyu-yu/Paper-updates"
TIMEZONE = pytz.timezone('Asia/Shanghai')

def translate_text(text, retry_count=3):
    """翻译文本，带有重试机制"""
    for i in range(retry_count):
        try:
            # 如果文本已经是中文，则不进行翻译
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return text
            translated = ts.google(text, to_language='zh')
            time.sleep(1)  # 添加延迟以避免请求过快
            return translated
        except Exception as e:
            if i == retry_count - 1:  # 如果是最后一次重试
                print(f"Translation failed: {str(e)}")
                return text  # 返回原文
            time.sleep(2)  # 失败后等待更长时间再重试
    return text

def check_keywords(text):
    """检查文本是否包含关键词"""
    if not text:
        return False
    text = text.lower()
    return any(keyword.lower() in text for keyword in KEYWORDS)

def format_content(entry):
    """格式化文章内容，包含原文和翻译"""
    date = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
    # 获取并翻译标题
    title = entry.title
    title_zh = translate_text(title)
    
    content = f"# {title}\n\n"
    if title_zh != title:
        content += f"## 标题翻译\n{title_zh}\n\n"
    
    content += f"Date: {date}\n\n"
    content += f"Link: {entry.link}\n\n"
    
    # 获取并翻译摘要
    if hasattr(entry, 'summary'):
        content += f"## Original Summary\n{entry.summary}\n\n"
        summary_zh = translate_text(entry.summary)
        if summary_zh != entry.summary:
            content += f"## 摘要翻译\n{summary_zh}\n\n"
    
    return content

def main():
    # 初始化GitHub
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    # 获取当前日期
    now = datetime.now(TIMEZONE)
    year_month = now.strftime("%Y-%m")
    today = now.strftime("%Y-%m-%d")
    
    # 创建内容收集列表
    filtered_content = []
    
    # 处理每个RSS源
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Processing feed: {feed_url}")
            
            for entry in feed.entries:
                # 检查标题和描述是否包含关键词
                title = entry.get('title', '')
                description = entry.get('description', '')
                
                if check_keywords(title) or check_keywords(description):
                    filtered_content.append(format_content(entry))
                    print(f"Found relevant content: {title}")
                    
        except Exception as e:
            print(f"Error processing feed {feed_url}: {str(e)}")
    
    if filtered_content:
        # 组合所有内容
        all_content = "\n---\n".join(filtered_content)
        
        try:
            # 检查文件夹是否存在
            try:
                repo.get_contents(f"content/{year_month}")
            except:
                repo.create_file(
                    f"content/{year_month}/.gitkeep",
                    f"Create folder for {year_month}",
                    ""
                )
            
            # 创建或更新文件
            file_path = f"content/{year_month}/{today}.md"
            try:
                # 如果文件存在，更新它
                file = repo.get_contents(file_path)
                repo.update_file(
                    file_path,
                    f"Update content for {today}",
                    all_content,
                    file.sha
                )
            except:
                # 如果文件不存在，创建新文件
                repo.create_file(
                    file_path,
                    f"Add content for {today}",
                    all_content
                )
                
            print(f"Successfully updated content for {today}")
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
    
    else:
        print("No relevant content found today")

if __name__ == "__main__":
    main()