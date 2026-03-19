---
source_url: https://duckdb.org/2025/03/28/using-duckdb-in-streamlit.html
author: "Petrica Leuca"
platform: duckdb.org (official blog)
scope_notes: "Trimmed from full Streamlit tutorial to focus on DuckDB Python client setup and connection patterns. Original post ~2000 words; trimmed to ~450 words covering connection methods and basic Python relational API usage."
---

The article demonstrates how to build a Streamlit application using a real-world Dutch railway dataset, connecting to DuckDB via its Python client. The application code is available on GitHub in the duckdb-blog-examples repository.

## Connecting to DuckDB in Streamlit

The database preparation function creates tables from remote CSV files:

```python
def prepare_duckdb(duckdb_conn):
    duckdb_conn.sql("""
        create table if not exists services as
        from 'https://blobs.duckdb.org/nl-railway/services-2024.csv.gz'
    """)

    duckdb_conn.sql("""
        create table if not exists stations as
        from 'https://blobs.duckdb.org/nl-railway/stations-2023-09.csv'
    """)
```

### Three Connection Methods

**In-Memory Connection with Caching:**

```python
@st.cache_resource(ttl=datetime.timedelta(hours=1), max_entries=2)
def get_duckdb_memory(session_id):
    duckdb_conn = duckdb.connect()
    prepare_duckdb(duckdb_conn=duckdb_conn)
    return duckdb_conn
```

**Persisted Local File Connection:**

```python
duckdb_conn = duckdb.connect(
    "train_stations_and_services.duckdb",
    read_only=True
)
```

**Attaching an External Database:**

```python
duckdb_conn = duckdb.connect()
duckdb_conn.execute(f"attach '{DUCKDB_EXTERNAL_LOCATION}' as ext_db")
duckdb_conn.execute("use ext_db")
```

DuckDB works best if you have allocated 1-4GB of memory per thread. The recommendation is to use a new connection per database interaction or at user session level, avoiding global connections.

## Analyzing Data with the Python Relational API

The Python relational API uses lazy evaluation. Execution occurs when calling `.df()` to extract to a Pandas dataframe, `.fetchall()` to extract in a list, `.write_to()` to export the data in a file, or calculation methods such as `.sum`, `.row_number`, etc.

```python
stations_selection = duckdb_conn.sql("""
    select name_long as station_name, geo_lat, geo_lng, code
    from stations
""").set_alias("stations_selection")

services_selection = (
    duckdb_conn.sql("from services")
    .aggregate("""
        station_code: "Stop:Station code",
        service_date: "Service:Date",
        service_date_format: strftime(service_date, '%d-%b (%A)'),
        num_services: count(*)
    """)
    .set_alias("services")
)
```

These relations can then be joined and further transformed:

```python
result = (
    stations_selection
    .join(
        services_selection,
        "services.station_code = stations_selection.code"
    )
    .select("""
        service_date,
        service_date_format,
        station_name,
        geo_lat,
        geo_lng,
        num_services
    """)
)
```

The relational API also supports window functions directly:

```python
top_5_query = (
    stations_query.aggregate("""
            station_name,
            service_month: monthname(service_date),
            service_month_id: month(service_date),
            num_services: sum(num_services)
        """)
    .select("""
            station_name,
            service_month,
            service_month_id,
            num_services,
            rn: row_number()
                over (
                    partition by service_month
                    order by num_services desc
                )
        """)
    .filter("rn <= 5")
    .order("service_month_id, station_name")
)
```

DuckDB's spatial extension can also be loaded for geospatial queries, demonstrating the extensibility of the Python client.
