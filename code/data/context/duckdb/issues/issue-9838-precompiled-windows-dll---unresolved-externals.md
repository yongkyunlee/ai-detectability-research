# Precompiled Windows DLL - Unresolved externals

**Issue #9838** | State: closed | Created: 2023-11-28 | Updated: 2026-03-06
**Author:** lkordos
**Labels:** under review, stale

### What happens?

I downloaded duckdb.dll v0.9.2 for Windows, duckdb.hpp and duckdb.h
I was using it successfully with parquet data files and CSV files.

However, when I try to parse the  MaterializedQueryResult to work with data, I get linking error unresolved externals:

duckdb::MaterializedQueryResult::Collection
duckdb::ColumnDataRow::GetValue

I tried to include the column_data_collection.hpp, but that resulted to "...already defined ..." error.

Am I missing something or are Collection and GetValue function implementations missing?


### To Reproduce
```
std::string result;
std::unique_ptr res = con->Query("SELECT col1 FROM MyTable);
duckdb::ColumnDataCollection& coll = res->Collection();
         for (auto& row : coll.Rows()) {
            for (idx_t col_idx = 0; col_idx  0) {
                  result += "\t";
               }
               auto val = row.GetValue(col_idx);
               result += val.IsNull() ? "NULL" : duckdb::StringUtil::Replace(val.ToString(), std::string("\0", 1), "\\0");
            }
            result += "\n";
         }
```
### OS:

Windows 11

### DuckDB Version:

0.9.2

### DuckDB Client:

C++

### Full Name:

Lubomir Kordos

### Affiliation:

Lukosoft Canada

### Have you tried this on the latest `main` branch?

I have tested with a release build (and could not test with a main build)

### Have you tried the steps to reproduce? Do they include all relevant data and configuration? Does the issue you report still appear there?

- [X] Yes, I have

## Comments

**Tishj:**
Please post the full compilation error, to provide proper context.

Likely what's wrong here is DUCKDB_API missing in one or more places for the definitions of the classes/methods

**lkordos:**
Full error description:
```
Creating library ..\..\..\bin\win22\debug\test.lib and object ..\..\..\bin\win22\debug\test.exp
1>analyzer.obj : error LNK2019: unresolved external symbol "public: class duckdb::Value __cdecl duckdb::ColumnDataRow::GetValue(unsigned __int64)const " (?GetValue@ColumnDataRow@duckdb@@QEBA?AVValue@2@_K@Z) referenced in function "public: enum result_code __cdecl Analyzer::MapGenes(class std::basic_string,class std::allocator > const &,class std::basic_string,class std::allocator > const &,class std::basic_string,class std::allocator > &)" (?MapGenes@Analyzer@@QEAA?AW4result_code@@AEBV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@0AEAV34@@Z)
1>analyzer.obj : error LNK2019: unresolved external symbol "public: class duckdb::ColumnDataCollection & __cdecl duckdb::MaterializedQueryResult::Collection(void)" (?Collection@MaterializedQueryResult@duckdb@@QEAAAEAVColumnDataCollection@2@XZ) referenced in function "public: enum result_code __cdecl Analyzer::MapGenes(class std::basic_string,class std::allocator > const &,class std::basic_string,class std::allocator > const &,class std::basic_string,class std::allocator > &)" (?MapGenes@Analyzer@@QEAA?AW4result_code@@AEBV?$basic_string@DU?$char_traits@D@std@@V?$allocator@D@2@@std@@0AEAV34@@Z)
1>..\..\..\bin\win22\debug\test.exe : fatal error LNK1120: 2 unresolved externals
1>Done building project "test_console.vcxproj" -- FAILED.
```

**lkordos:**
Hello, I'd like to ask about this issue: has been made any resolution in this case? Thank you.

**github-actions[bot]:**
This issue is stale because it has been open 90 days with no activity. Remove stale label or comment or this will be closed in 30 days.

**github-actions[bot]:**
This issue was closed because it has been stale for 30 days with no activity.

**rfx77:**
Same Problem here. I use the latest vcpkg version of duckdb with msvc fron Visual Studio 2026

Same code and same linker error.
