"""
政务数据目录技术元数据提取器

从 SQLAlchemy 兼容数据库提取表结构、主外键、行数，生成中文目录条目草稿。

用法：
    python catalog_extractor.py --conn "sqlite:///demo.db" --table t_person
    python catalog_extractor.py --conn "postgresql://user:pass@host/db" --table t_person --schema public --output draft.md

依赖：sqlalchemy（pip install sqlalchemy），以及对应数据库驱动。
只读元数据与行数，不修改数据；不访问外部网络（连接串由用户显式提供）。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone


def _try_import_sqlalchemy():
    try:
        import sqlalchemy as sa
        return sa
    except ImportError:
        return None


def extract_metadata(conn_string: str, table_name: str, schema: str | None = None) -> dict:
    sa = _try_import_sqlalchemy()
    if sa is None:
        raise ImportError("需要 sqlalchemy：pip install sqlalchemy，并安装对应数据库驱动")

    engine = sa.create_engine(conn_string)
    inspector = sa.inspect(engine)

    columns_raw = inspector.get_columns(table_name, schema=schema)
    pk = inspector.get_pk_constraint(table_name, schema=schema) or {}
    pk_cols = set(pk.get("constrained_columns") or [])
    fks = inspector.get_foreign_keys(table_name, schema=schema) or []
    fk_cols = {c for fk in fks for c in (fk.get("constrained_columns") or [])}

    columns = []
    for col in columns_raw:
        columns.append({
            "name": col["name"],
            "type": str(col.get("type", "")),
            "nullable": col.get("nullable", True),
            "primary_key": col["name"] in pk_cols,
            "foreign_key": col["name"] in fk_cols,
            "comment": col.get("comment") or "",
        })

    qualified = f"{schema}.{table_name}" if schema else table_name
    table = sa.Table(table_name, sa.MetaData(), schema=schema, autoload_with=engine)
    with engine.connect() as conn:
        row_count = conn.execute(sa.select(sa.func.count()).select_from(table)).scalar()

    return {
        "table_name": table_name,
        "schema": schema or "默认",
        "qualified_name": qualified,
        "extracted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "row_count": int(row_count or 0),
        "columns": columns,
        "foreign_keys": fks,
    }


def render_markdown(meta: dict) -> str:
    lines = [
        f"# 政务数据资源目录条目：{meta['table_name']}",
        "",
        "## 一、基本信息",
        "",
        "| 要素 | 内容 |",
        "|---|---|",
        f"| 资源名称 | {meta['table_name']} |",
        "| 资源代码 | [待填写] |",
        "| 资源类型 | 库表 |",
        "| 所属主题 / 领域 | [待填写] |",
        "| 资源摘要 | [一句话说明数据内容和用途] |",
        f"| 库表名 | `{meta['qualified_name']}` |",
        f"| 数据量 | {meta['row_count']:,} 行（提取时点） |",
        f"| 提取时间 | {meta['extracted_at']} |",
        "",
        "## 二、权属与权威源",
        "",
        "| 要素 | 内容 |",
        "|---|---|",
        "| 提供方 | [待填写] |",
        "| 数据 Owner | [待填写] |",
        "| 技术支撑单位 | [待填写] |",
        "| 是否权威源 | 是 / 否 / 待确认 |",
        "| 一数一源说明 | [待填写] |",
        "",
        "## 三、共享与开放属性",
        "",
        "| 要素 | 内容 |",
        "|---|---|",
        "| 共享属性 | 无条件共享 / 有条件共享 / 不予共享 |",
        "| 共享依据 | [有条件共享写条件；不予共享写法定依据] |",
        "| 共享方式 | 接口 / 批量文件 / 库表 |",
        "| 更新周期 | 实时 / 日更 / 周更 / 月更 |",
        "| 开放属性 | 无条件开放 / 有条件开放 / 不予开放 |",
        "| 开放依据 | [待填写] |",
        "",
        "## 四、数据结构",
        "",
        f"- **主键：** {', '.join(c['name'] for c in meta['columns'] if c['primary_key']) or '[待填写]'}",
        f"- **外键：** {len(meta['foreign_keys'])} 个（详见数据项说明）",
        f"- **行数：** {meta['row_count']:,}",
        "",
        "## 五、数据项说明",
        "",
        "| 序号 | 中文名 | 英文名 | 类型 | 可空 | 键 | 注释 | 业务定义 | 值域 | 是否敏感 |",
        "|---:|---|---|---|---|---|---|---|---|---|",
    ]

    for idx, col in enumerate(meta["columns"], start=1):
        keys = []
        if col["primary_key"]:
            keys.append("PK")
        if col["foreign_key"]:
            keys.append("FK")
        lines.append(
            f"| {idx} | [待填写] | {col['name']} | {col['type']} "
            f"| {'是' if col['nullable'] else '否'} | {', '.join(keys) or '-'} "
            f"| {col['comment'] or ''} | [待填写] | [待填写] | [是/否] |"
        )

    lines += [
        "",
        "## 六、数据质量",
        "",
        "- 最近稽核日期：[待填写]",
        "- 稽核报告编号：[待填写]",
        "- 已知问题：[待填写]",
        "",
        "## 七、血缘",
        "",
        "- **上游来源：** [待填写]",
        "- **下游使用方：** [待填写]",
        "- **加工链路：** [待填写]",
        "",
        "## 八、安全与分类分级",
        "",
        "- **数据分类：** [待填写]",
        "- **数据分级：** 核心 / 重要 / 一般",
        "- **个人信息标识：** 无 / 一般个人信息 / 敏感个人信息",
        "- **敏感程度：** 公开 / 内部 / 敏感 / 涉密",
        "- **脱敏要求：** [待填写]",
        "",
        "## 九、版本与审核",
        "",
        "- **版本号：** V0.1（草稿）",
        "- **编制人：** [待填写]",
        "- **审核人：** [待填写]",
        f"- **生成时间：** {meta['extracted_at']}",
        "",
        "---",
        "",
        "*由 catalog_extractor.py 生成，业务要素需人工补全后方可发布。*",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="提取数据库表结构，生成政务目录条目草稿")
    parser.add_argument("--conn", required=True, help="SQLAlchemy 连接串")
    parser.add_argument("--table", required=True, help="表名")
    parser.add_argument("--schema", default=None, help="模式名")
    parser.add_argument("--output", default=None, help="输出 Markdown 文件路径")
    args = parser.parse_args()

    try:
        meta = extract_metadata(args.conn, args.table, args.schema)
    except Exception as exc:
        print(f"提取失败：{exc}", file=sys.stderr)
        sys.exit(2)

    markdown = render_markdown(meta)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"目录草稿已写入 {args.output}")
    else:
        print(markdown)


def demo() -> None:
    demo_meta = {
        "table_name": "t_person",
        "schema": "public",
        "qualified_name": "public.t_person",
        "extracted_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "row_count": 1250000,
        "foreign_keys": [],
        "columns": [
            {"name": "id_number", "type": "CHAR(18)", "nullable": False, "primary_key": True, "foreign_key": False, "comment": "公民身份号码"},
            {"name": "name", "type": "VARCHAR(50)", "nullable": False, "primary_key": False, "foreign_key": False, "comment": "姓名"},
            {"name": "gender", "type": "CHAR(1)", "nullable": True, "primary_key": False, "foreign_key": False, "comment": "性别"},
        ],
    }
    print(render_markdown(demo_meta))


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        main()
