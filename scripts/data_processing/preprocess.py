"""
JD 数据预处理脚本
读取 data/raw/ 下所有 .txt 文件，
按 --- 拆分为独立 JD，
逐字段提取：岗位名称 / 公司 / 类型 / 硬性要求 / 软性素质 / 加分项 / 原始描述，
输出 JSONL（供 Dify 导入）和 Markdown（供人工查验）。
"""

import re
import json
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
KB_DIR = BASE_DIR / "data" / "knowledge_base"

# ── 所有已知段落标题（用于确定每个段落结束位置）───────────
ALL_HEADERS = [
    "硬性要求：",
    "软性素质：",
    "加分项：",
    "原始描述：",
    "岗位亮点：",
    "工作地点：",
]


# ══════════════════════════════════════════════════════════════
# 解析工具函数
# ══════════════════════════════════════════════════════════════

def extract_between(text: str, start_marker: str, stop_markers: list[str]) -> str:
    """
    从 text 中提取 start_marker 之后、第一个 stop_marker 之前的内容。
    找不到 start_marker 返回空字符串。
    """
    start_pos = text.find(start_marker)
    if start_pos == -1:
        return ""

    content_start = start_pos + len(start_marker)

    # 找到 content_start 之后最早出现的 stop_marker
    end_pos = len(text)
    for marker in stop_markers:
        pos = text.find(marker, content_start)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    return text[content_start:end_pos].strip()


def parse_list_items(text: str) -> list[str]:
    """
    从文本中提取以 -  或 - 开头的列表项。
    支持 "- 文本" 和 "-文本" 两种格式。
    """
    if not text:
        return []

    items: list[str] = []
    for line in text.strip().split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            items.append(stripped[2:].strip())
        elif stripped.startswith("-") and len(stripped) > 1:
            items.append(stripped[1:].strip())
    return items


def parse_single_line(text: str, marker: str) -> str:
    """
    提取单行字段值（如 岗位名称：xxx）。
    匹配 marker 后同一行剩余文本。
    """
    # 找到 marker 位置，取同一行冒号后的内容
    for line in text.split("\n"):
        if marker in line:
            # 找到 marker 在行内的位置
            idx = line.find(marker)
            value = line[idx + len(marker):].strip()
            return value
    return ""


# ══════════════════════════════════════════════════════════════
# JD 块解析
# ══════════════════════════════════════════════════════════════

def parse_jd_block(block: str) -> dict | None:
    """
    解析单个 JD 文本块，返回结构化字典。
    字段全部缺失时返回 None。
    """
    block = block.strip()
    if not block:
        return None

    # ── 标题行（【公司】职位名） ──
    title = ""
    first_line = block.split("\n")[0].strip()
    if first_line.startswith("【"):
        title = first_line

    # ── 单行字段 ──
    job_title = parse_single_line(block, "岗位名称：")
    company = parse_single_line(block, "公司：")
    job_type = parse_single_line(block, "类型：")

    # ── 硬性要求（列表） ──
    hard_text = extract_between(block, "硬性要求：", ALL_HEADERS)
    hard_reqs = parse_list_items(hard_text)

    # ── 软性素质（列表） ──
    soft_text = extract_between(block, "软性素质：", ALL_HEADERS)
    soft_quals = parse_list_items(soft_text)

    # ── 加分项（列表） ──
    bonus_text = extract_between(block, "加分项：", ALL_HEADERS)
    bonuses = parse_list_items(bonus_text)

    # ── 原始描述（纯文本，到块末尾） ──
    original = extract_between(block, "原始描述：", [])

    # ── 可选字段 ──
    location = parse_single_line(block, "工作地点：")
    highlights = extract_between(block, "岗位亮点：", ALL_HEADERS)

    # ── 如果所有核心字段都为空，跳过 ──
    if not title and not job_title and not company and not original:
        return None

    return {
        "title": title,
        "岗位名称": job_title,
        "公司": company,
        "类型": job_type,
        "硬性要求": hard_reqs,
        "软性素质": soft_quals,
        "加分项": bonuses,
        "原始描述": original,
        "工作地点": location,
        "岗位亮点": highlights,
        "source_file": "",  # 由调用方填入
    }


# ══════════════════════════════════════════════════════════════
# 主处理流程
# ══════════════════════════════════════════════════════════════

def process_all_files() -> list[dict]:
    """读取所有 .txt 文件，按 --- 拆分并逐条解析 JD。"""
    all_jds: list[dict] = []

    txt_files = sorted(RAW_DIR.glob("*.txt"))
    if not txt_files:
        print("[WARN] data/raw/ 中没有 .txt 文件")
        return all_jds

    for txt_file in txt_files:
        print(f"\n{'─' * 50}")
        print(f"[FILE] {txt_file.name}")
        content = txt_file.read_text(encoding="utf-8")

        # 按 --- 拆分为独立 JD 块
        blocks = re.split(r"\n---\n", content)

        for i, block in enumerate(blocks, 1):
            jd = parse_jd_block(block)
            if jd is None:
                continue
            jd["source_file"] = txt_file.name
            all_jds.append(jd)
            print(f"  [{len(all_jds):02d}] {jd['岗位名称']}  |  {jd['公司']}  |  {jd['类型']}")

    return all_jds


# ══════════════════════════════════════════════════════════════
# 输出
# ══════════════════════════════════════════════════════════════

def save_jsonl(jds: list[dict]) -> Path:
    """保存为 JSONL，每个 JD 一行。"""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    path = KB_DIR / "jds.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for jd in jds:
            f.write(json.dumps(jd, ensure_ascii=False) + "\n")
    print(f"\n[OK] JSONL → {path}  ({len(jds)} 条)")
    return path


def save_markdown(jds: list[dict]) -> Path:
    """保存为 Markdown，方便人工逐条查验。"""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    path = KB_DIR / "jds.md"
    lines: list[str] = []

    lines.append("# AI 求职助手 · 知识库（JD 全集）\n")
    lines.append(f"共 **{len(jds)}** 条 JD\n")

    for i, jd in enumerate(jds, 1):
        lines.append(f"---\n")
        lines.append(f"## {i}. {jd['title'] or jd['岗位名称'] or '(无标题)'}\n")

        # 基本信息
        lines.append("| 字段 | 内容 |")
        lines.append("|------|------|")
        for key in ["岗位名称", "公司", "类型", "工作地点"]:
            val = jd.get(key, "")
            lines.append(f"| {key} | {val or '—'} |")
        lines.append(f"| 来源文件 | {jd.get('source_file', '')} |")
        lines.append("")

        # 硬性要求
        lines.append("### 硬性要求\n")
        if jd["硬性要求"]:
            for item in jd["硬性要求"]:
                lines.append(f"- {item}")
        else:
            lines.append("*(无)*")
        lines.append("")

        # 软性素质
        lines.append("### 软性素质\n")
        if jd["软性素质"]:
            for item in jd["软性素质"]:
                lines.append(f"- {item}")
        else:
            lines.append("*(无)*")
        lines.append("")

        # 加分项
        lines.append("### 加分项\n")
        if jd["加分项"]:
            for item in jd["加分项"]:
                lines.append(f"- {item}")
        else:
            lines.append("*(无)*")
        lines.append("")

        # 岗位亮点
        if jd.get("岗位亮点"):
            lines.append("### 岗位亮点\n")
            lines.append(jd["岗位亮点"])
            lines.append("")

        # 原始描述
        lines.append("### 原始描述\n")
        if jd["原始描述"]:
            lines.append(jd["原始描述"])
        else:
            lines.append("*(无)*")
        lines.append("")

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Markdown → {path}  ({len(jds)} 条)")
    return path


# ══════════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("  求职助手 · JD 数据预处理")
    print("=" * 50)

    jds = process_all_files()

    if not jds:
        print("\n[WARN] 未解析到任何 JD，请检查 data/raw/ 目录。")
        exit(1)

    save_jsonl(jds)
    save_markdown(jds)

    # ── 统计摘要 ──
    print(f"\n{'=' * 50}")
    print(f"  处理完成：{len(jds)} 条 JD")
    companies = set(jd["公司"] for jd in jds if jd["公司"])
    print(f"  涉及公司：{len(companies)} 家")
    types = set(jd["类型"] for jd in jds if jd["类型"])
    print(f"  职位类型：{', '.join(sorted(types))}")
    print(f"{'=' * 50}")
