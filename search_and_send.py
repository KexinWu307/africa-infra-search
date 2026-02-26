import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse

# ====================== 自定义配置（你需要改的部分）======================
# 1. 关键词组A：非洲各国/机构
KEYWORDS_GROUP_A = [
    "非洲 Africa",
    "撒哈拉以南非洲 Sub-Saharan Africa",
    "北非 North Africa",
    "南非 Southern Africa",
    "西非 West Africa",
    "东非 East Africa",
    "南部非洲发展共同体 SADC",
    "西非国家经济共同体 ECOWAS",
    "非洲大陆自由贸易区 AfCFTA",
    "中亚 Central Asia",
    "埃及 Egypt",
    "利比亚 Libya",
    "毛里塔尼亚 Mauritania",
    "塞内加尔 Senegal",
    "科特迪瓦 Cote d‘Ivoire",
    "尼日利亚 Nigeria",
    "喀麦隆 Cameroon",
    "刚果民主共和国 DRC",
    "安哥拉 Angola",
    "肯尼亚 Kenya",
    "乌干达 Uganda",
    "哈萨克斯坦 Kazakhstan",
    "乌兹别克斯坦 Uzbekistan",
    "一带一路 Belt and Road",
    "中非合作论坛 FOCAC",
    "中国政府优惠贷款 Concessional Loan",
    "中国进出口银行 China Exim Bank",
    "国家国际发展合作署 CIDCA",
]

# 2. 关键词组B：基础设施相关
KEYWORDS_GROUP_B = [
    "智慧城市 Smart City",
    "数字政府 e-Government",
    "光纤骨干网 Fiber Backbone",
    "物联网 IoT",
    "光伏 Solar PV",
    "太阳能 Solar Power",
    "电站 Power Plant",
    "电网 Power Grid",
    "输变电 Transmission Line",
    "变电站 Substation",
    "矿业 Mining",
    "矿山供电 Mine Power Supply",
    "源网荷储 Source-Grid-Load-Storage",
    "铁路 Railway",
    "港口 Port",
    "公路 Highway",
    "机场 Airport",
    "基础设施 Infrastructure",
    "公共工程 Public Works",
]

# 3. 接收结果的邮箱
RECEIVE_EMAIL = "你的邮箱@xxx.com"

# ====================== 多平台搜索函数（核心修改）======================
def search_baidu(keyword):
    """百度搜索：按时间从新到旧，取前10条"""
    try:
        # 百度按时间排序的URL（tn=baidurt&ct=2097152&si=baidu.com&wd=关键词&bs=关键词&rsv_bp=0&rsv_spt=3&cl=2&f=8&rn=10&tn=baidurt&qbl=relate_question_0&wd=关键词&rqlang=cn&rs_src=0&rsv_pq=8a9c8c8c00008c8c&rsv_t=8c8c8c8c8c8c8c8c&rsv_btype=t&inputT=12345&rsv_sug3=12&rsv_sug1=12&rsv_sug7=100&rsv_sug2=0&rsv_sug4=12345）
        encoded_keyword = urllib.parse.quote(keyword)
        url = f"https://www.baidu.com/s?wd={encoded_keyword}&tn=baidurt&ct=2097152&rn=10&rqlang=cn&bs={encoded_keyword}&rsv_bp=1&rsv_spt=3&cl=2&f=8&rsv_sug2=0&inputT=0&rsv_sug4=0"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 提取百度按时间排序的结果
        for item in soup.find_all('div', class_='result-op c-container xpath-log new-pmd')[:10]:
            title_tag = item.find('h3', class_='t')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link_tag = title_tag.find('a')
            if not link_tag:
                continue
            link = link_tag['href']
            # 过滤广告（百度广告class含"ec-ad"）
            if "ec-ad" in str(item):
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
        # 必应按时间排序URL（sort=date）
        url = f"https://cn.bing.com/search?q={encoded_keyword}&sort=date&count=10"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 提取必应结果
        for item in soup.find_all('li', class_='b_algo')[:10]:
            title_tag = item.find('h2')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link_tag = title_tag.find('a')
            if not link_tag:
                continue
            link = link_tag['href']
            results.append((title, link))
        return results
    except Exception as e:
        print(f"必应搜索出错：{keyword} - {str(e)}")
        return []

def search_google(keyword):
    """谷歌搜索：按时间从新到旧，取前10条（注意：GitHub服务器可能无法访问谷歌，失败则跳过）"""
    try:
        encoded_keyword = urllib.parse.quote(keyword)
        # 谷歌按时间排序URL（tbs=qdr:d&sort=date）
        url = f"https://www.google.com/search?q={encoded_keyword}&tbs=qdr:d&sort=date&num=10"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # 提取谷歌结果
        for item in soup.find_all('div', class_='g')[:10]:
            title_tag = item.find('h3')
            if not title_tag:
                continue
            title = title_tag.get_text().strip()
            link_tag = item.find('a')
            if not link_tag:
                continue
            link = link_tag['href']
            # 过滤谷歌广告
            if "googleads" in link:
                continue
            results.append((title, link))
        return results
    except Exception as e:
        print(f"谷歌搜索出错（大概率无法访问）：{keyword} - {str(e)}")
        return []

# ====================== 交叉搜索+去重 ======================
def cross_search():
    """关键词交叉搜索，多平台汇总+去重，返回汇总结果"""
    # 存储所有结果（用集合去重，key为标题+链接的组合）
    all_results = set()
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
                    # 用标题+链接作为唯一标识去重
                    unique_key = f"{title}_{link}"
                    if unique_key not in all_results:
                        all_results.add(unique_key)
                        results_text.append(f"{i}. {title}")
                        results_text.append(f"   链接：{link}")
            else:
                results_text.append("   暂无有效结果")

            results_text.append("\n--- 必应结果 ---")
            # 2. 必应搜索
            bing_res = search_bing(keyword)
            if bing_res:
                for i, (title, link) in enumerate(bing_res, 1):
                    unique_key = f"{title}_{link}"
                    if unique_key not in all_results:
                        all_results.add(unique_key)
                        results_text.append(f"{i}. {title}")
                        results_text.append(f"   链接：{link}")
            else:
                results_text.append("   暂无有效结果")

            results_text.append("\n--- 谷歌结果 ---")
            # 3. 谷歌搜索（大概率失败，仅尝试）
            google_res = search_google(keyword)
            if google_res:
                for i, (title, link) in enumerate(google_res, 1):
                    unique_key = f"{title}_{link}"
                    if unique_key not in all_results:
                        all_results.add(unique_key)
                        results_text.append(f"{i}. {title}")
                        results_text.append(f"   链接：{link}")
            else:
                results_text.append("   暂无有效结果（谷歌访问失败）")

            # 延长等待时间，降低反爬概率
            time.sleep(2)

    # 汇总去重后的结果（可选：单独列出所有去重结果）
    results_text.append("\n" + "="*80)
    results_text.append(f"\n📊 去重后总结果数：{len(all_results)}")
    results_text.append("\n--- 所有去重结果汇总 ---")
    for i, unique_key in enumerate(all_results, 1):
        title, link = unique_key.split("_", 1)  # 拆分唯一标识
        results_text.append(f"{i}. {title}")
        results_text.append(f"   链接：{link}")

    return "\n".join(results_text)

# ====================== 发邮件逻辑（无修改）=====================
def send_email(content):
    """发送搜索结果到指定邮箱"""
    # 配置你的发件邮箱SMTP（必改！）
    SMTP_SERVER = "smtp.163.com"  # 比如163邮箱是smtp.163.com，QQ是smtp.qq.com
    SMTP_PORT = 465  # 加密端口，一般是465
    SENDER_EMAIL = "你的发件邮箱@163.com"  # 发件邮箱
    SENDER_PASSWORD = "你的邮箱授权码"  # 不是登录密码，是SMTP授权码！

    # 构建邮件内容（适配长内容）
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = Header(f"非洲基建搜索工具 <{SENDER_EMAIL}>", 'utf-8')
    msg['To'] = Header(RECEIVE_EMAIL, 'utf-8')
    msg['Subject'] = Header(f"【每日推送】非洲基建搜索结果 {datetime.now().strftime('%Y-%m-%d')}", 'utf-8')

    # 发送邮件
    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVE_EMAIL, msg.as_string())
        server.quit()
        print("邮件发送成功！")
    except Exception as e:
        print(f"邮件发送失败：{str(e)}")
        raise e

# ====================== 主程序 ======================
if __name__ == "__main__":
    # 1. 执行交叉搜索
    search_result = cross_search()
    # 2. 发送邮件
    send_email(search_result)
