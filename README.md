# ar5iv-to-notion

将 arXiv 论文导入 Notion，创建丰富的页面结构，包括完整内容和参考文献子页面。

## ✨ 特性

### 📄 论文内容提取
- 通过 **arXiv API** 获取元数据（标题、作者、摘要、分类等）
- 通过 **ar5iv** 提取完整内容（章节、图片、表格、公式、参考文献）
- 智能缓存，避免重复请求

### 🎨 丰富的 Notion 元素
| 元素 | 用途 |
|------|------|
| `heading_1/2/3` | 章节标题 |
| `paragraph` | 段落（支持富文本：粗体、斜体、链接等） |
| `callout` | 论文信息、提示框 |
| `quote` | 摘要、引用 |
| `code` | 代码块 |
| `equation` | LaTeX 数学公式 |
| `table` | 表格 |
| `bulleted_list_item` | 无序列表 |
| `numbered_list_item` | 有序列表 |
| `divider` | 分隔线 |
| `toggle` | 可折叠内容 |
| `image` | 图片 |
| `bookmark` | 链接预览 |
| `table_of_contents` | 自动目录 |

### 📚 参考文献处理
- 自动提取参考文献中的 **arXiv ID**
- 可选：通过 arXiv API **搜索**未找到 ID 的论文
- 为每个 arXiv 参考文献创建**子页面**
- 子页面包含元数据和摘要

## 🚀 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/ar5iv-to-notion.git
cd ar5iv-to-notion

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

#### 获取 Notion API Token

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 点击 "New integration"
3. 填写名称，选择工作区
4. 复制 "Internal Integration Token"

#### 获取根页面 ID

1. 在 Notion 中创建或选择一个页面
2. 点击右上角 "..." → "Copy link"
3. 从链接提取 page_id：`https://notion.so/xxx/<page_id>?v=xxx`

#### 授权 Integration

1. 打开目标页面
2. 点击右上角 "..." → "Connections"
3. 添加你创建的 Integration

#### 创建配置文件

```bash
cp .env.example .env
# 编辑 .env 填写 NOTION_TOKEN 和 NOTION_ROOT_PAGE_ID
```

### 3. 使用

```bash
# 导入单篇论文
python main.py 1706.03762

# 导入论文及其参考文献
python main.py 1706.03762 --with-refs

# 限制参考文献数量
python main.py 1706.03762 --with-refs --max-refs 10

# 搜索未知 arXiv ID 的参考文献
python main.py 1706.03762 --with-refs --search-refs

# 批量导入
python main.py 1706.03762 1810.04805 2301.08362

# 详细日志
python main.py 1706.03762 -v

# 不使用缓存
python main.py 1706.03762 --no-cache
```

## 📁 项目结构

```
ar5iv-to-notion/
├── config.py              # 配置管理
├── models.py              # 数据模型
├── utils.py               # 工具函数
├── arxiv_api.py           # arXiv API 客户端
├── ar5iv_extractor.py     # ar5iv 内容提取
├── reference_resolver.py  # 参考文献解析
├── notion_converter.py    # Notion blocks 转换
├── notion_creator.py      # Notion 页面创建
├── main.py               # 主程序入口
├── requirements.txt      # 依赖清单
├── .env.example          # 环境变量示例
└── README.md            # 本文档
```

## 🔧 模块说明

### arxiv_api.py
- 通过 arXiv API 获取论文元数据
- 支持按 ID 查询和标题搜索
- 遵守 arXiv API 速率限制（3秒间隔）

### ar5iv_extractor.py
- 从 ar5iv HTML 页面提取完整内容
- 支持章节、图片、表格、公式、参考文献

### reference_resolver.py
- 从参考文献文本提取 arXiv ID
- 可选：通过 arXiv API 搜索匹配论文

### notion_converter.py
- 将论文内容转换为 Notion blocks
- 支持 15+ 种 Notion 元素

### notion_creator.py
- 创建 Notion 页面
- 分批添加 blocks（解决 100 blocks 限制）
- 为参考文献创建子页面

## 📖 命令行参数

```
positional arguments:
  arxiv_ids            arXiv ID（如 1706.03762）

optional arguments:
  -h, --help           显示帮助信息
  -v, --verbose        显示详细日志
  --with-refs          处理参考文献（默认启用）
  --no-refs            不处理参考文献
  --search-refs        搜索未知 arXiv ID 的参考文献
  --max-refs N         最大参考文献子页面数（默认 20）
  --no-cache           不使用缓存
  --log-file PATH      日志文件路径
```

## 🔍 示例输出

导入 "Attention Is All You Need" 论文后，Notion 页面结构：

```
📄 Attention Is All You Need
├── 📋 论文信息 (callout)
├── 🔗 链接 (arXiv, PDF, ar5iv)
├── 📝 Abstract (quote)
├── 📑 Table of Contents
├── 📖 Introduction
├── 📖 Background
├── 📖 Model Architecture
│   ├── Encoder and Decoder Stacks
│   ├── Attention
│   └── ...
├── 📊 Tables
├── 🖼️ Figures
├── 📚 References
│   ├── 📎 [1706.03762] Attention paper...
│   ├── 📎 [1409.0473] Neural machine...
│   └── ...
```

## ⚠️ 注意事项

### arXiv API 限制
- 请求间隔至少 3 秒
- 批量查询建议使用较小的并发数

### Notion API 限制
- 每次请求最多 100 个 blocks
- 本工具自动分批处理

### ar5iv 可用性
- 部分旧论文可能没有 ar5iv 版本
- 此时只使用 arXiv API 元数据

## 🐛 常见问题

### Q: 论文页面内容不完整？
A: ar5iv 可能未收录该论文。程序会回退到仅使用 arXiv 元数据。

### Q: 参考文献解析不准确？
A: 参考文献格式多样，部分可能无法正确解析。启用 `--search-refs` 可提高匹配率。

### Q: API 被限制？
A: 程序会自动重试。如果频繁遇到，增加请求间隔或减少并发。

## 📝 开发

### 运行测试
```bash
pytest tests/ -v
```

### 代码格式化
```bash
black .
```

### 类型检查
```bash
mypy .
```

## 📄 License

MIT License

## 🙏 致谢

- [arXiv](https://arxiv.org/) - 论文元数据
- [ar5iv](https://ar5iv.labs.arxiv.org/) - HTML 版论文
- [Notion](https://www.notion.so/) - 页面托管