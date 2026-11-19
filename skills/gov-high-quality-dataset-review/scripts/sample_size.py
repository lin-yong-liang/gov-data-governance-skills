"""
计算人工复核所需样本量（比例估计 + 有限总体校正）。

用法：
    python sample_size.py --population 120000 --confidence 0.95 --margin 0.05
    python sample_size.py --population 800 --confidence 0.99 --margin 0.05 --p 0.5

仅标准库。纯本地运行，不访问网络。
"""

from __future__ import annotations

import argparse
import math
import sys
from statistics import NormalDist


def z_value(confidence: float) -> float:
    return NormalDist().inv_cdf(1 - (1 - confidence) / 2)


def calculate(population: int, confidence: float, margin: float, p: float) -> dict:
    if not 0 < confidence < 1:
        raise ValueError("confidence 必须在 0 和 1 之间")
    if not 0 < margin < 1:
        raise ValueError("margin 必须在 0 和 1 之间")
    if not 0 < p < 1:
        raise ValueError("p 必须在 0 和 1 之间")
    if population <= 0:
        raise ValueError("population 必须为正整数")

    z = z_value(confidence)
    n0 = z * z * p * (1 - p) / (margin * margin)
    n = n0 / (1 + (n0 - 1) / population)
    return {
        "z": z,
        "n0": n0,
        "n": math.ceil(n),
        "population": population,
        "confidence": confidence,
        "margin": margin,
        "p": p,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="抽样样本量计算")
    parser.add_argument("--population", type=int, required=False, default=120000, help="总体规模")
    parser.add_argument("--confidence", type=float, default=0.95, help="置信水平，默认 0.95")
    parser.add_argument("--margin", type=float, default=0.05, help="允许误差，默认 0.05")
    parser.add_argument("--p", type=float, default=0.5, help="预期比例，未知取 0.5（最保守）")
    args = parser.parse_args()

    try:
        result = calculate(args.population, args.confidence, args.margin, args.p)
    except ValueError as exc:
        print(f"参数错误：{exc}", file=sys.stderr)
        sys.exit(2)

    print("=" * 56)
    print("抽样样本量计算结果")
    print("=" * 56)
    print(f"  总体规模 N:      {result['population']:,}")
    print(f"  置信水平:        {result['confidence']:.0%}")
    print(f"  允许误差:        ±{result['margin']:.1%}")
    print(f"  预期比例 p:      {result['p']:.2f}")
    print(f"  Z 值:            {result['z']:.4f}")
    print(f"  理论样本量 n0:   {math.ceil(result['n0']):,}")
    print(f"  校正后样本量 n:  {result['n']:,}")
    print("=" * 56)
    print("说明：")
    print("- 上述为简单随机抽样样本量；分层抽样按各层规模比例分配，重点层设最低样本量。")
    print("- 确定性规则（空值、重复、格式、PII）建议全量扫描，不抽样。")
    print("- 标签质量人工复核需保证每个类别至少 100 条或全量。")
    print("- 样本量是最低要求，风险高的数据集应适当增加。")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        result = calculate(120000, 0.95, 0.05, 0.5)
        print(f"默认参数（N=120000，95%，±5%）样本量：{result['n']}")
    else:
        main()
