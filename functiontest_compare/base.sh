#!/bin/bash

# 创建一个目录来存储输出文件（如果它还不存在）
OUTPUT_DIR="base"
mkdir -p "$OUTPUT_DIR"

# 检查 curlall.txt 是否存在
CURL_COMMAND_FILE="./base.txt"
if [ ! -f "$CURL_COMMAND_FILE" ]; then
  echo "错误: 文件 $CURL_COMMAND_FILE 未找到。"
  exit 1
fi

# 初始化命令计数器
count=1
# 初始化一个变量来累积多行命令
current_command=""

echo "开始执行 curl 命令..."

# 逐行读取命令文件
while IFS= read -r line || [[ -n "$line" ]]; do
  # 移除可能存在的回车符（\r）
  line=$(echo "$line" | tr -d '\r')

  if [[ "$line" == curl* ]] && [[ -z "$current_command" ]]; then
    # 开始一个新的 curl 命令
    current_command="$line"
  elif [[ -n "$current_command" ]]; then
    # 追加到当前命令
    current_command="$current_command $line"
  fi

  # 检查命令是否结束（不以 \ 结尾）或文件是否结束
  if [[ -n "$current_command" ]] && ! [[ "$line" == *"\\" ]]; then
    output_file="$OUTPUT_DIR/response_$count.txt"
    echo "------------------------------------"
    echo "正在执行命令 #$count:"
    # 为了清晰起见，打印将要执行的命令（不包括输出重定向）
    # 注意：实际执行时，单引号和双引号需要正确处理，这里假设原始文件中的引号是正确的
    echo "$current_command"

    # 执行命令并将输出保存到文件
    # 使用 eval 来正确处理包含引号和变量的复杂命令字符串
    # 添加 -sS 以静默 curl 进度但显示错误
    eval "$current_command -sS -o '$output_file'"
    
    if [ $? -eq 0 ]; then
      echo "命令 #$count 执行成功。响应已保存到 $output_file"
    else
      echo "命令 #$count 执行失败。请检查 $output_file 或错误输出。"
    fi
    
    current_command="" # 重置当前命令
    count=$((count + 1))
  fi
done < "$CURL_COMMAND_FILE"

echo "------------------------------------"
echo "所有命令执行完毕。"
echo "输出文件保存在目录: $OUTPUT_DIR"