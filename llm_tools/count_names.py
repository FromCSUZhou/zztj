import json
import os
from collections import defaultdict

from loguru import logger

from llm_tools.prompt import COUNT_NAMES_PROMPT
from llm_tools.tools import call_gpt_static

# 函数定义：读取JSON文件
def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 函数定义：保存到新的JSON文件
def save_to_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


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


def merge_entries(data):
    merged_data = defaultdict(lambda: {"names": set(), "positions": set(), "occurrences": 0})

    for entry in data:
        # 找到entry中的所有名称和职位
        names = {entry.get(f"name_{i}") for i in range(1, 4) if f"name_{i}" in entry}
        positions = set()
        for i in range(1, 4):
            if f"position_{i}" in entry:
                pos = entry[f"position_{i}"]
                if isinstance(pos, list):
                    positions.update(pos)
                else:
                    positions.add(pos)
        if "position" in entry:
            pos = entry["position"]
            if isinstance(pos, list):
                positions.update(pos)
            else:
                positions.add(pos)

        # 使用其中一个名称和职位作为key进行归并
        primary_name = next(iter(names))
        primary_position = next(iter(positions)) if positions else None

        merged_data[primary_name]["names"].update(names)
        merged_data[primary_name]["positions"].update(positions)
        merged_data[primary_name]["occurrences"] += entry["occurrences"]

    # 将合并后的数据转换回所需格式
    result = []
    for key, value in merged_data.items():
        names_list = list(value["names"])
        positions_list = list(value["positions"])
        result_entry = {
            f"name_{i + 1}": name for i, name in enumerate(names_list)
        }
        for i, position in enumerate(positions_list):
            result_entry[f"position_{i + 1}"] = position
        result_entry["occurrences"] = value["occurrences"]
        result.append(result_entry)

    return result


def process_json_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)

            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # 处理数据
            merged_result = merge_entries(data)

            # 输出结果到新的JSON文件
            summary_filename = filename.replace(".json", "-summary.json")
            summary_file_path = os.path.join(folder_path, summary_filename)
            with open(summary_file_path, 'w', encoding='utf-8') as summary_file:
                json.dump(merged_result, summary_file, ensure_ascii=False, indent=4)

            print(f"Processed {filename} and saved summary as {summary_filename}")


def merge_all_summaries(folder_path, final_summary_filename):
    all_data = []

    for filename in os.listdir(folder_path):
        if filename.endswith("-summary.json"):
            file_path = os.path.join(folder_path, filename)

            # 读取summary JSON文件
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                all_data.extend(data)

    # 处理所有汇总数据
    final_merged_result = merge_entries(all_data)

    # 输出最终的汇总结果到新的JSON文件
    # final_summary_path = os.path.join(folder_path, final_summary_filename)
    with open(final_summary_filename, 'w', encoding='utf-8') as final_summary_file:
        json.dump(final_merged_result, final_summary_file, ensure_ascii=False, indent=4)

    print(f"All summaries merged and saved as {final_summary_filename}")


def json_to_excel(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    import pandas as pd

    filtered_data = [
        {
            "name_1": item.get("name_1", ""),
            "name_2": item.get("name_2", ""),
            "name_3": item.get("name_3", ""),
            "position_1": item.get("position_1", ""),
            "position_2": item.get("position_2", ""),
            "position_3": item.get("position_3", ""),
            "occurrences": item.get("occurrences", 0)
        }
        for item in data
    ]

    df = pd.DataFrame(filtered_data)
    file_path = "filtered_data.xlsx"
    df.to_excel(file_path, index=False)


def main():
    # 如果原始没有没有被处理，则使用下面的代码
    # with open("zztj_content_divided_by_paragraph.json", "r", encoding="utf-8") as f:
    #     content = json.load(f)
    #
    # count_name_position_by_paragraph(content)

    # 如果原始数据已经被处理过，则使用下面的代码
    # folder_path = "name-position-occurrences-v0.2.1"
    # process_json_files(folder_path)
    #
    # # 合并所有summary结尾的JSON文件并生成最终的summary文件
    # final_summary_filename = "final_name_summary.json"  # 最终汇总的文件名
    # merge_all_summaries(folder_path, final_summary_filename)

    # 使用下面的代码读取最终的summary文件，并到处为excel文件
    json_to_excel("final_name_summary.json")



if __name__ == "__main__":
    main()
