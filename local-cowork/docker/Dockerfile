# LocalCowork 沙盒环境
FROM python:3.11-slim

# 安装系统工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    vim \
    tree \
    jq \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
RUN pip install --no-cache-dir \
    python-docx \
    openpyxl \
    python-pptx \
    pypdf \
    reportlab \
    pandas \
    numpy \
    matplotlib \
    requests \
    beautifulsoup4

# 创建工作目录
WORKDIR /workspace

# 设置非 root 用户（安全）
RUN useradd -m -s /bin/bash cowork
USER cowork

CMD ["tail", "-f", "/dev/null"]
