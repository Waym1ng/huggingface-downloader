# 模型下载工具

这是一个用于从Hugging Face下载模型文件的工具，支持通过URL或JSON文件两种方式下载模型文件。

## 功能特点

- 支持两种下载模式：
  - 通过URL获取文件列表并下载
  - 使用已有的JSON文件进行下载
- 支持指定文件后缀筛选下载（URL模式）
- 自动生成文件列表并保存为JSON（URL模式）
- 多线程并行下载，提高下载速度
- 显示下载进度条
- 自动创建保存目录
- 支持使用hf-mirror.com镜像加速下载
- 自动跳过已存在的文件，避免重复下载
- 显示文件大小信息

## 安装

1. 确保已安装Python 3.6+
2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 从URL下载

```bash
python model_downloader.py --url https://huggingface.co/facefusion/models-3.0.0/tree/main
```

这将：
1. 从指定URL获取文件列表
2. 筛选出指定后缀的文件（默认为`.safetensors`）
3. 生成JSON文件保存文件列表
4. 下载文件到指定目录（默认为`./models`）

### 从JSON文件下载

```bash
python model_downloader.py --json ./models/facefusion_models-3.0.0.json
```

这将：
1. 读取JSON文件中的文件列表
2. 跳过已存在的文件
3. 下载新文件到指定目录

### 参数说明

- `--url`：Hugging Face模型仓库URL（与`--json`参数二选一）
- `--json`：使用已有的JSON文件进行下载（与`--url`参数二选一）
- `--ext`：要下载的文件后缀列表，默认为`.safetensors`（仅在使用`--url`时有效）
- `--output`：下载文件保存的目录路径，默认为`./models`
- `--threads`：并行下载的线程数，默认为3
- `--mirror`：使用hf-mirror.com镜像加速下载

### 示例

1. 从URL下载所有`.safetensors`和`.hash`文件到指定目录，使用镜像：

```bash
python model_downloader.py --url https://huggingface.co/facefusion/models-3.2.0/tree/main --ext .safetensors .hash --output ./downloaded_models --threads 5 --mirror
```

2. 使用已有的JSON文件下载：

```bash
python model_downloader.py --json ./models/facefusion_models-3.2.0.json --output ./downloaded_models --threads 5 --mirror
```

## 注意事项

- 下载大文件时请确保有足够的存储空间
- 可能需要稳定的网络连接才能成功下载大型模型文件
- 部分仓库可能需要登录才能访问
- 使用镜像时，如果遇到下载问题，可以尝试不使用镜像
- 使用`--json`参数时，`--ext`参数将被忽略
- 程序会自动跳过已存在的文件，避免重复下载
- JSON文件包含完整的文件信息，包括文件名、URL和大小 