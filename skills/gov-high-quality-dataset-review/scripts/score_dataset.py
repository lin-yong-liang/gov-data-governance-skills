"""
高质量数据集评分汇总。

读取 scorecard CSV（模板见 assets/scorecard_template.csv），计算维度得分、
总分、否决项，并给出认定结论。

用法：
    python score_dataset.py --input scorecard.csv

仅标准库。纯本地运行，不访问网络。
退出码：0 通过；1 有条件通过；2 不通过；3 输入错误。
"""

from __future__ import annotations

import argparse
import csv
import sys

DIMENSIONS = ["说明文档", "数据质量", "模型应用"]
TRUE_VALUES = {"是", "y", "yes", "true", "1"}


def read_rows(path: str, encoding: str | None = None) -> list[dict]:
    encodings = [encoding] if encoding else ["utf-8-sig", "gbk", "utf-8"]
    for enc in encodings:
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别 {path} 的编码，请用 --encoding 指定")


def normalize_dimension(value: str) -> str:
    text = str(value).strip()
    if "说明文档" in text or text.upper().startswith("A"):
        return "说明文档"
    if "数据质量" in text or text.upper().startswith("B"):
        return "数据质量"
    if "模型应用" in text or text.upper().startswith("C"):
        return "模型应用"
    return text or "未分类"


def parse_number(value, *, percent: bool = False):
    text = str(value or "").strip().replace("%", "").replace("％", "")
    if text == "" or text.upper() in {"N/A", "NA", "-", "—"}:
        return None
    if percent:
        return float(text)
    return float(text)


def evaluate(rows: list[dict]) -> dict:
    dims = {name: {"weight": 0.0, "weighted": 0.0, "items": 0, "na": []} for name in DIMENSIONS}
    veto_items = []
    warnings = []

    for row in rows:
        dim = normalize_dimension(row.get("维度", ""))
        if dim not in dims:
            warnings.append(f"未知维度 {dim}，已跳过")
            continue

        code = str(row.get("指标编号", "")).strip()
        weight = parse_number(row.get("权重(%)"))
        score = parse_number(row.get("指标得分(0-100)"))
        veto = str(row.get("否决项(是/否)", "")).strip().lower() in TRUE_VALUES

        if veto:
            veto_items.append(code or str(row.get("指标名称", "")).strip())

        if weight is None:
            warnings.append(f"{code} 缺少权重，已跳过")
            continue
        if score is None:
            dims[dim]["na"].append(code)
            continue

        dims[dim]["weight"] += weight
        dims[dim]["weighted"] += weight * score
        dims[dim]["items"] += 1

    scores = {}
    for name, data in dims.items():
        scores[name] = round(data["weighted"] / data["weight"], 2) if data["weight"] > 0 else None

    available = [value for value in scores.values() if value is not None]
    overall = round(sum(available) / len(available), 2) if available else None

    if veto_items:
        conclusion = "不通过"
        reason = "存在否决项"
    elif not available:
        conclusion = "不通过"
        reason = "没有可用的指标得分"
    elif any(value < 80 for value in available):
        conclusion = "不通过"
        reason = "存在维度得分低于 80"
    elif any(80 <= value < 90 for value in available):
        conclusion = "有条件通过"
        reason = "存在维度得分在 80–89 之间"
    elif all(value >= 90 for value in available):
        conclusion = "高质量数据集（通过）"
        reason = "所有评测维度均 ≥90 且无否决项"
    else:
        conclusion = "不通过"
        reason = "未满足判定条件"

    # 维度权重合计警告
    for name, data in dims.items():
        if data["items"] and abs(data["weight"] - 100) > 0.01:
            warnings.append(f"{name} 权重合计 {data['weight']:g}%，不是 100%，已按实际权重归一化")

    return {
        "dims": dims,
        "scores": scores,
        "overall": overall,
        "veto_items": veto_items,
        "warnings": warnings,
        "conclusion": conclusion,
        "reason": reason,
    }


def render(result: dict) -> str:
    lines = [
        "=" * 60,
        "高质量数据集评分汇总",
        "=" * 60,
        "维度得分：",
    ]
    for name in DIMENSIONS:
        data = result["dims"].get(name)
        score = result["scores"].get(name)
        if not data or data["items"] == 0:
            lines.append(f"  {name}: N/A（豁免或未评分）")
            continue
        na = f"，N/A {len(data['na'])} 项" if data["na"] else ""
        flag = "达标" if score >= 90 else ("有条件" if score >= 80 else "不达标")
        lines.append(f"  {name}: {score:6.2f} / 100  [{flag}]（{data['items']} 项{na}）")

    if result["overall"] is not None:
        lines.append(f"\n总分（展示用）: {result['overall']:.2f} / 100")

    if result["veto_items"]:
        lines.append(f"\n否决项: {', '.join(result['veto_items'])}")
    else:
        lines.append("\n否决项: 无")

    if result["warnings"]:
        lines.append("\n提示：")
        for warning in result["warnings"]:
            lines.append(f"  - {warning}")

    lines += [
        "",
        f"结论: {result['conclusion']}",
        f"理由: {result['reason']}",
    ]
    if result["conclusion"] == "有条件通过":
        lines.append("处理: 限期整改后复测，复测通过方可认定。")
    elif result["conclusion"] == "不通过":
        lines.append("处理: 整改后重新评测；存在否决项的，整改完成前不得进入认定流程。")
    lines.append("=" * 60)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="高质量数据集评分汇总")
    parser.add_argument("--input", required=True, help="评分表 CSV")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    try:
        rows = read_rows(args.input, args.encoding)
    except Exception as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        sys.exit(3)

    if not rows:
        print("错误：评分表为空", file=sys.stderr)
        sys.exit(3)

    required = {"维度", "指标编号", "权重(%)", "指标得分(0-100)"}
    if not required.issubset(rows[0].keys()):
        print(f"错误：缺少必要列，需要 {', '.join(sorted(required))}", file=sys.stderr)
        sys.exit(3)

    try:
        result = evaluate(rows)
    except ValueError as exc:
        print(f"数据错误：{exc}", file=sys.stderr)
        sys.exit(3)

    print(render(result))

    if result["conclusion"] == "高质量数据集（通过）":
        sys.exit(0)
    if result["conclusion"] == "有条件通过":
        sys.exit(1)
    sys.exit(2)


def demo() -> None:
    rows = []
    weights = {
        "说明文档": [("A1", 20, 95), ("A2", 25, 92), ("A3", 20, 100), ("A4", 20, 90), ("A5", 15, 100)],
        "数据质量": [("B1", 15, 98), ("B2", 20, 96), ("B3", 15, 94), ("B4", 15, 92),
                    ("B5", 10, 100), ("B6", 10, 95), ("B7", 5, 100), ("B8", 10, 100)],
        "模型应用": [("C1", 25, 92), ("C2", 30, 93), ("C3", 25, 90), ("C4", 20, 88)],
    }
    for dim, items in weights.items():
        for code, weight, score in items:
            rows.append({"维度": dim, "指标编号": code, "权重(%)": weight,
                         "指标得分(0-100)": score, "否决项(是/否)": "否"})
    print(render(evaluate(rows)))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
