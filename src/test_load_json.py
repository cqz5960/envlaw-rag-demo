import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_path = os.path.join(BASE_DIR, "data", "processed", "ecocode_sample.json")

try:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("✅ JSON 加载成功")
    print(f"📄 法典名称: {data['title']}")
    print(f"📚 共 {len(data['articles'])} 条法条")
    
    # 显示前3条法条的编号和内容预览
    print("\n🔍 法条预览（前3条）:")
    for article in data['articles'][:3]:
        print(f"   第{article['number']}条: {article['content'][:50]}...")
        
except FileNotFoundError:
    print(f"❌ 文件未找到: {file_path}")
except json.JSONDecodeError as e:
    print(f"❌ JSON 格式错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
