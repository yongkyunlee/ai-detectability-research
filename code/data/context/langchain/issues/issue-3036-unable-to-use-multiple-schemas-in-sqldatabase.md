# Unable to use multiple schemas in SQLDatabase

**Issue #3036** | State: closed | Created: 2023-04-17 | Updated: 2026-03-16
**Author:** engma-linguistics

I'd like to be able to run a query via SQLDatabaseSequentialChain or SQLDatabaseChain involving multiple tables living in multiple different schemas, but it seems that as it is, the code is set up to only allow and look through just the one schema provided.

## Comments

**parkerdgabel:**
Looking through the code this should be possible. I'll take a look into adding multiple schema support.

**engma-linguistics:**
That would be huge! Thank you.

**freedeaths:**
Change sql_database.py like this?
PS: It works, but it change the parameter `schema` type from Optional[str] to Optional[List[str]]. Or is it necessary to use schema as 'schema_1, schema_2' and self._schema = [s.strip() for s in schema.split(',')]?

```python
"""SQLAlchemy wrapper around a database."""
from __future__ import annotations

import warnings
from typing import Any, Iterable, List, Optional

from sqlalchemy import MetaData, Table, create_engine, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.schema import CreateTable


def _format_index(index: dict) -> str:
    return (
        f'Name: {index["name"]}, Unique: {index["unique"]},'
        f' Columns: {str(index["column_names"])}'
    )


class SQLDatabase:
    """SQLAlchemy wrapper around a database."""

    def __init__(
        self,
        engine: Engine,
        schema: Optional[List(str)] = None,
        metadata: Optional[MetaData] = None,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: Optional[dict] = None,
        view_support: Optional[bool] = False,
    ):
        """Create engine from database URI."""
        self._engine = engine
        self._schema = schema
        if include_tables and ignore_tables:
            raise ValueError("Cannot specify both include_tables and ignore_tables")

        self._inspector = inspect(self._engine)

        self._all_tables_per_schema = {}
        for schema in self._schema:
            self._all_tables_per_schema[schema] = set(
                self._inspector.get_table_names(schema=schema)
                + (self._inspector.get_view_names(schema=schema) if view_support else [])
            )

        # including view support by adding the views as well as tables to the all
        # tables list if view_support is True
        self._all_tables = set(value for values in self._all_tables_per_schema.values() for value in values)

        self._include_tables = set(include_tables) if include_tables else set()
        if self._include_tables:
            missing_tables = self._include_tables - self._all_tables
            if missing_tables:
                raise ValueError(
                    f"include_tables {missing_tables} not found in database"
                )
        self._ignore_tables = set(ignore_tables) if ignore_tables else set()
        if self._ignore_tables:
            missing_tables = self._ignore_tables - self._all_tables
            if missing_tables:
                raise ValueError(
                    f"ignore_tables {missing_tables} not found in database"
                )
        usable_tables = self.get_usable_table_names()
        self._usable_tables = set(usable_tables) if usable_tables else self._all_tables

        if not isinstance(sample_rows_in_table_info, int):
            raise TypeError("sample_rows_in_table_info must be an integer")

        self._sample_rows_in_table_info = sample_rows_in_table_info
        self._indexes_in_table_info = indexes_in_table_info

        self._custom_table_info = custom_table_info
        if self._custom_table_info:
            if not isinstance(self._custom_table_info, dict):
                raise TypeError(
                    "table_info must be a dictionary with table names as keys and the "
                    "desired table info as values"
                )
            # only keep the tables that are also present in the database
            intersection = set(self._custom_table_info).intersection(self._all_tables)
            self._custom_table_info = dict(
                (table, self._custom_table_info[table])
                for table in self._custom_table_info
                if table in intersection
            )

        self._metadata = metadata or MetaData()
        # including view support if view_support = true
        for schema in self._schema:
            self._metadata.reflect(
                views=view_support,
                bind=self._engine,
                only=self._all_tables_per_schema[schema],
                schema=schema,
            )

    @classmethod
    def from_uri(
        cls, database_uri: str, engine_args: Optional[dict] = None, **kwargs: Any
    ) -> SQLDatabase:
        """Construct a SQLAlchemy engine from URI."""
        _engine_args = engine_args or {}
        return cls(create_engine(database_uri, **_engine_args), **kwargs)

    @property
    def dialect(self) -> str:
        """Return string representation of dialect to use."""
        return self._engine.dialect.name

    def get_usable_table_names(self) -> Iterable[str]:
        """Get names of tables available."""
        if self._include_tables:
            return self._include_tables
        return self._all_tables - self._ignore_tables

    def get_table_names(self) -> Iterable[str]:
        """Get names of tables available."""
        warnings.warn(
            "This method is deprecated - please use `get_usable_table_names`."
        )
        return self.get_usable_table_names()

    @property
    def table_info(self) -> str:
        """Information about all tables in the database."""
        return self.get_table_info()

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_table_info`, the specified number of sample rows will be
        appended to each table description. This can increase performance as
        demonstrated in the paper.
        """
        all_table_names = self.get_usable_table_names()
        if table_names is not None:
            missing_tables = set(table_names).difference(all_table_names)
            if missing_tables:
                raise ValueError(f"table_names {missing_tables} not found in database")
            all_table_names = table_names

        meta_tables = [
            tbl
            for tbl in self._metadata.sorted_tables
            if tbl.name in set(all_table_names)
            and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
        ]

        tables = []
        for table in meta_tables:
            if self._custom_table_info and table.name in self._custom_table_info:
                tables.append(self._custom_table_info[table.name])
                continue

            # add create table command
            create_table = str(CreateTable(table).compile(self._engine))
            table_info = f"{create_table.rstrip()}"
            has_extra_info = (
                self._indexes_in_table_info or self._sample_rows_in_table_info
            )
            if has_extra_info:
                table_info += "\n\n/*"
            if self._indexes_in_table_info:
                table_info += f"\n{self._get_table_indexes(table)}\n"
            if self._sample_rows_in_table_info:
                table_info += f"\n{self._get_sample_rows(table)}\n"
            if has_extra_info:
                table_info += "*/"
            tables.append(table_info)
        final_str = "\n\n".join(tables)
        return final_str

    def _get_table_indexes(self, table: Table) -> str:
        indexes = self._inspector.get_indexes(table.name)
        indexes_formatted = "\n".join(map(_format_index, indexes))
        return f"Table Indexes:\n{indexes_formatted}"

    def _get_sample_rows(self, table: Table) -> str:
        # build the select command
        command = select([table]).limit(self._sample_rows_in_table_info)

        # save the columns in string format
        columns_str = "\t".join([col.name for col in table.columns])

        try:
            # get the sample rows
            with self._engine.connect() as connection:
                sample_rows = connection.execute(command)
                # shorten values in the sample rows
                sample_rows = list(
                    map(lambda ls: [str(i)[:100] for i in ls], sample_rows)
                )

            # save the sample rows in string format
            sample_rows_str = "\n".join(["\t".join(row) for row in sample_rows])

        # in some dialects when there are no rows in the table a
        # 'ProgrammingError' is returned
        except ProgrammingError:
            sample_rows_str = ""

        return (
            f"{self._sample_rows_in_table_info} rows from {table.name} table:\n"
            f"{columns_str}\n"
            f"{sample_rows_str}"
        )

    def run(self, command: str, fetch: str = "all") -> str:
        """Execute a SQL command and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.
        """
        with self._engine.begin() as connection:
            if self._schema is not None:
                connection.exec_driver_sql(f"SET search_path TO {self._schema}")
            cursor = connection.execute(text(command))
            if cursor.returns_rows:
                if fetch == "all":
                    result = cursor.fetchall()
                elif fetch == "one":
                    result = cursor.fetchone()[0]
                else:
                    raise ValueError("Fetch parameter must be either 'one' or 'all'")
                return str(result)
        return ""

    def get_table_info_no_throw(self, table_names: Optional[List[str]] = None) -> str:
        """Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_table_info`, the specified number of sample rows will be
        appended to each table description. This can increase performance as
        demonstrated in the paper.
        """
        try:
            return self.get_table_info(table_names)
        except ValueError as e:
            """Format the error message"""
            return f"Error: {e}"

    def run_no_throw(self, command: str, fetch: str = "all") -> str:
        """Execute a SQL command and return a string representing the results.

        If the statement returns rows, a string of the results is returned.
        If the statement returns no rows, an empty string is returned.

        If the statement throws an error, the error message is returned.
        """
        try:
            return self.run(command, fetch)
        except SQLAlchemyError as e:
            """Format the error message"""
            return f"Error: {e}"

```

**yb-yu:**
Hello, is anyone currently working on this issue? It doesn't seem like there's an assignee.

If no one is on it, would it be okay if I take it on? 👀

**osoucy-newton:**
I also had to support the same use case and I came up with this subclass of `SQLDatabase`.

It seems to work great for me. Maybe I should PR this changes? Although they would be a breaking change given the `schema` argument has been changed to `schemas`


```python
"""SQLAlchemy wrapper around a database."""
from __future__ import annotations

from typing import Any, List, Optional

from sqlalchemy import MetaData, create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable

from langchain import utils
from langchain import SQLDatabase as _SQLDatabase


class SQLDatabase(_SQLDatabase):
    """SQLAlchemy wrapper around a database."""

    def __init__(
        self,
        engine: Engine,
        schemas: List[str],
        metadata: Optional[MetaData] = None,
        ignore_tables: Optional[List[str]] = None,
        include_tables: Optional[List[str]] = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: Optional[dict] = None,
        view_support: bool = False,
        max_string_length: int = 300,
    ):
        """Create engine from database URI."""
        self._engine = engine
        self._schema = None
        self._schemas = schemas
        if include_tables and ignore_tables:
            raise ValueError("Cannot specify both include_tables and ignore_tables")

        self._inspector = inspect(self._engine)

        # including view support by adding the views as well as tables to the all
        # tables list if view_support is True
        self._all_tables_per_schema = {}
        for schema in self._schemas:
            self._all_tables_per_schema[schema] = set(
                self._inspector.get_table_names(schema=schema)
                + (self._inspector.get_view_names(schema=schema) if view_support else [])
            )
        self._all_tables = set(f"{k}.{name}" for k, names in self._all_tables_per_schema.items() for name in names)

        self._include_tables = set(include_tables) if include_tables else set()
        if self._include_tables:
            missing_tables = self._include_tables - self._all_tables
            if missing_tables:
                raise ValueError(
                    f"include_tables {missing_tables} not found in database"
                )
        self._ignore_tables = set(ignore_tables) if ignore_tables else set()
        if self._ignore_tables:
            missing_tables = self._ignore_tables - self._all_tables
            if missing_tables:
                raise ValueError(
                    f"ignore_tables {missing_tables} not found in database"
                )
        usable_tables = self.get_usable_table_names()
        self._usable_tables = set(usable_tables) if usable_tables else self._all_tables

        if not isinstance(sample_rows_in_table_info, int):
            raise TypeError("sample_rows_in_table_info must be an integer")

        self._sample_rows_in_table_info = sample_rows_in_table_info
        self._indexes_in_table_info = indexes_in_table_info

        self._custom_table_info = custom_table_info
        if self._custom_table_info:
            if not isinstance(self._custom_table_info, dict):
                raise TypeError(
                    "table_info must be a dictionary with table names as keys and the "
                    "desired table info as values"
                )
            # only keep the tables that are also present in the database
            intersection = set(self._custom_table_info).intersection(self._all_tables)
            self._custom_table_info = dict(
                (table, self._custom_table_info[table])
                for table in self._custom_table_info
                if table in intersection
            )

        self._max_string_length = max_string_length

        self._metadata = metadata or MetaData()
        # including view support if view_support = true

        for schema in self._schemas:
            self._metadata.reflect(
                views=view_support,
                bind=self._engine,
                only=[v.split(".")[-1] for v in self._usable_tables if v.startswith(schema)],
                schema=schema,
            )

        # Add id to tables metadata
        for t in self._metadata.sorted_tables:
            t.id = f"{t.schema}.{t.name}"

    @classmethod
    def from_uri(
        cls,
        database_uri: str,
        schemas: Optional[List[str]] = None,
        engine_args: Optional[dict] = None,
        **kwargs: Any
    ) -> SQLDatabase:
        """Construct a SQLAlchemy engine from URI."""
        _engine_args = engine_args or {}
        engine = create_engine(database_uri, **_engine_args)
        return cls(engine, schemas=schemas, **kwargs)

    @classmethod
    def from_databricks(
        cls,
        catalog: str,
        schemas: Optional[List[str]] = None,
        host: Optional[str] = None,
        api_token: Optional[str] = None,
        warehouse_id: Optional[str] = None,
        cluster_id: Optional[str] = None,
        engine_args: Optional[dict] = None,
        **kwargs: Any,
    ) -> SQLDatabase:
        """
        Class method to create an SQLDatabase instance from a Databricks connection.
        This method requires the 'databricks-sql-connector' package. If not installed,
        it can be added using `pip install databricks-sql-connector`.

        Args:
            catalog (str): The catalog name in the Databricks database.
            schemas (List[str[): The schema name(s) in the catalog
            host (Optional[str]): The Databricks workspace hostname, excluding
                'https://' part. If not provided, it attempts to fetch from the
                environment variable 'DATABRICKS_HOST'. If still unavailable and if
                running in a Databricks notebook, it defaults to the current workspace
                hostname. Defaults to None.
            api_token (Optional[str]): The Databricks personal access token for
                accessing the Databricks SQL warehouse or the cluster. If not provided,
                it attempts to fetch from 'DATABRICKS_TOKEN'. If still unavailable
                and running in a Databricks notebook, a temporary token for the current
                user is generated. Defaults to None.
            warehouse_id (Optional[str]): The warehouse ID in the Databricks SQL. If
                provided, the method configures the connection to use this warehouse.
                Cannot be used with 'cluster_id'. Defaults to None.
            cluster_id (Optional[str]): The cluster ID in the Databricks Runtime. If
                provided, the method configures the connection to use this cluster.
                Cannot be used with 'warehouse_id'. If running in a Databricks notebook
                and both 'warehouse_id' and 'cluster_id' are None, it uses the ID of the
                cluster the notebook is attached to. Defaults to None.
            engine_args (Optional[dict]): The arguments to be used when connecting
                Databricks. Defaults to None.
            **kwargs (Any): Additional keyword arguments for the `from_uri` method.

        Returns:
            SQLDatabase: An instance of SQLDatabase configured with the provided
                Databricks connection details.

        Raises:
            ValueError: If 'databricks-sql-connector' is not found, or if both
                'warehouse_id' and 'cluster_id' are provided, or if neither
                'warehouse_id' nor 'cluster_id' are provided and it's not executing
                inside a Databricks notebook.
        """
        try:
            from databricks import sql  # noqa: F401
        except ImportError:
            raise ValueError(
                "databricks-sql-connector package not found, please install with"
                " `pip install databricks-sql-connector`"
            )
        context = None
        try:
            from dbruntime.databricks_repl_context import get_context

            context = get_context()
        except ImportError:
            pass

        default_host = context.browserHostName if context else None
        if host is None:
            host = utils.get_from_env("host", "DATABRICKS_HOST", default_host)

        default_api_token = context.apiToken if context else None
        if api_token is None:
            api_token = utils.get_from_env(
                "api_token", "DATABRICKS_TOKEN", default_api_token
            )

        if warehouse_id is None and cluster_id is None:
            if context:
                cluster_id = context.clusterId
            else:
                raise ValueError(
                    "Need to provide either 'warehouse_id' or 'cluster_id'."
                )

        if warehouse_id and cluster_id:
            raise ValueError("Can't have both 'warehouse_id' or 'cluster_id'.")

        if warehouse_id:
            http_path = f"/sql/1.0/warehouses/{warehouse_id}"
        else:
            http_path = f"/sql/protocolv1/o/0/{cluster_id}"

        uri = (
            f"databricks://token:{api_token}@{host}?"
            f"http_path={http_path}&catalog={catalog}"
        )
        return cls.from_uri(database_uri=uri, schemas=schemas, engine_args=engine_args, **kwargs)

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """Get information about specified tables.

        Follows best practices as specified in: Rajkumar et al, 2022
        (https://arxiv.org/abs/2204.00498)

        If `sample_rows_in_table_info`, the specified number of sample rows will be
        appended to each table description. This can increase performance as
        demonstrated in the paper.
        """
        all_table_names = self.get_usable_table_names()
        if table_names is not None:
            missing_tables = set(table_names).difference(all_table_names)
            if missing_tables:
                raise ValueError(f"table_names {missing_tables} not found in database")
            all_table_names = table_names

        meta_tables = [
            tbl
            for tbl in self._metadata.sorted_tables
            if tbl.id in set(all_table_names)
            and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
        ]

        tables = []
        for table in meta_tables:
            if self._custom_table_info and table.name in self._custom_table_info:
                tables.append(self._custom_table_info[table.name])
                continue

            # add create table command
            create_table = str(CreateTable(table).compile(self._engine))
            table_info = f"{create_table.rstrip()}"
            has_extra_info = (
                self._indexes_in_table_info or self._sample_rows_in_table_info
            )
            if has_extra_info:
                table_info += "\n\n/*"
            if self._indexes_in_table_info:
                table_info += f"\n{self._get_table_indexes(table)}\n"
            if self._sample_rows_in_table_info:
                table_info += f"\n{self._get_sample_rows(table)}\n"
            if has_extra_info:
                table_info += "*/"
            tables.append(table_info)
        final_str = "\n\n".join(tables)
        return final_str

```

**osoucy-newton:**
Maybe it's an error specific to the engine you are using for your database / SQLAlchemy. I'm using Databricks SQL warehouse. What exactly is the error?

**txge:**
Is this currently being worked on? Our use case is impacted/limited by this too. Happy to contribute.

**gillan-satsure:**
Same issue for me. Seems to take only one schema, no choice in the matter as well

**ElderBlade:**
Is there any update on this? I also need to access tables in different schemas.

**Repskin:**
If you are using MSSQL like me, search_path is not available so if you want to bypass this issue, you can create synonym for each table directly in MSSQL. It's not the best solution but it can fix that issue (i am referring synonym directly in the prompt).
