import subprocess
import os
import shutil
import json
import re
import argparse # 新增导入
import difflib  # 用于生成文件差异
import zipfile  # 用于创建压缩文件
import datetime # 用于生成带时间戳的文件名

# 配置
BASE_SH_SCRIPT = "./base.sh"
TEST_SH_SCRIPT = "./test.sh"

# base.sh 输出的目录名
BASE_OUTPUT_DIR = "base"
# test.sh 实际输出的目录名 (根据 test.sh 脚本)
TEST_SH_ACTUAL_OUTPUT_DIR = "test"
# test.sh 输出重命名后的目标目录名，用于比较 (与实际目录相同，不需要重命名)
TARGET_TEST_OUTPUT_DIR = "test"

# 将输出文件格式改为 Markdown
DIFFERENCES_REPORT_FILE = "differences_report.md"
RESPONSE_FILE_PATTERN = re.compile(r"response_(\d+)\.txt")

def run_shell_script(script_path):
    """执行指定的 shell 脚本"""
    print(f"正在执行脚本: {script_path} ...")
    try:
        # 使用 bash 执行脚本
        process = subprocess.run(
            ['bash', script_path],
            capture_output=True,
            text=True,
            check=True, # 如果脚本返回非零退出码则抛出异常
            cwd="." # 在当前目录执行
        )
        print(f"脚本 {script_path} 执行成功。")
        if process.stdout:
            print("标准输出:\n", process.stdout)
        if process.stderr:
            print("标准错误:\n", process.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"脚本 {script_path} 执行失败。")
        print(f"返回码: {e.returncode}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"标准错误: {e.stderr}")
    except FileNotFoundError:
        print(f"错误: 脚本 {script_path} 未找到。")
    except Exception as e:
        print(f"执行脚本 {script_path} 时发生未知错误: {e}")
    return False

def compare_json_content(file_path1, file_path2):
    """比较两个 JSON 文件的内容"""
    try:
        with open(file_path1, 'r', encoding='utf-8') as f1, \
             open(file_path2, 'r', encoding='utf-8') as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)
            return data1 == data2, data1, data2
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误，文件: {file_path1} 或 {file_path2} - {e}")
        return False, None, None # 解析失败视为不同
    except FileNotFoundError:
        print(f"比较时文件未找到: {file_path1} 或 {file_path2}")
        return False, None, None # 文件缺失视为不同
    except Exception as e:
        print(f"比较文件 {file_path1} 和 {file_path2} 时发生错误: {e}")
        return False, None, None
        
def get_file_content_as_string(file_path):
    """安全地读取文件内容，如果文件不存在则返回适当的消息"""
    if not os.path.exists(file_path):
        return f"文件不存在: {file_path}"
    if not os.path.isfile(file_path):
        return f"路径不是一个文件: {file_path}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"读取文件时发生错误: {file_path} - {str(e)}"
        
def generate_file_diff(content1, content2):
    """生成两个文本内容之间的差异"""
    if content1 is None or content2 is None:
        return "无法生成差异比较 - 一个或多个文件内容无效"
        
    # 将内容拆分为行
    lines1 = content1.splitlines()
    lines2 = content2.splitlines()
    
    # 生成差异
    diff = difflib.unified_diff(
        lines1, lines2,
        lineterm='',
        n=3  # 上下文行数
    )
    
    # 合并差异结果
    diff_text = '\n'.join(diff)
    return diff_text if diff_text else "未检测到具体差异（可能是格式或空白字符造成）"
    
def copy_file_with_prefix(src_path, dest_dir, prefix):
    """将文件复制到目标目录，并添加前缀"""
    if not os.path.exists(src_path):
        print(f"警告: 源文件 {src_path} 不存在，无法复制")
        return False
    
    # 获取原始文件名
    filename = os.path.basename(src_path)
    # 创建带前缀的新文件名
    new_filename = f"{prefix}_{filename}"
    # 构建目标文件路径
    dest_path = os.path.join(dest_dir, new_filename)
    
    # 确保目标目录存在
    os.makedirs(dest_dir, exist_ok=True)
    
    try:
        # 复制文件
        shutil.copy2(src_path, dest_path)
        print(f"已复制: {src_path} -> {dest_path}")
        return True
    except Exception as e:
        print(f"复制文件时出错: {e}")
        return False

def create_zip_archive(source_dir, output_filename=None):
    """将目录压缩为 ZIP 文件
    
    Args:
        source_dir: 要压缩的目录路径
        output_filename: 输出的 ZIP 文件名（如果为 None，将基于目录名和当前时间生成）
        
    Returns:
        str: 创建的 ZIP 文件路径，如果失败返回 None
    """
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        print(f"错误: 目录 {source_dir} 不存在或不是一个有效的目录")
        return None
    
    # 如果没有提供输出文件名，根据源目录和当前时间生成一个
    if output_filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = os.path.basename(os.path.normpath(source_dir))
        output_filename = f"{dir_name}_{timestamp}.zip"
    
    try:
        # 确保输出文件名以 .zip 结尾
        if not output_filename.endswith('.zip'):
            output_filename += '.zip'
        
        # 创建 ZIP 文件
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径，以便保留目录结构
                    arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                    zipf.write(file_path, arcname)
        
        print(f"已成功创建 ZIP 归档: {output_filename}")
        return output_filename
    
    except Exception as e:
        print(f"创建 ZIP 归档时出错: {e}")
        return None

def get_file_number(filename):
    """从文件名中提取编号 (例如 response_1.txt -> 1)"""
    match = RESPONSE_FILE_PATTERN.match(filename)
    if match:
        return match.group(1)
    return None

def main():
    parser = argparse.ArgumentParser(description="执行脚本并比较输出，或仅比较输出。")
    parser.add_argument(
        "--skiptest",
        action="store_true",
        help="如果设置此参数，则跳过执行 base.sh 和 test.sh，直接进行比较。"
    )
    args = parser.parse_args()

    if not args.skiptest:
        # 1. 清理并创建 base.sh 的输出目录
        if os.path.exists(BASE_OUTPUT_DIR):
            print(f"正在移除已存在的目录: {BASE_OUTPUT_DIR}")
            shutil.rmtree(BASE_OUTPUT_DIR)
        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        print(f"已创建/确保目录 {BASE_OUTPUT_DIR} 存在。")

        # 清理 test.sh 可能产生的旧目录 (实际输出目录和目标比较目录)
        if os.path.exists(TARGET_TEST_OUTPUT_DIR):
            print(f"正在移除已存在的目录: {TARGET_TEST_OUTPUT_DIR}")
            shutil.rmtree(TARGET_TEST_OUTPUT_DIR)
        if os.path.exists(TEST_SH_ACTUAL_OUTPUT_DIR):
            print(f"正在移除已存在的目录: {TEST_SH_ACTUAL_OUTPUT_DIR}")
            shutil.rmtree(TEST_SH_ACTUAL_OUTPUT_DIR)

        # 2. 执行 base.sh
        # 假设 base.sh 会将其输出放入 BASE_OUTPUT_DIR
        print(f"\n--- 开始执行 {BASE_SH_SCRIPT} ---")
        if not run_shell_script(BASE_SH_SCRIPT):
            print(f"{BASE_SH_SCRIPT} 执行失败，中止操作。")
            return
        print(f"--- {BASE_SH_SCRIPT} 执行完毕 ---")

        # 3. 执行 test.sh
        print(f"\n--- 开始执行 {TEST_SH_SCRIPT} ---")
        if not run_shell_script(TEST_SH_SCRIPT):
            print(f"{TEST_SH_SCRIPT} 执行失败，中止操作。")
            return
        print(f"--- {TEST_SH_SCRIPT} 执行完毕 ---")

        # 4. 检查 test.sh 的输出目录是否存在
        if not os.path.exists(TEST_SH_ACTUAL_OUTPUT_DIR):
            print(f"错误: 脚本 {TEST_SH_SCRIPT} 未创建预期的输出目录 {TEST_SH_ACTUAL_OUTPUT_DIR}。")
            return
            
        # 由于目录名相同，不需要重命名，只需检查目录是否存在
        print(f"测试输出目录 {TEST_SH_ACTUAL_OUTPUT_DIR} 已存在，将用于比较")
    else:
        print("--- 跳过脚本执行，直接进行比较 ---")
        # 确保比较目录存在
        if not os.path.exists(BASE_OUTPUT_DIR):
            print(f"错误: 目录 {BASE_OUTPUT_DIR} 不存在。请先运行脚本或确保输出已就绪。")
            return
        if not os.path.exists(TARGET_TEST_OUTPUT_DIR):
            print(f"错误: 目录 {TARGET_TEST_OUTPUT_DIR} 不存在。请先运行脚本或确保输出已就绪。")
            return


    # 5. 比较输出文件
    print(f"\n--- 开始比较 {BASE_OUTPUT_DIR} 和 {TARGET_TEST_OUTPUT_DIR} 中的文件 ---")
    differing_file_numbers = set()

    if not os.path.isdir(BASE_OUTPUT_DIR):
        print(f"错误: {BASE_OUTPUT_DIR} 不是一个有效的目录。")
        return
    if not os.path.isdir(TARGET_TEST_OUTPUT_DIR):
        print(f"错误: {TARGET_TEST_OUTPUT_DIR} 不是一个有效的目录。")
        return

    base_dir_files = os.listdir(BASE_OUTPUT_DIR)

    for filename in base_dir_files:
        file_number = get_file_number(filename)
        if not file_number:
            print(f"跳过文件 {filename} (在 {BASE_OUTPUT_DIR} 中)，因其不符合 'response_N.txt' 格式。")
            continue

        base_file_path = os.path.join(BASE_OUTPUT_DIR, filename)
        test_file_path = os.path.join(TARGET_TEST_OUTPUT_DIR, filename)

        if not os.path.exists(test_file_path):
            print(f"差异: 文件 {filename} 存在于 {BASE_OUTPUT_DIR} 但不存在于 {TARGET_TEST_OUTPUT_DIR}。")
            differing_file_numbers.add((file_number, "missing_in_test", base_file_path, test_file_path))
        elif not os.path.isfile(test_file_path):
            print(f"差异: {test_file_path} 不是一个文件。")
            differing_file_numbers.add((file_number, "missing_in_test", base_file_path, test_file_path))
        else:
            print(f"正在比较: {base_file_path} 与 {test_file_path}")
            is_same, base_content_json, test_content_json = compare_json_content(base_file_path, test_file_path)
            if not is_same:
                print(f"差异: 文件 {filename} (编号: {file_number}) 内容不同。")
                differing_file_numbers.add((file_number, "content_different", base_file_path, test_file_path))
            else:
                print(f"相同: 文件 {filename} (编号: {file_number}) 内容一致。")

    # 检查 TARGET_TEST_OUTPUT_DIR 中存在但 BASE_OUTPUT_DIR 中不存在的文件
    test_dir_files = os.listdir(TARGET_TEST_OUTPUT_DIR)
    for filename in test_dir_files:
        file_number = get_file_number(filename)
        if not file_number:
            # print(f"跳过文件 {filename} (在 {TARGET_TEST_OUTPUT_DIR} 中)，因其不符合 'response_N.txt' 格式。")
            continue
        
        base_file_path_check = os.path.join(BASE_OUTPUT_DIR, filename)
        test_file_path = os.path.join(TARGET_TEST_OUTPUT_DIR, filename)
        if not os.path.exists(base_file_path_check):
            print(f"差异: 文件 {filename} 存在于 {TARGET_TEST_OUTPUT_DIR} 但不存在于 {BASE_OUTPUT_DIR}。")
            differing_file_numbers.add((file_number, "missing_in_base", base_file_path_check, test_file_path))

    # 6. 将有差异的文件复制到 /diff 目录，并添加前缀
    # 按编号排序差异项
    sorted_differing_items = sorted(differing_file_numbers, key=lambda x: int(x[0]))
    
    # 定义差异文件的目标目录
    DIFF_DIR = "./diff"
    # 确保目标目录存在
    os.makedirs(DIFF_DIR, exist_ok=True)
    
    if sorted_differing_items:
        # 打印差异文件编号摘要
        diff_numbers = [item[0] for item in sorted_differing_items]
        print(f"\n发现差异的文件编号: {', '.join(diff_numbers)}")
        print(f"发现 {len(sorted_differing_items)} 个有差异的文件。")
        
        # 复制每个有差异的文件
        for item in sorted_differing_items:
            number, diff_type, base_path, test_path = item
            
            if diff_type == "content_different":
                # 两个文件内容不同，都需要复制
                copy_file_with_prefix(base_path, DIFF_DIR, "base")
                copy_file_with_prefix(test_path, DIFF_DIR, "test")
                
            elif diff_type == "missing_in_base":
                # base 中缺失文件，只复制 test 中的文件
                copy_file_with_prefix(test_path, DIFF_DIR, "test")
                
            elif diff_type == "missing_in_test":
                # test 中缺失文件，只复制 base 中的文件
                copy_file_with_prefix(base_path, DIFF_DIR, "base")
    else:
        print("\n未发现任何差异。")

    print(f"\n比较完成。有差异的文件已复制到: {DIFF_DIR} 目录")
    
    # 7. 将差异目录压缩成 ZIP 文件
    if sorted_differing_items:  # 只有在有差异时才创建 ZIP 文件
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"diff_{timestamp}.zip"
        zip_path = create_zip_archive(DIFF_DIR, zip_filename)
        if zip_path:
            print(f"差异文件已压缩为: {zip_path}")

if __name__ == "__main__":
    main()