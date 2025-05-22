import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
from tqdm import tqdm
import concurrent.futures

def get_file_urls(base_url, file_extensions, use_mirror=False):
    """
    获取指定后缀的文件URL列表，如果file_extensions包含'all'，则获取所有文件
    """
    try:
        # 如果使用镜像，替换URL
        if use_mirror:
            base_url = base_url.replace('huggingface.co', 'hf-mirror.com')
        
        response = requests.get(base_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"请求网页出错: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    file_list = []
    
    # 匹配所有的文件链接
    file_elements = soup.find_all('a', title="Download file")
    
    for element in file_elements:
        href = element.get('href')
        # 从href中提取文件名
        file_name = os.path.basename(href)
        if '?download=true' in file_name:
            file_name = file_name.replace('?download=true', '')
        
        # 检查是否是指定后缀的文件，或者是否下载所有文件
        if 'all' in file_extensions or any(file_name.endswith(ext) for ext in file_extensions):
            # 获取文件大小信息
            size_element = element.find_next('span')
            file_size = size_element.text.strip() if size_element else "未知大小"
            
            file_url = urljoin(base_url, href)
            # 根据Hugging Face的结构，构建正确的下载URL
            if 'huggingface.co' in base_url or 'hf-mirror.com' in base_url:
                # 替换为正确的下载URL格式
                if '/blob/' in file_url:
                    file_url = file_url.replace('/blob/', '/resolve/')
                elif '/tree/main/' in file_url:
                    file_url = file_url.replace('/tree/main/', '/resolve/main/')
            
            file_list.append({
                "name": file_name,
                "url": file_url,
                "size": file_size
            })
    
    return file_list

def download_file(url, save_path, chunk_size=8192, use_mirror=False):
    """
    下载文件到指定路径
    """
    try:
        # 检查文件是否已存在
        if os.path.exists(save_path):
            print(f"文件已存在，跳过下载: {save_path}")
            return True
            
        # 如果使用镜像，替换URL
        if use_mirror:
            url = url.replace('huggingface.co', 'hf-mirror.com')
            
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=os.path.basename(save_path)) as pbar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return True
    except requests.exceptions.RequestException as e:
        print(f"下载文件失败: {url}, 错误: {e}")
        return False
    except Exception as e:
        print(f"保存文件时出错: {save_path}, 错误: {e}")
        return False

def get_repo_name(url):
    """
    从URL中提取仓库名称
    """
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) >= 2:
        return f"{path_parts[0]}_{path_parts[1]}"
    return "unknown_repo"

def main():
    parser = argparse.ArgumentParser(description='从Hugging Face下载指定后缀的模型文件')
    parser.add_argument('--url', help='Hugging Face模型仓库URL')
    parser.add_argument('--json', help='使用已有的JSON文件进行下载')
    parser.add_argument('--ext', nargs='+', default=['.safetensors'], help='要下载的文件后缀列表，例如：.safetensors .onnx .hash，使用all下载所有文件')
    parser.add_argument('--output', default='./models', help='下载文件保存的目录路径')
    parser.add_argument('--threads', type=int, default=3, help='并行下载的线程数')
    parser.add_argument('--mirror', action='store_true', help='使用hf-mirror.com镜像')
    args = parser.parse_args()
    
    # 检查参数
    if not args.url and not args.json:
        parser.error("必须提供 --url 或 --json 参数之一")
    
    if args.url and args.json:
        parser.error("不能同时提供 --url 和 --json 参数")
    
    file_list = []
    json_path = None
    
    if args.json:
        # 从JSON文件读取文件列表
        try:
            with open(args.json, 'r', encoding='utf-8') as f:
                file_list = json.load(f)
            json_path = args.json
            print(f"从 {args.json} 读取文件列表")
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            return
    else:
        # 从URL获取文件列表
        print(f"正在从 {args.url} 获取文件列表...")
        file_list = get_file_urls(args.url, args.ext, args.mirror)
        
        if not file_list:
            print("未找到匹配的文件")
            return
        
        # 获取仓库名称
        repo_name = get_repo_name(args.url)
        
        # 保存文件列表到JSON
        json_path = os.path.join(args.output, f'{repo_name}.json')
        os.makedirs(args.output, exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(file_list, f, ensure_ascii=False, indent=2)
        
        print(f"找到 {len(file_list)} 个匹配文件，信息已保存至 {json_path}")
    
    # 检查已存在的文件
    existing_files = []
    new_files = []
    for file_info in file_list:
        save_path = os.path.join(args.output, file_info['name'])
        if os.path.exists(save_path):
            existing_files.append(file_info['name'])
        else:
            new_files.append(file_info)
    
    if existing_files:
        print(f"\n以下文件已存在，将跳过下载：")
        for file_name in existing_files:
            print(f"- {file_name}")
    
    if not new_files:
        print("\n所有文件都已存在，无需下载")
        return
    
    # 确认是否下载
    confirm = input(f"\n是否下载 {len(new_files)} 个新文件到 {args.output} 目录? (y/n): ").lower()
    if confirm != 'y':
        print("已取消下载")
        return
    
    # 并行下载文件
    print(f"开始下载文件，使用 {args.threads} 个线程...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for file_info in new_files:
            save_path = os.path.join(args.output, file_info['name'])
            futures.append(
                executor.submit(download_file, file_info['url'], save_path, use_mirror=args.mirror)
            )
        
        # 等待所有下载完成
        success_count = 0
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
        
        print(f"下载完成，成功: {success_count}/{len(new_files)}")

if __name__ == "__main__":
    main() 