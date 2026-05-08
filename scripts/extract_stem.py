#!/usr/bin/env python

import sys
import os
import re

def main(base_file):
    if not os.path.exists(base_file):
        print(f"錯誤：找不到文件 {base_file}")
        sys.exit(1)

    # 推導 stem 文件名
    stem_file = base_file.replace('.base.', '.stem.')
    temp_base_file = base_file + '.tmp'

    stem_count = 0
    base_count = 0

    with open(base_file, 'r', encoding='utf-8') as f_in, \
         open(temp_base_file, 'w', encoding='utf-8') as f_base, \
         open(stem_file, 'w', encoding='utf-8') as f_stem:

        in_header = True

        for line in f_in:
            if in_header:
                # ==========================
                # 處理 Stem 文件的表頭
                # ==========================
                stem_line = line
                if line.startswith('name:'):
                    # 將 name 替換為包含 .stem 的名稱
                    stem_line = re.sub(r'^(name:\s*"?)([^"\s]+)("?.*)$', r'\g<1>cangjie5.stem\g<3>', line)
                f_stem.write(stem_line)

                # ==========================
                # 處理 Base 文件的表頭
                # ==========================
                # 如果遇到 '- stem'，則不寫入 base 文件
                if line.strip() == '- stem':
                    pass
                else:
                    f_base.write(line)

                if line.strip() == '...':
                    in_header = False
                continue

            # ==========================
            # 處理數據區段
            # ==========================
            # 保留空行與註釋
            if not line.strip() or line.startswith('#'):
                f_base.write(line)
                f_stem.write(line)
                continue

            # 去除換行符後按 Tab 分割
            parts = line.rstrip('\r\n').split('\t')

            # Base 文件：強制只取前 2 個字段 (text, code)
            if len(parts) >= 2:
                f_base.write(f"{parts[0]}\t{parts[1]}\n")
                base_count += 1
            else:
                f_base.write(line) # 容錯：如果有小於 2 列的異常行，原樣保留

            # Stem 文件：只有當字段 >= 3 時，才寫入完整記錄
            if len(parts) >= 3:
                f_stem.write(line)
                stem_count += 1

    # 替換原來的 base 文件
    os.replace(temp_base_file, base_file)

    print(f"修復與拆分完成！")
    print("-" * 30)
    print(f"已生成: {stem_file}")
    print(f"  -> 提取了 {stem_count} 條包含 3 個字段的記錄 (表頭 name 已修改為 cangjie5.stem)")
    print(f"已更新: {base_file}")
    print(f"  -> 共 {base_count} 條記錄被截斷為 2 個字段 (表頭已移除 '- stem')")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python extract_stem.py <文件名.base.dict.yaml>")
        sys.exit(1)

    main(sys.argv[1])
