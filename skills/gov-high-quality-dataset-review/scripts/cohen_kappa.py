"""
计算两名标注员之间的 Cohen's κ 与逐标签一致性。

输入 CSV 至少包含两列标注结果，行一一对应；任一列为空的行会被跳过。
用法：
    python cohen_kappa.py --input labels.csv --col-a annotator_a --col-b annotator_b
    python cohen_kappa.py --input labels.csv --col-a a --col-b b --threshold 0.8

仅标准库。纯本地运行，不访问网络。
退出码：0 κ ≥ 阈值；1 κ < 阈值或无法计算；2 输入错误。
"""

from __future__ import annotations

import argparse
import csv
import sys


def read_rows(path: str, encoding: str | None = None) -> list[dict]:
    encodings = [encoding] if encoding else ["utf-8-sig", "gbk", "utf-8"]
    for enc in encodings:
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别 {path} 的编码，请用 --encoding 指定")


def cohen_kappa(a: list[str], b: list[str]) -> dict:
    n = len(a)
    if n == 0:
        raise ValueError("没有有效的成对标注")

    po = sum(1 for x, y in zip(a, b) if x == y) / n
    labels = sorted(set(a) | set(b))
    pe = sum((a.count(label) / n) * (b.count(label) / n) for label in labels)

    if pe >= 1.0:
        return {"n": n, "po": po, "pe": pe, "kappa": None,
                "note": "所有标注均为同一类别，κ 无法计算"}

    return {"n": n, "po": po, "pe": pe, "kappa": (po - pe) / (1 - pe), "note": ""}


def label_table(a: list[str], b: list[str]) -> list[dict]:
    labels = sorted(set(a) | set(b))
    rows = []
    for label in labels:
        a_count = a.count(label)
        b_count = b.count(label)
        both = sum(1 for x, y in zip(a, b) if x == label and y == label)
        union = sum(1 for x, y in zip(a, b) if x == label or y == label)
        rows.append({
            "标签": label,
            "A 标注数": a_count,
            "B 标注数": b_count,
            "双方一致数": both,
            "Jaccard": round(both / union, 3) if union else 0.0,
        })
    return rows


def confusion_markdown(a: list[str], b: list[str]) -> str:
    labels = sorted(set(a) | set(b))
    header = "| A \\ B | " + " | ".join(labels) + " |"
    sep = "|---|" + "|".join(["---:"] * len(labels)) + "|"
    lines = [header, sep]
    for la in labels:
        counts = [sum(1 for x, y in zip(a, b) if x == la and y == lb) for lb in labels]
        lines.append(f"| {la} | " + " | ".join(str(c) for c in counts) + " |")
    return "\n".join(lines)


def interpretation(kappa: float | None) -> str:
    if kappa is None:
        return "无法计算"
    value = round(kappa, 4)
    if value < 0:
        return "差于随机"
    if value <= 0.20:
        return "轻微一致"
    if value <= 0.40:
        return "一般一致"
    if value <= 0.60:
        return "中等一致"
    if value <= 0.80:
        return "较强一致"
    return "几乎完全一致"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cohen's κ 标注一致性")
    parser.add_argument("--input", required=True, help="标注 CSV")
    parser.add_argument("--col-a", required=True, help="标注员 A 的列名")
    parser.add_argument("--col-b", required=True, help="标注员 B 的列名")
    parser.add_argument("--threshold", type=float, default=0.8, help="合格阈值，默认 0.8")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    try:
        rows = read_rows(args.input, args.encoding)
    except Exception as exc:
        print(f"读取失败：{exc}", file=sys.stderr)
        sys.exit(2)

    if not rows:
        print("错误：CSV 为空", file=sys.stderr)
        sys.exit(2)
    if args.col_a not in rows[0] or args.col_b not in rows[0]:
        print(f"错误：列 {args.col_a} 或 {args.col_b} 不存在", file=sys.stderr)
        sys.exit(2)

    a, b = [], []
    for row in rows:
        va = str(row.get(args.col_a) or "").strip()
        vb = str(row.get(args.col_b) or "").strip()
        if va and vb:
            a.append(va)
            b.append(vb)

    try:
        result = cohen_kappa(a, b)
    except ValueError as exc:
        print(f"计算失败：{exc}", file=sys.stderr)
        sys.exit(2)

    print("=" * 56)
    print("标注一致性结果")
    print("=" * 56)
    print(f"  有效样本数: {result['n']}")
    print(f"  观察一致率 Po: {result['po']:.4f}")
    print(f"  期望一致率 Pe: {result['pe']:.4f}")
    if result["kappa"] is None:
        print(f"  Cohen's κ: 无法计算（{result['note']}）")
    else:
        print(f"  Cohen's κ: {result['kappa']:.4f}（{interpretation(result['kappa'])}）")
        print(f"  阈值: {args.threshold:.2f} → {'达标' if result['kappa'] >= args.threshold else '未达标'}")
    print()
    print("逐标签统计：")
    for row in label_table(a, b):
        print(f"  {row['标签']}: A={row['A 标注数']} B={row['B 标注数']} "
              f"一致={row['双方一致数']} Jaccard={row['Jaccard']}")
    print()
    print("混淆矩阵（行=A，列=B）：")
    print(confusion_markdown(a, b))
    print("=" * 56)

    if result["kappa"] is None or result["kappa"] < args.threshold:
        sys.exit(1)


def demo() -> None:
    a = ["正例", "正例", "负例", "负例", "正例", "负例", "正例", "负例", "正例", "负例"]
    b = ["正例", "负例", "负例", "负例", "正例", "正例", "正例", "负例", "正例", "负例"]
    result = cohen_kappa(a, b)
    print(f"κ = {result['kappa']:.4f}（{interpretation(result['kappa'])}），Po={result['po']:.2f}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
