import json

# 读取zztj_content.json文件
with open('zztj_content.json', 'r', encoding='utf-8') as file:
    zztj_content = json.load(file)

# 创建新的结构
new_content = {}

for key, value in zztj_content.items():
    # 按段落分割内容
    paragraphs = value.split('\n\n')
    # 创建子键值对
    new_paragraphs = {i+1: paragraph for i, paragraph in enumerate(paragraphs)}
    new_content[key] = new_paragraphs

# 将新的结构写入新的JSON文件
with open('zztj_content_divided_by_paragraph.json', 'w', encoding='utf-8') as file:
    json.dump(new_content, file, ensure_ascii=False, indent=4)

print("新的zztj_content_divided_by_paragraph.json文件已创建。")
