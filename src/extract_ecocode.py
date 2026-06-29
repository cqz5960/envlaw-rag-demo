"""
从 PDF 中提取《生态环境法典》法条，输出为 JSON
智能处理换行：只保留以句号/问号等结尾的段落分隔，合并行尾折行
用法：python extract_ecocode.py
"""
import pdfplumber
import json
import re

PDF_PATH = "E:/OneDrive - cug.edu.cn/文件整理/Workbuddy Files/编程与AI/envlaw-rag-demo/docs/中华人民共和国生态环境法典.pdf"
OUTPUT_PATH = "E:/OneDrive - cug.edu.cn/文件整理/Workbuddy Files/编程与AI/envlaw-rag-demo/data/processed/ecocode_full.json"

DIGITS = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
UNITS  = {'十':10,'百':100,'千':1000,'万':10000}

def cn_to_int(s: str) -> int:
    """正确转换中文数字为阿拉伯数字，支持 一~九千九百九十九"""
    if s.isdigit():
        return int(s)
    # 以十/百/千/万开头时，补一个"一"（十二 → 一十二）
    if s[0] in UNITS:
        s = '一' + s
    result = 0
    i = 0
    while i < len(s):
        if s[i] in DIGITS:
            num = DIGITS[s[i]]
            if i + 1 < len(s) and s[i+1] in UNITS:
                # 数字+单位：如 一百、二十、三千
                result += num * UNITS[s[i+1]]
                i += 2
            else:
                # 数字无单位（个位）：如 三
                result += num
                i += 1
        else:
            # 零 或其他无关字符，跳过
            i += 1
    return result

# 段落结尾标点的 Unicode 码点
PARA_END = set([0x3002, 0xFF01, 0xFF1F, 0xFF1B, 0xFF09, 0x300D, 0x300F])

def should_break(prev_line: str) -> bool:
    """上一行是否以段落结尾标点结束"""
    if not prev_line:
        return False
    return ord(prev_line[-1]) in PARA_END

def clean_content(raw: str) -> str:
    """合并行尾折行，只保留真正的段落分隔"""
    lines = raw.strip().split('\n')
    if not lines:
        return ""
    merged = [lines[0]]
    for line in lines[1:]:
        if should_break(merged[-1]):
            merged.append(line)
        else:
            merged[-1] = merged[-1] + line
    result = '\n'.join(merged)
    # 中文文本去掉所有空格（PDF 提取时字符间距会被识别为空格）
    result = result.replace(' ', '')
    return result

print("正在读取 PDF（318页），请稍候...")

with pdfplumber.open(PDF_PATH) as pdf:
    full_text = ""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            full_text += text + "\n"

print(f"提取完成，共 {len(full_text)} 字符")

# 正则：匹配"第X条"，X 可以是阿拉伯数字或中文数字
pattern = re.compile(r'第([\d一二三四五六七八九十百千万]+)条\s*')
matches = list(pattern.finditer(full_text))
print(f"找到 {len(matches)} 个法条匹配")

articles = []
for i, match in enumerate(matches):
    num_str = match.group(1)
    num = cn_to_int(num_str)
    start = match.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
    raw_content = full_text[start:end]
    content = clean_content(raw_content)
    if content and num > 0:
        articles.append({"number": num, "content": content})

# 去重（同一条号取最长内容）
seen = {}
for art in articles:
    n = art["number"]
    if n not in seen or len(art["content"]) > len(seen[n]["content"]):
        seen[n] = art

articles = sorted(seen.values(), key=lambda x: x["number"])
print(f"去重后共 {len(articles)} 条法条")
if articles:
    print(f"条号范围：第 {articles[0]['number']} 条 ~ 第 {articles[-1]['number']} 条")
    # 验证前3条
    for art in articles[:3]:
        print(f"  第{art['number']}条：{art['content'][:40]}...")

output = {
    "title": "中华人民共和国生态环境法典",
    "articles": articles
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"已保存到：{OUTPUT_PATH}")
