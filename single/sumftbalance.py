import json

# 读取 JSON 文件
json_file_path = "1.json"  # 替换为你的 JSON 文件路径
try:
    with open(json_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # 计算 ftBalance 的总和
    total_ft_balance = sum(item["ftBalance"] for item in data["ftUtxoList"])
    
    # 输出结果
    print(f"ftBalance 的总和为: {total_ft_balance}")
except FileNotFoundError:
    print(f"错误：文件 {json_file_path} 未找到。")
except KeyError:
    print("错误：JSON 数据中未找到 'ftUtxoList' 或 'ftBalance' 字段。")
except Exception as e:
    print(f"发生错误：{e}")
