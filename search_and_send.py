import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import time
from datetime import datetime

# ====================== 自定义配置（你需要改的部分）======================
# 1. 关键词组A：非洲各国/机构（替换成你的完整列表）
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

# 2. 关键词组B：基础设施相关（替换成你的完整列表）
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
RECEIVE_EMAIL = "1418085836@qq.com"

# ====================== 搜索逻辑 ======================
def cross_search():
    """关键词交叉搜索，返回汇总结果"""
    results = []
    results.append(f"【非洲基建搜索结果】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    results.append("="*50 + "\n")

    # 交叉组合关键词搜索（这里用百度搜索示例）
    for a in KEYWORDS_GROUP_A:
        for b in KEYWORDS_GROUP_B:
            keyword = f"{a} {b}"
            results.append(f"\n🔍 搜索关键词：{keyword}")
            
            # 百度搜索接口（无需APIKey，适合零基础）
            try:
                url = f"https://www.baidu.com/s?wd={requests.utils.quote(keyword)}"
                # 添加请求头，模拟浏览器访问
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # 简单提取前3条结果标题（零基础友好版，不搞复杂解析）
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                search_results = soup.find_all('h3', class_='t')[:3]
                
                if search_results:
                    for i, res in enumerate(search_results, 1):
                        title = res.get_text().strip()
                        link = res.find('a')['href']
                        results.append(f"{i}. {title}")
                        results.append(f"   链接：{link}")
                else:
                    results.append("   暂无有效结果")
                    
            except Exception as e:
                results.append(f"   搜索出错：{str(e)}")
            
            time.sleep(1)  # 避免请求过快被封

    return "\n".join(results)

# ====================== 发邮件逻辑 ======================
def send_email(content):
    """发送搜索结果到指定邮箱"""
    # 配置你的发件邮箱SMTP（必改！看下面的说明）
    SMTP_SERVER = "smtp.qq.com"  # 比如163邮箱是smtp.163.com，QQ是smtp.qq.com
    SMTP_PORT = 465  # 加密端口，一般是465
    SENDER_EMAIL = "1418085836@qq.com"  # 发件邮箱
    SENDER_PASSWORD = "mlggihpdnertgaca"  # 不是登录密码，是SMTP授权码！

    # 构建邮件内容
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
