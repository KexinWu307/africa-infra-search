import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse
import re

# ====================== 自定义配置（你需要改的部分）======================
# 1. 关键词组A：非洲各国/机构
KEYWORDS_GROUP_A = [
    "非洲",
    "中亚",
    "埃及",
    "毛里塔尼亚",
    "塞内加尔",
    "科特迪瓦",
    "尼日利亚",
    "喀麦隆",
    "刚果民主共和国",
    "安哥拉",
    "肯尼亚",
    "乌干达",
    "乌兹别克斯坦",
    "一带一路",
    "中非合作论坛",
    "中国政府优惠贷款",
    "中国进出口银行",
    "国家国际发展合作署",
]

# 2. 关键词组B：基础设施相关
KEYWORDS_GROUP_B = [
    "智慧城市",
    "数字政府",
    "光纤骨干网",
    "物联网",
    "光伏",
    "太阳能",
    "矿业",
    "矿山供电",
    "铁路",
    "港口",
    "公路",
    "机场",
    "基础设施",
]

# 3. 邮箱配置（必改！）
RECEIVE_EMAIL = "1418085836@qq.com"  # 接收结果的邮箱
SENDER_EMAIL = "1418085836@qq.com"   # 发件邮箱（163/QQ/企业邮箱均可）
SENDER_PASSWORD = "fptablpbheevfgii"  # 不是登录密码，是SMTP授权码
SMTP_SERVER = "smtp.qq.com"            # 163: smtp.163.com | QQ: smtp.qq.com
SMTP_PORT = 465                         # 加密端口，一般为465

# ====================== 通用请求头（防反爬）======================
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.baidu.com/",
    "Cache-Control": "max-age=0"
}

# ====================== 多平台搜索函数（修复核心问题）======================
def search_baidu(keyword):
    """百度搜索：修复结果解析，按时间从新到旧，取前10条"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        # 百度按时间排序的正确URL（增加tn=baidulocal）
        url = f"https://www.baidu.com/s?wd={encoded_keyword}&tn=baidulocal&cl=2&ct=2097152&rn=10&rsv_bp=1&rsv_spt=3&ie=utf-8&rsv_t=123"
        response = requests.get(url, headers=COMMON_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 修复：百度新版搜索结果class
        for item in soup.find_all('div', class_='result-op c-container xpath-log new-pmd')[:10]:
            # 兼容百度不同样式的标题提取
            title_tag = item.find('h3', class_='t') or item.find('h3')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link_tag = title_tag.find('a')
            if not link_tag or 'href' not in link_tag.attrs:
                continue
            link = link_tag['href']
            
            # 过滤广告
            if "ec-ad" in str(item) or "推广" in title:
                continue
            results.append((title, link))
        return results
    except Exception as e:
        print(f"百度搜索出错：{keyword} - {str(e)}")
        return []

def search_bing(keyword):
    """必应搜索：按时间从新到旧，取前10条"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://cn.bing.com/search?q={encoded_keyword}&sort=date&count=10&mkt=zh-CN"
        response = requests.get(url, headers=COMMON_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for item in soup.find_all('li', class_='b_algo')[:10]:
            title_tag = item.find('h2')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link_tag = title_tag.find('a')
            if not link_tag or 'href' not in link_tag.attrs:
                continue
            link = link_tag['href']
            results.append((title, link))
        return results
    except Exception as e:
        print(f"必应搜索出错：{keyword} - {str(e)}")
        return []

def search_google(keyword):
    """谷歌搜索：修复链接提取，按时间从新到旧，取前10条"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://www.google.com/search?q={encoded_keyword}&tbs=qdr:d&sort=date&num=10&hl=zh-CN"
        response = requests.get(url, headers=COMMON_HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for item in soup.find_all('div', class_='g')[:10]:
            title_tag = item.find('h3')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link_tag = item.find('a')
            if not link_tag or 'href' not in link_tag.attrs:
                continue
            
            # 修复：解析谷歌跳转链接，提取真实URL
            raw_link = link_tag['href']
            if raw_link.startswith('/url?q='):
                link = urllib.parse.unquote(raw_link.split('/url?q=')[1].split('&')[0])
            else:
                link = raw_link
            
            # 过滤广告
            if "googleads" in link:
                continue
            results.append((title, link))
        return results
    except Exception as e:
        print(f"谷歌搜索出错（大概率无法访问）：{keyword} - {str(e)}")
        return []

# ====================== 交叉搜索+去重（修复去重逻辑）=====================
def cross_search():
    """关键词交叉搜索，多平台汇总+去重，返回汇总结果"""
    # 修复：用字典存储结果（key=链接，value=标题），避免标题含_导致拆分错误
    all_results = {}
    total_keywords = len(KEYWORDS_GROUP_A) * len(KEYWORDS_GROUP_B)
    current = 0

    results_text = []
    results_text.append(f"【非洲基建搜索结果】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    results_text.append(f"总计交叉关键词数：{total_keywords}\n")
    results_text.append("="*80 + "\n")

    # 交叉组合关键词搜索
    for a in KEYWORDS_GROUP_A:
        for b in KEYWORDS_GROUP_B:
            keyword = f"{a} {b}"
            current += 1
            results_text.append(f"\n🔍 搜索关键词（{current}/{total_keywords}）：{keyword}")
            results_text.append("\n--- 百度结果 ---")
            
            # 1. 百度搜索
            baidu_res = search_baidu(keyword)
            if baidu_res:
                for i, (title, link) in enumerate(baidu_res, 1):
                    if link not in all_results:
                        all_results[link] = title
                        results_text.append(f"{i}. {title}")
                        results_text.append(f"   链接：{link}")
            else:
                results_text.append("   暂无有效结果")

            results_text.append("\n--- 必应结果 ---")
            # 2. 必应搜索
            bing_res = search_bing(keyword)
            if bing_res:
                for i, (title, link) in enumerate(bing_res, 1):
                    if link not in all_results:
                        all_results[link] = title
                        results_text.append(f"{i}. {title}")
                        results_text.append(f"   链接：{link}")
            else:
                results_text.append("   暂无有效结果")

            results_text.append("\n--- 谷歌结果 ---")
            # 3. 谷歌搜索（大概率失败，仅尝试）
            google_res = search_google(keyword)
            if google_res:
                for i, (title, link) in enumerate(google_res, 1):
                    if link not in all_results:
                        all_results[link] = title
                        results_text.append(f"{i}. {title}")
                        results_text.append(f"   链接：{link}")
            else:
                results_text.append("   暂无有效结果（谷歌访问失败）")

            # 优化：随机休眠1-3秒，降低反爬概率
            time.sleep(1 + (current % 3))

    # 汇总去重后的结果
    results_text.append("\n" + "="*80)
    results_text.append(f"\n📊 去重后总结果数：{len(all_results)}")
    results_text.append("\n--- 所有去重结果汇总 ---")
    for i, (link, title) in enumerate(all_results.items(), 1):
        results_text.append(f"{i}. {title}")
        results_text.append(f"   链接：{link}")

    # 限制内容长度（避免邮箱拦截）
    final_content = "\n".join(results_text)
    if len(final_content) > 50000:
        final_content = final_content[:50000] + "\n\n⚠️ 内容过长，已截断前50000字符"
    
    return final_content

# ====================== 发邮件逻辑（修复编码错误）=====================
def send_email(content):
    """发送搜索结果到指定邮箱（修复编码+优化兼容性）"""
    try:
        # 构建邮件内容（纯文本+UTF-8强制编码）
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = Header(f"Africa Infra Search <{SENDER_EMAIL}>", 'utf-8')
        msg['To'] = Header(RECEIVE_EMAIL, 'utf-8')
        msg['Subject'] = Header(f"Africa Infra Search Result {datetime.now().strftime('%Y-%m-%d')}", 'utf-8')

        # 发送邮件（移除冗余编码，简化逻辑）
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVE_EMAIL, msg.as_string())
        print("✅ 邮件发送成功！")
    except Exception as e:
        print(f"❌ 邮件发送失败：{str(e)}")
        # 打印详细错误信息，方便排查
        import traceback
        traceback.print_exc()

# ====================== 主程序（增加全局异常捕获）=====================
if __name__ == "__main__":
    try:
        print(f"🚀 开始执行非洲&中亚基建交叉搜索：{datetime.now()}")
        # 1. 执行交叉搜索
        search_result = cross_search()
        # 2. 打印结果（方便调试）
        print(search_result)
        # 3. 发送邮件
        send_email(search_result)
        print(f"🎉 任务完成：{datetime.now()}")
    except Exception as e:
        print(f"❌ 程序执行失败：{str(e)}")
        # 发送失败提醒邮件
        error_content = f"程序执行失败：{str(e)}\n{datetime.now()}"
        send_email(error_content)
