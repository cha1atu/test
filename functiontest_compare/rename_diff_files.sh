#!/bin/bash

# 设置工作目录
WORK_DIR="./"
API_FILE="$WORK_DIR/api.txt"
DIFF_DIR="$WORK_DIR/diff"

# 确保api.txt文件存在
if [ ! -f "$API_FILE" ]; then
    echo "错误: $API_FILE 文件不存在!"
    exit 1
fi

# 确保diff目录存在
if [ ! -d "$DIFF_DIR" ]; then
    echo "错误: $DIFF_DIR 目录不存在!"
    exit 1
fi

# 遍历diff目录下的所有txt文件
for file in "$DIFF_DIR"/*.txt; do
    # 获取文件名(不含路径)
    filename=$(basename "$file")
    
    # 使用正则表达式提取文件名中的数字
    if [[ $filename =~ _([0-9]+)\.txt$ ]]; then
        # 提取数字部分
        line_number="${BASH_REMATCH[1]}"
        
        # 从api.txt获取对应行的内容，并去除前后空格
        line_content=$(sed -n "${line_number}p" "$API_FILE" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        
        # 如果找到了内容，则重命名文件
        if [ -n "$line_content" ]; then
            # 构建新文件名: 原文件名_api内容.txt
            new_filename="${filename%.txt}_${line_content}.txt"
            
            # 替换新文件名中的空格为下划线(如果需要)
            new_filename=$(echo "$new_filename" | sed 's/ /_/g')
            
            # 重命名文件
            mv "$file" "$DIFF_DIR/$new_filename"
            echo "已重命名: $filename -> $new_filename"
        else
            echo "警告: 在api.txt中找不到第${line_number}行内容，文件 $filename 未重命名"
        fi
    else
        echo "警告: 文件名 $filename 不符合预期格式，跳过处理"
    fi
done

echo "处理完成!"
