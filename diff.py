input_file = "diff.txt"  # 输入文件名
output_file = "diff.txt"  # 输出文件名

# 逐行读取输入文件，过滤并写入输出文件
with open(input_file, "r") as input_f, open(output_file, "w") as output_f:
    for line in input_f:
        if line.startswith("+") or line.startswith("-"):
            output_f.write(line)
            print(1)
