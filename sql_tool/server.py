import os
from datetime import datetime, date
from sqlalchemy import create_engine, text, inspect
from mcp.server import FastMCP

mcp = FastMCP(
    "SQL Tool",
    description="A tool for executing SQL queries and retrieving database schema information.",
)

def get_engine(readonly=True):
    return create_engine(
        os.environ['DB_URL'],
        isolation_level='AUTOCOMMIT',
        execution_options={'readonly': readonly}
    )

def get_db_info():
    engine = get_engine(readonly=True)
    with engine.connect():
        url = engine.url
        result = {
            "dialect": engine.dialect.name,
            "version": list(engine.dialect.server_version_info),
            "database": url.database,
            "host": url.host,
            "user": url.username
        }
        return result

DB_INFO = get_db_info()
PREFIX = os.environ.get('PREFIX', 'sql_tool')
EXECUTE_QUERY_MAX_CHARS = int(os.environ.get('EXECUTE_QUERY_MAX_CHARS', 4000))

def format_value(val):
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return val  # keep None or native types

@mcp.tool(name=f"{PREFIX}_all_table_names", description=f"Return all table names in the database separated by comma. {DB_INFO}")
def all_table_names() -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(inspector.get_table_names())


@mcp.tool(
    name=f"{PREFIX}_filter_table_names",
    description=f"Return all table names in the database containing the substring 'q' separated by comma. {DB_INFO}"
)
def filter_table_names(q: str) -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(x for x in inspector.get_table_names() if q in x)

@mcp.tool(name=f"{PREFIX}_schema_definitions", description=f"Returns schema and relation information for the given tables. {DB_INFO}")
def schema_definitions(table_names: list[str]) -> dict:
    engine = get_engine()
    inspector = inspect(engine)
    schema_data = {}

    for table in table_names:
        columns = inspector.get_columns(table)
        foreign_keys = inspector.get_foreign_keys(table)
        primary_keys = set(inspector.get_pk_constraint(table)["constrained_columns"])

        schema_data[table] = {
            "columns": [
                {
                    **{k: v for k, v in col.items() if k != "comment"},
                    "primary_key": col["name"] in primary_keys
                }
                for col in columns
            ],
            "relationships": [
                {
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                }
                for fk in foreign_keys
            ]
        }

    return schema_data

def execute_query_description():
    parts = [
        f"Execute a SQL query and return results in a readable format. Results will be truncated after {EXECUTE_QUERY_MAX_CHARS} characters."
    ]
    parts.append(
        "IMPORTANT: Always use the params parameter for query parameter substitution (e.g. 'WHERE id = :id' with "
        "params={'id': 123}) to prevent SQL injection. Direct string concatenation is a serious security risk.")
    parts.append(DB_INFO)
    return " ".join(parts)

@mcp.tool(name=f"{PREFIX}_execute_query", description=execute_query_description())
def execute_query(query: str, params: dict = {}) -> dict:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            if query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                columns = result.keys()
                return {
                    "columns": list(columns),
                    "rows": [[format_value(val) for val in row] for row in rows]
                }
            else:
                return {"status": "ok"}
    except Exception as e:
        return {"error": str(e)}

def main():
    mcp.run()

if __name__ == "__main__":
    main()
