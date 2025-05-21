import os
from datetime import datetime, date
from sqlalchemy import create_engine, text, inspect
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SQL Tools")

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
        result = [
            f"Connected to {engine.dialect.name}",
            f"version {'.'.join(str(x) for x in engine.dialect.server_version_info)}",
            f"database {url.database}",
        ]
        if url.host:
            result.append(f"on {url.host}")
        if url.username:
            result.append(f"as user {url.username}")
        return " ".join(result) + "."
    
DB_INFO = get_db_info()
PREFIX = os.environ.get('PREFIX', 'sql_tool')
EXECUTE_QUERY_MAX_CHARS = int(os.environ.get('EXECUTE_QUERY_MAX_CHARS', 4000))

def format_value(val):
    if val is None:
        return "NULL"
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    return str(val)

@mcp.tool(
    name="all_table_names_{PREFIX}",
    description=f"Return all table names in the database separated by comma. {DB_INFO}"
)
def all_table_names() -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(inspector.get_table_names())

@mcp.tool(
    name="filter_table_names_{PREFIX}",
    description=f"Return all table names in the database containing the substring 'q' separated by comma. {DB_INFO}"
)
def filter_table_names(q: str) -> str:
    engine = get_engine()
    inspector = inspect(engine)
    return ", ".join(x for x in inspector.get_table_names() if q in x)

@mcp.tool(
    name="schema_definitions_{PREFIX}",
    description=f"Returns schema and relation information for the given tables. {DB_INFO}"
)
def schema_definitions(table_names: list[str]) -> str:
    def format(inspector, table_name):
        columns = inspector.get_columns(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        primary_keys = set(inspector.get_pk_constraint(table_name)["constrained_columns"])
        result = [f"{table_name}:"]

        # Process columns
        show_key_only = {"nullable", "autoincrement"}
        for column in columns:
            if "comment" in column:
                del column["comment"]
            name = column.pop("name")
            column_parts = (["primary key"] if name in primary_keys else []) + [str(
                column.pop("type"))] + [k if k in show_key_only else f"{k}={v}" for k, v in column.items() if v]
            result.append(f"    {name}: " + ", ".join(column_parts))

        # Process relationships
        if foreign_keys:
            result.extend(["", "    Relationships:"])
            for fk in foreign_keys:
                constrained_columns = ", ".join(fk['constrained_columns'])
                referred_table = fk['referred_table']
                referred_columns = ", ".join(fk['referred_columns'])
                result.append(f"      {constrained_columns} -> {referred_table}.{referred_columns}")

        return "\n".join(result)

@mcp.tool(
    name="execute_query_{PREFIX}",
    description="Executes a SQL query against the database and returns the results."
)
def execute_query(query: str, params: dict = {}) -> str:
    engine = get_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})  # Ensure params is not None

            if query.strip().upper().startswith("SELECT"):
                rows = result.fetchall()
                if rows:
                    header = " | ".join(result.keys())
                    lines = [" | ".join(format_value(v) for v in row) for row in rows]
                    return header + "\n" + "-" * len(header) + "\n" + "\n".join(lines)
                else:
                    return "No results found."
            else:
                return "Query executed successfully."

    except Exception as e:
        return f"Error executing query: {e}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
