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
    "https://www.nature.com/natmachintell.rss",
    "https://www.nature.com/natrevmats.rss",
    "https://www.nature.com/nphys.rss",
    "https://www.nature.com/natrevchem.rss",
    "https://www.nature.com/natelectron.rss",
    "https://www.nature.com/nnano.rss",
    "https://www.nature.com/nphoton.rss",
    "https://www.nature.com/natrevphys.rss",
    "https://www.nature.com/ncomms.rss",
    "https://www.nature.com/npjcompumats.rss",
    "https://academic.oup.com/rss/site_5332/3198.xml",
    "https://rss.sciencedirect.com/publication/science/20959273",
    "http://feeds.feedburner.com/acs/jacsat",
    "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=ancac3",
    "https://onlinelibrary.wiley.com/action/showFeed?jc=15213773&type=etoc&feed=rss",
    "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=nalefd",
    "https://www.annualreviews.org/action/showFeed?ui=45mu4&mi=3fndc3&ai=68t8&jc=conmatphys&type=etoc&feed=atom",
    "https://www.annualreviews.org/action/showFeed?ui=45mu4&mi=3fndc3&ai=sy&jc=physchem&type=etoc&feed=atom",
    "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=jpclcd",
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
    "https://pubs.acs.org/action/showFeed?type=axatoc&feed=rss&jc=chreay",
    'http://feeds.feedburner.com/acs/nalefd',
    'http://feeds.feedburner.com/acs/achre4',
    "http://feeds.feedburner.com/physicstodaynews",
    'https://iopscience.iop.org/journal/rss/2632-2153',
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
from datetime import datetime, timedelta
import re
from github import Github
import pytz
import translators.server as tss
import time
import requests

# 配置参数
FERRO_KEYWORDS = [
    "ferroelec",
    "ferromag",
    "ferroic",
    "magnetic",
]

ML_KEYWORDS = [
    "neural network",
    "learning",
]

DFT_KEYWORDS = [
    "NONADABATIC",
    "QUANTUM DYNAMIC",
    "TDDFT",
    "TIME DEPENDENT DENSITY",
    "density functional",
]


# 企业微信机器人webhook
WECHAT_WEBHOOK_FERRO = os.getenv('WECHAT_WEBHOOK_FERRO')
WECHAT_WEBHOOK_ML = os.getenv('WECHAT_WEBHOOK_ML')
WECHAT_WEBHOOK_DFT = os.getenv('WECHAT_WEBHOOK_DFT')

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
    
    if check_keywords(text, ML_KEYWORDS):
        return "ML"
    elif check_keywords(text, FERRO_KEYWORDS):
        return "ferro"
    elif check_keywords(text, DFT_KEYWORDS):
        return "DFT"
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
    
    if hasattr(entry, 'dc_creator'):
        authors = entry.dc_creator.split(', ')
        content += f"**Authors:** {', '.join(authors)}\n\n"
    else:
        print('Missing author information: ', entry)
    
    if hasattr(entry, 'summary'):
        # content += f"## Original Summary\n{entry.summary}\n\n"
        # summary = translate_text(entry.summary)
        summary = entry.summary
        # if summary_zh != entry.summary:
        content += f"{summary}\n\n"
    
    return content

def send_to_wechat(content, webhook_url):
    """发送消息到企业微信群，如果内容过长则分割成多条消息"""
    headers = {'Content-Type': 'application/json'}
    max_length = 1500  # 企业微信单条消息的最大长度

    # 将内容分割成多个部分
    parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]

    for i, part in enumerate(parts):
        data = {
            "msgtype": "text",
            "text": {
                "content": f"(Part {i+1}/{len(parts)})\n\n{part}"
            }
        }
        response = requests.post(webhook_url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Failed to send message part {i+1} to WeChat: {response.text}")
        time.sleep(1)  # 添加短暂延迟以避免频率限制

def Science_Bulletin_extract(rss_entry):
    """Extract publication date as a datetime object and author information from RSS entry."""
    # Parse the entry using BeautifulSoup
    soup = BeautifulSoup(rss_entry, 'xml')
    
    # Extract the description
    description = soup.find('description').text
    
    # Extract the publication date using regex
    date_match = re.search(r'Publication date:\s*(.*)', description)
    publication_date_str = date_match.group(1) if date_match else "Date not found"
    
    # Convert the publication date string to a datetime object
    # Assuming the format is "Available online DD Month YYYY"
    try:
        publication_date = publication_date_str.replace('Available online ', '').replace('</p>', '')
    except ValueError:
        publication_date = None  # Handle cases where the date format is unexpected
    
    # Extract authors using regex
    author_match = re.search(r'Author\(s\):\s*(.*)', description)
    authors = author_match.group(1).split(', ') if author_match else ["Authors not found"]
    
    return publication_date, authors

def main():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    
    now = datetime.now(TIMEZONE)
    year_month = now.strftime("%Y-%m")
    today = now.strftime("%Y-%m-%d")
    
    # 为每个类别创建单独的内容列表
    ferro_content = []
    ml_content = []
    DFT_content = []
    
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
                elif 'Science Bulletin' in entry:
                    entry_date, authors = Science_Bulletin_extract(entry)
                else:
                    # 如果没有日期信息，直接读取这个 entry
                    print(f"Fail to load the date of {entry}")
                    entry_date = now.date() - timedelta(days = 1)
                
                # 检查是否是昨天的内容
                if entry_date == now.date() - timedelta(days = 1):
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
                        elif category == "DFT":
                            DFT_content.append(formatted_content)
                        print(f"Found {category} content: {title}")
                
        except Exception as e:
            print(f"Error processing feed {feed_url}: {str(e)}")
    
    # 处理和保存每个类别的内容
    for category, content_list in [("ferro", ferro_content), ("ML", ml_content), ("DFT", DFT_content)]:
        if content_list:
            all_content = "\n---\n".join(content_list)
            
            try:
                # ... (GitHub 相关操作保持不变)
                
                print(f"Successfully updated {category} content for {today}")
                
                # 发送到企业微信群
                wechat_content = f"# {category.upper()} 更新 ({today})\n\n{all_content}"
                
                # 根据类别选择相应的 webhook URL
                if category == "ferro":
                    webhook_url = WECHAT_WEBHOOK_FERRO
                elif category == "ML":
                    webhook_url = WECHAT_WEBHOOK_ML
                elif category == "DFT":
                    webhook_url = WECHAT_WEBHOOK_DFT
                else:
                    print(f"Unknown category: {category}")
                    continue

                send_to_wechat(wechat_content, webhook_url)
                
            except Exception as e:
                print(f"Error occurred while saving {category} content: {str(e)}")


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
                
            except Exception as e:
                print(f"Error occurred while saving {category} content: {str(e)}")
    
    if not ferro_content and not ml_content and not DFT_content:
        print("No relevant content found today")

if __name__ == "__main__":
    main()
