# SQL Tool

`sql-tool` is a command-line utility for exploring and querying SQL databases. It provides tools to list tables, inspect schema definitions, and execute SQL queries interactively.

## Features

- List all table names in the connected database
- Filter tables by substring
- View schema and relation information for tables
- Execute arbitrary SQL queries and view results
- Read-only and write modes supported

## Installation

Clone the repository and install dependencies:

```sh
pip install "git+https://github.com/Phanith-LIM/sql-tool.git"
```
```sh
uv add "git@+github.com:Phanith-LIM/sql-tool.git"
```
## Usage
Start the server with the following command:
```python
res_sqlite = StdioServerParameters(
    command= "uv",
	args= ["run", "sql-tool"],
    env= {
        "DB_URL": "sqlite:///titanic.db",
    }
)
```
