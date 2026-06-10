# Sarcopenia Diagnosis Tool (肌少症在线诊断工具) 📊🏥

[![Streamlit App](https://img.shields.io/badge/Streamlit-Open%20App-FF4B4B?style=flat&logo=Streamlit&logoColor=white)](https://sarcopenia-risk-analytics-j5mybxvzszqvdazhbxtjrf.streamlit.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Institution: WCH](https://img.shields.io/badge/Institution-West%20China%20Hospital-blue)](http://www.wchscu.cn/)

Sarcopenia Diagnosis Tool 是一款专注于老年医学临床与科研的肌少症在线诊断与筛查系统。本工具集成了亚洲与欧洲最新的肌少症诊断共识，支持**个体患者的精准临床诊断**以及**人群的批量数据一键诊断与结果下载**，旨在提升临床诊断效率，规范学术论文中的定量评估标准。

> 💡 本项目受到 四川大学华西医院、国家老年疾病临床医学研究中心 的支持。程序仅供科研与学习使用。

---

## ✨ 核心特性 (Key Features)

### 1. 🔍 多重国际诊断共识多轨集成 (Multi-Consensus Integration)

系统内置并精准解析了主流的肌少症诊断共识标准：

* **AWGS 2025 (亚洲最新共识)**：支持 50–64 岁中老年人与 $\ge 65$ 岁老年人的双轨切点诊断；将物理功能（如步速、五次坐立试验）独立为预后及表现指标。
* **AWGS 2019 (亚洲经典共识)**：集成传统亚洲人群切点，支持“可能肌少症”、“确诊肌少症”及“严重肌少症”的三级阶梯式诊断。
* **EWGSOP2 (欧洲最新共识)**：支持西方人群标准，将肌肉力量低下作为判定“可能肌少症”的首要触发指征，并支持绝对肌质量（ASM）与综合躯体功能指标（TUG、400m步行等）的合并诊断。

### 2. 🤖 容错型数据智能软转换 (Smart Fault-Tolerant Conversion)

* **混合文本智能解析**：在批量诊断模式下，若遇到缺失值（`NaN`）或临床录入的非数值文本（如“异常”、“无法配合”、“拒绝”等），系统会自动启用内置的智能转换逻辑将其降级，确保行内其他有效测量值（如步速正常但坐立异常）依然能参与并联算法。
* **全军覆没安全拦截**：若某患者在“肌肉力量”或“体力表现”模块中的所有级联指标均由于缺失或输入错误而失效，系统将精准判定为 `体力表现数据全部无效` 等状态，绝不抛错，保障大数据清洗的流畅度。

### 3. 👤 双轨诊断模式 (Dual Diagnosis Modes)

* **个体门诊诊疗**：提供极简的可视化表单，支持医师在门诊或床旁手动输入参数，结果通过定制化彩色高亮卡片（成功/警告/危险）即时反馈诊断结论。
* **科研批量处理**：一键上传 `.xlsx`, `.xls` 或 `.csv` 格式的大型临床数据库，支持 Excel 特定表单（Sheets）选择及自定义列名动态映射，追加诊断列后支持内存流一键无损下载。

---

## 💻 在线访问

👉 [点击进入：肌少症在线诊断工具]([https://www.google.com/search?q=https://your-sarcopenia-app-url.streamlit.app/](https://sarcopenia-diagnosis-tool-j6xn623ftp8ehtgk6f6itb.streamlit.app/))

---

## 🚀 安装与运行 (Installation & Usage)

### 1. 环境准备

确保你的计算机上已安装 Python 3.9 或更高版本。

### 2. 克隆仓库

```bash
git clone https://github.com/your-username/Sarcopenia-Diagnosis-Tool.git
cd Sarcopenia-Diagnosis-Tool

```

### 3. 安装依赖库

建议在虚拟环境（如 venv 或 conda）中安装以下依赖：

```bash
pip install -r requirements.txt

```

*(注意：请确保安装了 `streamlit`, `pandas`, `openpyxl` 等基础核心库)*

### 4. 启动程序

在项目根目录下运行以下命令启动 Web UI：

```bash
streamlit run main.py

```

*(运行后，浏览器会自动打开 `http://localhost:8501`)*

---

## 📖 快速使用指南 (Quick Start Guide)

1. **选择诊断共识**：在页面顶部选择用于诊断的共识（如 `AWGS 2025`），展开“查看当前诊断共识”卡片可直接阅览内置的切点表与诊断流程图。
2. **切换诊断模式**：选择“👤 手动输入受试者信息进行诊断”或“📁 批量 Excel/CSV 诊断与结果下载”。
3. **单人模式配置**：展开对应的卡片（基本信息、肌肉力量、肌肉质量、体力表现），填入受试者的测量数值，点击“🩺 开始诊断”即可。
4. **批量模式配置**：
* 上传患者表格文件，如为 Excel 表格，在下拉菜单中选择目标表单（Sheet）。
* 在各个信息卡片中，将对应的指标与你表格中的**表头列名**进行下拉匹配（支持防重复选择校验）。
* 点击“🩺 开始诊断”，在下方生成的预览表中检查最后一列的 `【共识名称】诊断结果`。


5. **结果导出**：点击“📥 下载完成诊断的 Excel 报表”，即可将附带诊断结论的表格保存至本地。

---


## ✉️ 反馈与支持 (Support)

本程序受到四川大学华西医院、国家老年疾病临床医学研究中心的支持。
如果您在批量清洗大型数据、多中心数据映射时遇到任何 Bug，或有新的功能建议（如增加对特定人体成分仪格式的自动适配），欢迎提交 Issue。

---

© 2026 West China Hospital, Sichuan University, China.
