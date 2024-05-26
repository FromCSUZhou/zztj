import json

from loguru import logger

from llm_tools.prompt import COUNT_NAMES_PROMPT
from llm_tools.tools import call_gpt_static


def count_name_position_by_full_content(content: dict):
    for key, value in content.items():
        file_name = key
        content_text = value

        # 生成用于调用GPT模型的内容
        llm_content = COUNT_NAMES_PROMPT.format(file_name=file_name, content=content_text)
        # print(llm_content)

        result = call_gpt_static(
            query=[{"role": "user", "content": llm_content}],
            model='gpt-4o', temperature=0.5)["content"]

        # 提取JSON内容并转换格式
        bracket_index = result.find('[')
        bracket_last = result.rfind(']')
        result = result[bracket_index:bracket_last + 1]

        logger.info(file_name + "*OUTPUT*: " + result)

        result_content_json = json.loads(result)

        # 遍历result_content_json并统计每个名字在content_text中出现的次数
        for entry in result_content_json:
            name = entry['name']
            occurrences = content_text.count(name)
            entry['occurrences'] = occurrences

        with open(f"name-position-occurrences-v0.2/{file_name}.json", "w", encoding="utf-8") as f:
            json.dump(result_content_json, f, ensure_ascii=False, indent=4)

        logger.info(f"Saved {file_name}.json")


def count_name_position_by_paragraph(content: dict):
    for key, value in content.items():
        file_name = key
        content_dict = value

        # 按照每三段进行拼接
        segments = []
        current_segment = ""
        segment_counter = 0

        for segment_key in sorted(content_dict.keys(), key=int):
            segment_counter += 1
            current_segment += content_dict[segment_key] + "\n"
            if segment_counter % 3 == 0:
                segments.append(current_segment)
                current_segment = ""

        # 如果还有剩余的段落
        if current_segment:
            segments.append(current_segment)

        final_result_content_json = []

        # 处理每个段落
        for segment in segments:
            # 生成用于调用GPT模型的内容
            llm_content = COUNT_NAMES_PROMPT.format(file_name=file_name, content=segment)

            result = call_gpt_static(
                query=[{"role": "user", "content": llm_content}],
                model='deepseek-chat', temperature=0.5)["content"]

            # 提取JSON内容并转换格式
            bracket_index = result.find('[')
            bracket_last = result.rfind(']')
            result = result[bracket_index:bracket_last + 1]

            logger.info(file_name + "*OUTPUT*: " + result)

            result_content_json = json.loads(result)

            # 遍历result_content_json并统计每个名字在segment中出现的次数
            for entry in result_content_json:
                names = [entry.get(f'name_{i}') for i in range(1, 4) if entry.get(f'name_{i}')]
                entry['occurrences'] = sum(segment.count(name) for name in names)

            final_result_content_json.extend(result_content_json)

        # 将最终的result_content_json写入一个文件
        with open(f"name-position-occurrences-v0.2.2/{file_name}.json", "w", encoding="utf-8") as f:
            json.dump(final_result_content_json, f, ensure_ascii=False, indent=4)

        logger.info(f"Saved {file_name}.json")


def main():
    with open("zztj_content_divided_by_paragraph.json", "r", encoding="utf-8") as f:
        content = json.load(f)

    count_name_position_by_paragraph(content)


if __name__ == "__main__":
    main()
