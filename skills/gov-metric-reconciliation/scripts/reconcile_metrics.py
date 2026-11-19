"""
政务指标对账助手：比较两个来源的同一指标，计算差异并给出处理建议。

用法：
    python reconcile_metrics.py --values 125000 118120 --tolerance 0.001
    python reconcile_metrics.py --source-a a.csv --source-b b.csv --metric case_count \
        --date-col stat_date --date 2026-10-31

依赖：仅标准库。纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import csv
import io
import sys


def compare_values(value_a: float, value_b: float, tolerance: float = 0.001) -> dict:
    absolute_diff = value_a - value_b
    if value_a != 0:
        pct_diff = absolute_diff / value_a
        within = abs(pct_diff) <= tolerance
        pct_display = f"{pct_diff:+.4%}"
    else:
        pct_diff = None
        within = abs(absolute_diff) < 1e-12
        pct_display = "无法计算（来源 A 为 0）"

    return {
        "value_a": value_a,
        "value_b": value_b,
        "absolute_diff": absolute_diff,
        "pct_diff": pct_diff,
        "pct_display": pct_display,
        "tolerance": tolerance,
        "within_tolerance": within,
        "status": "ACCEPTED" if within else "INVESTIGATE",
    }


def _read_text(path: str, encoding: str | None = None) -> str:
    encodings = [encoding] if encoding else ["utf-8-sig", "gbk", "utf-8"]
    for enc in encodings:
        try:
            with open(path, encoding=enc, newline="") as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法识别 {path} 的编码，请用 --encoding 指定")


def load_metric_from_csv(
    filepath: str,
    metric_col: str,
    date_col: str | None = None,
    date: str | None = None,
    encoding: str | None = None,
) -> float:
    reader = csv.DictReader(io.StringIO(_read_text(filepath, encoding)))
    total = 0.0
    matched = 0
    for row in reader:
        if date_col and date and row.get(date_col) != date:
            continue
        raw = row.get(metric_col)
        if raw is None or str(raw).strip() == "":
            continue
        total += float(raw)
        matched += 1

    if matched == 0:
        suffix = f"（日期 {date}）" if date else ""
        raise ValueError(f"{filepath} 中没有匹配记录{suffix}")
    return total


def build_report(result: dict, label_a: str, label_b: str) -> str:
    lines = [
        "=" * 64,
        "政务指标口径对账结果",
        "=" * 64,
        f"  {label_a}: {result['value_a']:,.2f}",
        f"  {label_b}: {result['value_b']:,.2f}",
        f"  绝对差(A-B): {result['absolute_diff']:+,.2f}",
        f"  百分比差:    {result['pct_display']}",
        f"  容差:        {result['tolerance']:.4%}",
        "",
        f"  结论: {result['status']}",
    ]

    if result["within_tolerance"]:
        lines.append("  差异在容差内，记录后可关闭。")
    else:
        lines += [
            "",
            "  排查建议：",
            "  1. 先核对指标定义（分子/分母/统计对象）。",
            "  2. 对比过滤条件：状态、地区、事项范围。",
            "  3. 对比关联方式与关联键，检查是否漏数或放大。",
            "  4. 对比统计粒度与去重逻辑。",
            "  5. 对齐时间字段与双方数据截止时间。",
            "  6. 按地区/部门/事项类型下钻，定位差异集中区域。",
            "  7. 填写 assets/reconciliation_report_template.md。",
        ]

    lines.append("=" * 64)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="政务指标口径对账")
    parser.add_argument("--values", nargs=2, type=float, metavar=("A", "B"), help="直接比较两个值")
    parser.add_argument("--source-a", help="来源 A 的 CSV 文件")
    parser.add_argument("--source-b", help="来源 B 的 CSV 文件")
    parser.add_argument("--metric", default="value", help="指标列名")
    parser.add_argument("--date-col", default=None, help="日期列名")
    parser.add_argument("--date", default=None, help="筛选日期，如 2026-10-31")
    parser.add_argument("--tolerance", type=float, default=0.001,
                        help="可接受差异比例，默认 0.001（0.1%%）")
    parser.add_argument("--label-a", default="来源 A")
    parser.add_argument("--label-b", default="来源 B")
    parser.add_argument("--encoding", help="可选：CSV 编码")
    args = parser.parse_args()

    if args.values:
        value_a, value_b = args.values
    elif args.source_a and args.source_b:
        try:
            value_a = load_metric_from_csv(args.source_a, args.metric, args.date_col, args.date, args.encoding)
            value_b = load_metric_from_csv(args.source_b, args.metric, args.date_col, args.date, args.encoding)
        except (OSError, ValueError) as exc:
            print(f"取数失败：{exc}", file=sys.stderr)
            sys.exit(2)
    else:
        parser.error("请提供 --values，或同时提供 --source-a 与 --source-b")

    result = compare_values(value_a, value_b, args.tolerance)
    print(build_report(result, args.label_a, args.label_b))
    sys.exit(0 if result["within_tolerance"] else 1)


def demo() -> None:
    result = compare_values(125_000.0, 118_120.0, tolerance=0.001)
    print(build_report(result, "大屏（来源 A）", "月报（来源 B）"))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
