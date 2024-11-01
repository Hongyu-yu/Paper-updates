# 配置参数
RSS_FEEDS = [
    "http://feeds.aps.org/rss/allsuggestions.xml",
    'http://feeds.aps.org/rss/recent/prl.xml',
    "http://feeds.aps.org/rss/recent/prx.xml",
    "http://feeds.aps.org/rss/recent/physics.xml",
    'http://feeds.aps.org/rss/recent/rmp.xml',
    'https://phys.org/rss-feed/physics-news/',
    'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science',
    'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv',
    'https://www.nature.com/nature.rss',
    "https://www.nature.com/natcomputsci.rss",
    "https://www.nature.com/nchem.rss",
    "http://www.nature.com/nphys/journal/vaop/ncurrent/rss.rdf",
    "https://www.nature.com/npjcompumats.rss",
    "https://academic.oup.com/rss/site_5332/3198.xml",
    "https://rss.sciencedirect.com/publication/science/20959273",
    'https://www.pnas.org/rss/Physics.xml',
    'https://www.pnas.org/rss/Applied_Physical_Sciences.xml',
    "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jctcce",
    'https://aip.scitation.org/action/showFeed?type=etoc&feed=rss&jc=jcp',
    "http://aip.scitation.org/action/showFeed?type=etoc&feed=rss&jc=apl",
    "https://pubs.aip.org/rss/site_1000043/1000024.xml",
    "http://feeds.aps.org/rss/recent/prxenergy.xml",
    "http://feeds.aps.org/rss/recent/prmaterials.xml",
    "http://feeds.aps.org/rss/recent/prresearch.xml",
    "http://feeds.aps.org/rss/recent/prb.xml",
    'http://feeds.feedburner.com/acs/nalefd',
    'http://feeds.feedburner.com/acs/achre4',
    "http://feeds.feedburner.com/physicstodaynews",
    'https://onlinelibrary.wiley.com/action/showFeed?jc=15214095&type=etoc&feed=rss',
    'https://onlinelibrary.wiley.com/action/showFeed?jc=16163028&type=etoc&feed=rss',
    'https://onlinelibrary.wiley.com/action/showFeed?jc=21983844&type=etoc&feed=rss',
    'http://export.arxiv.org/rss/cond-mat',
    'http://export.arxiv.org/rss/physics',
    'https://chemrxiv.org/engage/rss/chemrxiv',
    "https://www.researchsquare.com/rss.xml",
    # 添加更多RSS源
]

import feedparser
import os
from datetime import datetime
import re
from github import Github
import pytz
import translators.server as tss
import time
import requests

# 配置参数
FERRO_KEYWORDS = [
    "ferroelec",
    "ferromag"
]

ML_KEYWORDS = [
    "neural network",
    "machine",
    "learning",
]

ML_DFT_KEYWORDS = [
    "machine learning",
    "density functional"
]


# 企业微信机器人webhook
WECHAT_WEBHOOK = os.getenv('WECHAT_WEBHOOK')

# GitHub配置
GITHUB_TOKEN = os.getenv('MY_GITHUB_TOKEN')
REPO_NAME = "Hongyu-yu/Paper-updates"
TIMEZONE = pytz.timezone('UTC')

def translate_text(text, retry_count=3):
    """翻译文本，带有重试机制"""
    if not text:
        return text
        
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        return text
        
    for i in range(retry_count):
        try:
            translated = tss.translate_text(
                text,
                to_language='zh',
                from_language='en',
                translator='alibaba'
            )
            time.sleep(1)
            return translated
        except Exception as e:
            if i == retry_count - 1:
                print(f"Translation failed: {str(e)}")
                return text
            time.sleep(2)
    return text

def check_keywords(text, keywords):
    """检查文本是否包含特定关键词组中的词"""
    if not text:
        return False
    text = text.lower()
    return any(keyword.lower() in text for keyword in keywords)

def get_category(title, description):
    """确定文章属于哪个类别"""
    text = f"{title} {description}".lower()
    
    if check_keywords(text, FERRO_KEYWORDS):
        return "ferro"
    elif all(keyword.lower() in text for keyword in ML_DFT_KEYWORDS):
        return "ML_DFT"
    elif check_keywords(text, ML_KEYWORDS):
        return "ML"
    return None

def format_content(entry):
    """格式化文章内容"""
    date = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    
    title = entry.title
    title_zh = translate_text(title)
    
    content = f"# {title}\n\n"
    if title_zh != title:
        content += f"## {title_zh}\n\n"
    
    content += f"Link: {entry.link}\n\n"
    
    if hasattr(entry, 'summary'):
        # content += f"## Original Summary\n{entry.summary}\n\n"
        summary_zh = translate_text(entry.summary)
        # if summary_zh != entry.summary:
        content += f"{summary_zh}\n\n"
    
    return content

def send_to_wechat(content):
    """发送消息到企业微信群，如果内容过长则分割成多条消息"""
    headers = {'Content-Type': 'application/json'}
    max_length = 1000  # 企业微信单条消息的最大长度

    # 将内容分割成多个部分
    parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]

    for i, part in enumerate(parts):
        data = {
            "msgtype": "text",
            "text": {
                "content": f"(Part {i+1}/{len(parts)})\n\n{part}"
            }
        }
        response = requests.post(WECHAT_WEBHOOK, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Failed to send message part {i+1} to WeChat: {response.text}")
        time.sleep(1)  # 添加短暂延迟以避免频率限制

def main():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    now = datetime.now(TIMEZONE)
    year_month = now.strftime("%Y-%m")
    today = now.strftime("%Y-%m-%d")
    
    # 为每个类别创建单独的内容列表
    ferro_content = []
    ml_content = []
    ml_dft_content = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Processing feed: {feed_url}")
            
            for entry in feed.entries:
                # 获取 entry 的发布日期
                if 'published_parsed' in entry:
                    entry_date = datetime(*entry.published_parsed[:6]).date()
                elif 'updated_parsed' in entry:
                    entry_date = datetime(*entry.updated_parsed[:6]).date()
                else:
                    # 如果没有日期信息，直接读取这个 entry
                    entry_date = now.date()
                
                # 检查是否是今天的内容
                if entry_date == now.date():
                    title = entry.get('title', '')
                    description = entry.get('description', '')
                    
                    # 确定文章类别
                    category = get_category(title, description)
                    if category:
                        formatted_content = format_content(entry)
                        if category == "ferro":
                            ferro_content.append(formatted_content)
                        elif category == "ML":
                            ml_content.append(formatted_content)
                        elif category == "ML_DFT":
                            ml_dft_content.append(formatted_content)
                        print(f"Found {category} content: {title}")
                
        except Exception as e:
            print(f"Error processing feed {feed_url}: {str(e)}")
    
    # 处理和保存每个类别的内容
    for category, content_list in [("ferro", ferro_content), ("ML", ml_content), ("ML_DFT", ml_dft_content)]:
        if content_list:
            all_content = "\n---\n".join(content_list)
            
            try:
                # 确保类别文件夹存在
                folder_path = f"{category}/{year_month}"
                try:
                    repo.get_contents(folder_path)
                except:
                    try:
                        repo.get_contents(f"{category}")
                    except:
                        repo.create_file(
                            f"{category}/.gitkeep",
                            f"Create folder for {category}",
                            ""
                        )
                    repo.create_file(
                        f"{folder_path}/.gitkeep",
                        f"Create folder for {category}/{year_month}",
                        ""
                    )
                
                # 创建或更新文件
                file_path = f"{folder_path}/{today}.md"
                try:
                    file = repo.get_contents(file_path)
                    repo.update_file(
                        file_path,
                        f"Update {category} content for {today}",
                        all_content,
                        file.sha
                    )
                except:
                    repo.create_file(
                        file_path,
                        f"Add {category} content for {today}",
                        all_content
                    )
                    
                print(f"Successfully updated {category} content for {today}")
                
                # 发送到企业微信群
                wechat_content = f"# {category.upper()} 更新 ({today})\n\n{all_content[:2000]}..."  # 限制长度
                send_to_wechat(wechat_content)
                
            except Exception as e:
                print(f"Error occurred while saving {category} content: {str(e)}")
    
    if not ferro_content and not ml_content and not ml_dft_content:
        print("No relevant content found today")

if __name__ == "__main__":
    main()