import os
import json
from bs4 import BeautifulSoup

# 文件目录路径
directory = '/Users/tuozhou/Desktop/My_PhD/Quantitative_History/zztj/后汉书/本纪'

# 初始化一个字典用于存储结果
results = {}

# 遍历目录下所有文件
for filename in os.listdir(directory):
    if filename.endswith('原文.html'):
        filepath = os.path.join(directory, filename)

        # 读取HTML文件内容
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(content, 'html.parser')

        # 查找所有<p>标签
        paragraphs = soup.find_all('p')

        # 初始化一个临时列表用于存储段落
        text_list = []
        # 遍历所有<p>标签，过滤掉不需要的内容
        for p in paragraphs:
            # 仅保留不包含其他标签的纯文本内容
            if p.find_all(recursive=False):
                continue  # 跳过包含嵌套标签的段落
            text = p.get_text(strip=True)
            if text:
                text_list.append(text)

        # 按段落存储
        if text_list:
            results[filename] = {str(i + 1): text for i, text in enumerate(text_list)}

# 将结果保存为JSON文件
output_filepath = '/Users/tuozhou/Desktop/My_PhD/Quantitative_History/zztj/llm_tools/houhanshu_content_divided_by_paragraph/houhanshu_content_divided_by_paragraph_ji.json'
with open(output_filepath, 'w', encoding='utf-8') as json_file:
    json.dump(results, json_file, ensure_ascii=False, indent=4)

print(f"处理完成，结果已保存到 {output_filepath}")
