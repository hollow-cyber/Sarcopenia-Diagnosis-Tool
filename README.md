# Sarcopenia Diagnosis Tool (肌少症在线诊断工具) 📊🏥

[![Streamlit App](https://img.shields.io/badge/Streamlit-Open%20App-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://sarcopenia-diagnosis-tool-j6xn623ftp8ehtgk6f6itb.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Institution: WCH](https://img.shields.io/badge/Institution-West%20China%20Hospital-blue)](http://www.wchscu.cn/)

Sarcopenia Diagnosis Tool 是一款专注于老年医学临床与科研的肌少症在线诊断与筛查系统。本工具集成了各种主流的肌少症诊断共识，支持**个体患者的精准临床诊断**以及**人群的批量数据一键诊断与结果下载**，旨在提升临床诊断效率，规范学术论文中的定量评估标准。

> 💡 本项目受到 四川大学华西医院、国家老年疾病临床医学研究中心 的支持。程序仅供科研与学习使用。

---

## ✨ 核心特性 (Key Features)

### 1. 🔍 多重国际诊断共识多轨集成 (Multi-Consensus Integration)

系统内置并精准解析了主流的肌少症诊断共识标准：

* **AWGS 2025（亚洲最新共识）**：支持 50–64 岁中老年人与 $\ge 65$ 岁老年人的双轨切点诊断；肌量支持 DXA/BIA 与身高²/BMI 校正。
* **AWGS 2019（亚洲经典共识）**：集成传统亚洲人群切点，支持“可能肌少症”、“确诊肌少症”及“严重肌少症”的三级阶梯式诊断。
* **AWGS 2014（亚洲早期共识）**：低肌量且力量或体力表现低下即判定为肌少症，不增加严重程度分级。
* **EWGSOP2（欧洲最新共识）**：支持西方人群标准，按力量 → 肌量 → 体力表现的顺序判断“可能肌少症”“肌少症”“严重肌少症”，支持绝对肌质量（ASM）与 TUG、400 米步行等综合躯体功能指标。
* **FNIH（美国 FNIH 项目）**：基于握力与 ALM 的推荐（Recommended）与备选（Alternate）阈值组合。

### 2. 🤖 逐行容错与明确的缺测语义 (Fault-Tolerant Batch Processing)

* **单行失败不影响整批**：批量诊断时，某一行出现缺失值（`NaN`）或临床录入的非数值文本（如“异常”“无法配合”“拒绝”），系统不会中断整个批次，只把该行标记为“无法评估”，并在“评估说明”列写明具体原因（如数值越界、握力需 > 0、性别无效等）。
* **缺测不等于正常**：任何维度缺测时，由各共识的分级规则决定能否继续给出结论。
* **错误分层处理**：受试者数据问题以诊断结果与说明呈现；文件格式、表头、列映射等配置问题则明确提示需要修正的位置，避免把配置错误伪装成“资料不足”。

### 3. 👤 双轨诊断模式 (Dual Diagnosis Modes)

* **个体门诊诊疗**：提供极简的可视化表单，支持医师在门诊或床旁手动输入性别、年龄与各项测量值；结果通过定制化的彩色结果卡片（成功／警告／危险）即时反馈，并逐条显示缺测或输入错误说明。
* **科研批量处理**：一键上传 `.xlsx` 或 `.csv` 格式的临床数据库，支持 Excel 特定表单（Sheet）选择与自定义列名动态映射（同一列不可重复映射）；在原表后追加诊断结果与评估说明，并支持内存流一键下载 `.xlsx`。
* **规则与界面同源**：每个共识模块同时声明阈值/测量规则、诊断分级和输入界面；批量模式复用同一份输入定义。

---

## 💻 在线访问

👉 [点击进入：肌少症在线诊断工具](https://sarcopenia-diagnosis-tool-j6xn623ftp8ehtgk6f6itb.streamlit.app/)

---

## 🚀 安装与运行 (Installation & Usage)

### 1. 环境准备

确保计算机上已安装 **Python 3.11 或更高版本**。

### 2. 克隆仓库

```bash
git clone https://github.com/hollow-cyber/Sarcopenia-Diagnosis-Tool.git
cd Sarcopenia-Diagnosis-Tool
```

### 3. 安装依赖库

建议在虚拟环境（如 venv 或 conda）中安装依赖：

```bash
pip install -r requirements.txt
```

（依赖包含 `streamlit`、`pandas`、`openpyxl`，具体版本要求见 `requirements.txt`。）

### 4. 启动程序

在项目根目录下运行以下命令启动 Web UI：

```bash
streamlit run main.py
# 或使用
python -m streamlit run main.py
```

（运行后，浏览器会自动打开 `http://localhost:8501`。`img/`、`ref/` 使用相对路径，请在项目根目录启动。）

---

## 📖 快速使用指南 (Quick Start Guide)

1. **选择诊断共识**：在页面顶部选择用于诊断的共识（如 `AWGS 2025`）；展开“查看当前诊断共识”卡片可直接阅览内置的切点表、算法图与原文链接。
2. **切换诊断模式**：选择“👤 手动输入单人数据”或“📁 批量 Excel/CSV 上传”。
3. **单人模式配置**：展开对应的卡片（受试者基本信息、肌肉力量、肌肉质量、体力表现），填入受试者的测量数值，点击“🩺 开始诊断”即可得到诊断结论与逐条说明。
4. **批量模式配置**：
   * 上传患者表格文件；如为 Excel 表格，可在下拉菜单中选择目标表单（Sheet）。
   * 在各个信息卡片中，将对应的指标与你表格中的**表头列名**进行下拉匹配（程序会校验同一列是否被重复选择）。
   * 点击“🩺 开始诊断”，在下方预览表中查看新增的“【共识名称】诊断结果”与“【共识名称】评估说明”两列。
5. **结果导出**：点击“📥 下载诊断结果 Excel”，即可将附带诊断结论的表格保存至本地。

---

## 🗂️ 项目结构 (Project Structure)

```text
Sarcopenia-Diagnosis-Tool/
├── main.py                  # 启动入口：页头 + 共识选择 + 页面渲染
├── ui.py                    # 通用页面：基本信息、模式切换、批量文件、结果与下载
├── ui_controls.py           # 共识文件共享的输入控件（FormContext）与自动分列
├── engine.py                # 纯诊断引擎：数值校验 + 阈值比较 + 调用共识分级函数
├── models.py                # 6 个精简类型：Compare / State / Rule / Domain / Consensus / Result
├── batch.py                 # 表格读取、列映射校验、逐行批量诊断与 Excel 导出
├── consensuses/
│   ├── __init__.py          # 注册表 MODULES 与 renderer_for()
│   ├── awgs2014.py          # 每个共识一个文件：SPEC + classify + render_form
│   ├── awgs2019.py          #   AWGS 2019 是注释最完整的样板文件
│   ├── awgs2025.py
│   ├── ewgsop2.py
│   └── fnih.py
├── src/
│   └── set_st_custom_style.py   # 页头、logo 与提示条样式
├── img/                     # 共识算法图、阈值图与华西 logo
├── ref/                     # 各共识原文 PDF
├── requirements.txt         # 运行依赖
└── README.md
```

在线应用运行路径只涉及 `main.py`、`ui.py`、`ui_controls.py`、`engine.py`、`models.py`、
`batch.py`、`consensuses/` 与 `src/set_st_custom_style.py`；`img/` 与 `ref/` 只作为展示资源。

---

## 🧩 新增一个共识 (Adding a Consensus)

1. **复制模板**：复制一个现有共识文件作为模板（推荐 `consensuses/awgs2019.py`），改写模块说明、`classify`、`render_form` 与 `SPEC` 并同步相关资料到 `img` 或 `ref` 当中；阈值只写在 `Rule.cutoffs` 中，单位与比较符同时写明。
2. **注册模块**：在 `consensuses/__init__.py` 的 `MODULES` 元组中加入新模块（顺序即页面顺序）。
3**本地验证**：运行页面检查该共识的输入控件、阈值边界与分级结论。

---

## 🧪 本地验证与常见问题

* **启动检查**：修改规则或界面后，建议至少启动一次页面，逐个切换五个共识，检查输入控件、诊断结论与原文展示是否正常。
* **批量表头**：`.xlsx`/`.csv` 的首行默认作为列名；表头不能为空或重复，否则程序会提示修正。
* **评估说明列**：批量结果的“评估说明”会汇总该行的输入错误与缺测提示；没有额外说明时为空。
* **图片缺失**：若 `img/` 下的截图缺失，页面会给出提示，但不影响诊断计算。

---

## ✉️ 反馈与支持 (Support)

本程序受到四川大学华西医院、国家老年疾病临床医学研究中心的支持。
如果您在批量清洗大型数据、多中心数据映射时遇到任何 Bug，或有新的功能建议（如增加对特定人体成分仪格式的自动适配），欢迎提交 Issue。

---

© 2026 West China Hospital, Sichuan University, China.
