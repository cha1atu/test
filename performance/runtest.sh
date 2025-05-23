#!/bin/bash

# 默认参数
JMX_DIR="./jmx"
OUTPUT_DIR="result"
GENERATE_JTL=true
GENERATE_REPORT=false
REPORT_DIR="report"
MERGE_REPORT=false
MERGE_REPORT_DIR="merged_report"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -d|--jmx-dir)
      JMX_DIR="$2"
      shift 2
      ;;
    -o|--output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --no-jtl)
      GENERATE_JTL=false
      shift
      ;;
    -r|--report)
      GENERATE_REPORT=true
      shift
      ;;
    --report-dir)
      REPORT_DIR="$2"
      shift 2
      ;;
    -m|--merge-report)
      MERGE_REPORT=true
      shift
      ;;
    --merge-dir)
      MERGE_REPORT_DIR="$2"
      shift 2
      ;;
    *)
      echo "未知参数: $1"
      echo "用法: $0 [-d|--jmx-dir <目录>] [-o|--output-dir <目录>] [--no-jtl] [-r|--report] [--report-dir <目录>] [-m|--merge-report] [--merge-dir <目录>]"
      exit 1
      ;;
  esac
done

# 创建输出目录（如果不存在）
mkdir -p "$OUTPUT_DIR"

# 如果需要报告，创建报告目录
if [ "$GENERATE_REPORT" = true ]; then
  mkdir -p "$REPORT_DIR"
fi

# 如果需要合并报告，创建合并报告目录
if [ "$MERGE_REPORT" = true ]; then
  mkdir -p "$MERGE_REPORT_DIR"
fi

# 检查JMX目录是否存在
if [ ! -d "$JMX_DIR" ]; then
  echo "错误: JMX目录 '$JMX_DIR' 不存在"
  exit 1
fi

# 用于存储所有生成的JTL文件路径
all_jtl_files=()

# 遍历JMX_DIR目录下的所有.jmx文件
for jmx_file in "$JMX_DIR"/*.jmx; do
    # 检查文件是否存在
    if [ -f "$jmx_file" ]; then
        # 提取文件名（不含扩展名）
        filename=$(basename "$jmx_file" .jmx)
        
        # 定义输出文件路径
        log_file="$OUTPUT_DIR/${filename}.log"
        jtl_file="$OUTPUT_DIR/${filename}.jtl"
        test_report_dir="$REPORT_DIR/$filename"

        # 检查结果文件是否已存在
        if [ -f "$log_file" ] && ([ ! $GENERATE_JTL = true ] || [ -f "$jtl_file" ]); then
            echo "跳过: $jmx_file 的结果文件已存在"
            # 如果JTL文件存在且需要合并报告，将其添加到列表中
            if [ "$MERGE_REPORT" = true ] && [ -f "$jtl_file" ]; then
                all_jtl_files+=("$jtl_file")
            fi
            continue
        fi
        
        # 运行jmeter
        echo "正在处理: $jmx_file"
        
        if [ "$GENERATE_JTL" = true ]; then
            jmeter -n -t "$jmx_file" -l "$jtl_file" -j "$log_file"
            
            # 检查jmeter执行是否成功
            if [ $? -eq 0 ]; then
                echo "完成: $jmx_file -> 输出保存在 $jtl_file 和 $log_file"
                # 将成功生成的JTL文件添加到列表中，用于稍后合并
                if [ "$MERGE_REPORT" = true ]; then
                    all_jtl_files+=("$jtl_file")
                fi
                
                # 如果需要生成单独报告
                if [ "$GENERATE_REPORT" = true ]; then
                    echo "正在为 $jmx_file 生成报告..."
                    mkdir -p "$test_report_dir"
                    jmeter -g "$jtl_file" -o "$test_report_dir"
                    
                    if [ $? -eq 0 ]; then
                        echo "报告生成完成: $test_report_dir"
                    else
                        echo "错误: 为 $jmx_file 生成报告失败"
                    fi
                fi
            else
                echo "错误: $jmx_file 执行失败"
            fi
        else
            jmeter -n -t "$jmx_file" -j "$log_file"
            
            # 检查jmeter执行是否成功
            if [ $? -eq 0 ]; then
                echo "完成: $jmx_file -> 日志保存在 $log_file"
            else
                echo "错误: $jmx_file 执行失败"
            fi
        fi
    fi
done

# 如果需要生成合并报告且有JTL文件
if [ "$MERGE_REPORT" = true ] && [ ${#all_jtl_files[@]} -gt 0 ]; then
    echo "正在合并JTL文件并生成综合报告..."
    # 创建临时合并JTL文件
    merged_jtl="$OUTPUT_DIR/merged.jtl"
    
    # 将第一个文件作为基础文件复制
    cp "${all_jtl_files[0]}" "$merged_jtl"
    
    # 从第二个文件开始，提取数据行并追加到合并文件
    if [ ${#all_jtl_files[@]} -gt 1 ]; then
        for ((i=1; i<${#all_jtl_files[@]}; i++)); do
            # 跳过头行，只取数据行追加（从第2行开始）
            tail -n +2 "${all_jtl_files[$i]}" >> "$merged_jtl"
        done
    fi
    
    # 使用合并后的JTL文件生成报告
    jmeter -g "$merged_jtl" -o "$MERGE_REPORT_DIR"
    
    if [ $? -eq 0 ]; then
        echo "合并报告生成完成: $MERGE_REPORT_DIR"
    else
        echo "错误: 合并报告生成失败"
    fi
fi

echo "所有.jmx文件处理完成"