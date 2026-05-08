#!/usr/bin/env python

import sys
import os
import re

def is_extended_cjk(text):
    """
    判斷字串中是否包含 CJK 擴展區漢字或兼容漢字。
    """
    for ch in text:
        cp = ord(ch)
        if ((0x3400 <= cp <= 0x4DBF) or     # Ext A
            (0x20000 <= cp <= 0x2A6DF) or   # Ext B
            (0x2A700 <= cp <= 0x2B73F) or   # Ext C
            (0x2B740 <= cp <= 0x2B81F) or   # Ext D
            (0x2B820 <= cp <= 0x2CEAF) or   # Ext E
            (0x2CEB0 <= cp <= 0x2EBEF) or   # Ext F
            (0x30000 <= cp <= 0x3134F) or   # Ext G
            (0x31350 <= cp <= 0x323AF) or   # Ext H
            (0x2EBF0 <= cp <= 0x2EE5F) or   # Ext I
            (0x323B0 <= cp <= 0x3347F) or   # Ext J
            (0xF900 <= cp <= 0xFAFF) or     # Compatibility Ideographs
            (0x2F800 <= cp <= 0x2FA1F)):    # Compatibility Ideographs Supplement
            return True
    return False

def process_header(header_lines, suffix):
    """
    過濾 YAML 表頭，只保留特定的欄位，並自動修改 name。
    """
    out_lines = []
    in_yaml = False
    keep_current_key = False
    allowed_keys = {'name', 'version', 'columns'}

    for line in header_lines:
        # 標記進入與離開 YAML 區塊
        if line.strip() == '---':
            in_yaml = True
            out_lines.append(line)
            continue
        elif line.strip() == '...':
            in_yaml = False
            out_lines.append(line)
            continue

        if not in_yaml:
            # YAML 區塊外部的內容（如 # 註解）全部保留
            out_lines.append(line)
        else:
            # 在 YAML 區塊內部，尋找頂層 Key (不以空格開頭，且包含冒號)
            match = re.match(r'^([A-Za-z0-9_-]+):', line)
            if match:
                key = match.group(1)
                # 判斷這個 key 是否在我們的白名單中
                keep_current_key = (key in allowed_keys)

                # 如果是 name 欄位，自動加上後綴 (如 .extended)
                if keep_current_key and key == 'name':
                    line = re.sub(r'^(name:\s*"?)([^"\s]+)("?.*)$', rf'\g<1>\g<2>.{suffix}\g<3>', line)

            # 如果目前處於需要保留的 key 之下（包含其下的列表項如 - text），則寫入
            if keep_current_key:
                out_lines.append(line)

    return out_lines

def main(input_file):
    # 處理檔名
    if input_file.endswith('.dict.yaml'):
        prefix = input_file[:-10]
    else:
        prefix, _ = os.path.splitext(input_file)

    out_ext_file = f"{prefix}.extended.dict.yaml"
    out_base_file = f"{prefix}.base.dict.yaml"

    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            # 1. 先讀取整個表頭區塊 (直到遇見 '...')
            header_lines = []
            for line in f_in:
                header_lines.append(line)
                if line.strip() == '...':
                    break

            # 2. 生成兩份客製化的新表頭
            ext_header = process_header(header_lines, 'extended')
            base_header = process_header(header_lines, 'base')

            # 3. 創建輸出文件，寫入新表頭，並開始分流數據
            with open(out_ext_file, 'w', encoding='utf-8') as f_ext, \
                 open(out_base_file, 'w', encoding='utf-8') as f_base:

                f_ext.writelines(ext_header)
                f_base.writelines(base_header)

                ext_count = 0
                base_count = 0

                for line in f_in:
                    # 處理空行與數據區內的註釋
                    if not line.strip() or line.startswith('#'):
                        f_ext.write(line)
                        f_base.write(line)
                        continue

                    parts = line.split('\t')
                    if len(parts) > 0:
                        col1 = parts[0]
                        if is_extended_cjk(col1):
                            f_ext.write(line)
                            ext_count += 1
                        else:
                            f_base.write(line)
                            base_count += 1

        print(f"處理完成！已自動精簡 YAML 表頭並重新命名。")
        print(f"源文件: {input_file}")
        print(f"擴展區 ({ext_count} 條) -> {out_ext_file}")
        print(f"基本區 ({base_count} 條) -> {out_base_file}")

    except FileNotFoundError:
        print(f"錯誤: 找不到文件 {input_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python split_dict_with_header.py <文件名.dict.yaml>")
        sys.exit(1)

    main(sys.argv[1])
