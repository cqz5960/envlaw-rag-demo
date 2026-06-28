from langchain_deepseek import ChatDeepSeek

# 初始化DeepSeek模型（替换成你的API Key）
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key="sk-2c4f44887d6d49e5b22ec2c7667ea45e",  # ← 替换成你的Key
    temperature=0.7
)

# 测试：问个问题
response = llm.invoke("你好，请介绍一下你自己")
print(response.content)