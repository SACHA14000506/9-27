import os

# 定义要替换的内容
old_content = {
    'suffix_num': '"0"', 
    'suffix_repo': '"vue"',  
    'suffix_branch': '"main"',  
    'suffix_file': '"vue_data"' 
}

# 定义新内容
new_content = {
    
    'suffix_num': '"1"', 
    'suffix_repo': '"z3"',  
    'suffix_branch': '"master"',  
    'suffix_file': '"z3_data"'  
}

# 要处理的文件列表
file_paths = ["001.py", "002.py", "003.py", "004.py", "005.py", "006.py","all_id.py","choose_id0.py","choose_id1.py","merge.py"]  # 替换为你的文件名

def replace_content_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:  # 读取时指定 utf-8 编码
            content = file.read()
        
        # 替换指定的内容
        for key, old_value in old_content.items():
            new_value = new_content[key]
            content = content.replace(f'{key} = {old_value}', f'{key} = {new_value}')
        
        # 将修改后的内容写回文件，写入时也指定 utf-8 编码
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Successfully updated {file_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

# 对所有文件进行处理
for file_path in file_paths:
    replace_content_in_file(file_path)