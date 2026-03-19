# [Bug] generate_grammar.py: PR #19751 keyword sort fix has incorrect strip_p/lower() call order and misses 5 other sort sites

**Issue #21400** | State: closed | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** ZikeWang
**Labels:** under review

### What happens?

PR #19751 (commit cf3860f, merged 2025-11-13) fixed the keyword sorting bug in `generate_grammar.py` but has two remaining issues:
1. **Incorrect call order:** The fix uses `strip_p(x[0].lower())`, but `strip_p()` checks `x.endswith("_P")` (uppercase). Calling `.lower()` first turns `"YEAR_P"` into `"year_p"`, so `strip_p()` fails to strip the `_P` suffix. The correct order is `strip_p(x[0]).lower()`.
2. **Incomplete fix:** Only the `kwlist.sort()` call (1 of 6) was patched. The other 5 keyword category list sorts (`unreserved_keywords`, `colname_keywords`, `func_name_keywords`, `type_name_keywords`, `reserved_keywords`) still use uppercase sorting without `.lower()`.

### To Reproduce

The bug can be reproduced by adding any underscore-containing keyword that is alphabetically adjacent to an existing `_P`-suffixed keyword in `generate_grammar.py`.

**Step 1: Verify the call order bug with a simple Python script**

```Python
def strip_p(x):
    if x.endswith("_P"):
        return x[:-2]
    else:
        return x

# Simulate keywords that would coexist in kwlist
keywords = [("YEAR_P", "UNRESERVED"), ("YEAR_MONTH", "UNRESERVED"), ("YEARS_P", "UNRESERVED"),
            ("DAY_P", "UNRESERVED"), ("DAY_HOUR", "UNRESERVED"), ("DAYS_P", "UNRESERVED")]

# Current PR #19751 sort: strip_p(x[0].lower())
pr_sort = sorted(keywords, key=lambda x: strip_p(x[0].lower()))

# Correct sort: strip_p(x[0]).lower()
correct_sort = sorted(keywords, key=lambda x: strip_p(x[0]).lower())

print("=== PR #19751 sort order (strip_p(x[0].lower())) ===")
for kw, cat in pr_sort:
    sort_key = strip_p(kw.lower())
    name = strip_p(kw).lower()
    print(f"  {kw:15s}  sort_key={sort_key:15s}  kwlist_name={name}")

print()
print("=== Correct sort order (strip_p(x[0]).lower()) ===")
for kw, cat in correct_sort:
    sort_key = strip_p(kw).lower()
    name = strip_p(kw).lower()
    print(f"  {kw:15s}  sort_key={sort_key:15s}  kwlist_name={name}")
```

```
=== PR #19751 sort order (strip_p(x[0].lower())) ===
  DAY_HOUR         sort_key=day_hour         kwlist_name=day_hour
  DAY_P            sort_key=day_p            kwlist_name=day
  DAYS_P           sort_key=days_p           kwlist_name=days
  YEAR_MONTH       sort_key=year_month       kwlist_name=year_month
  YEAR_P           sort_key=year_p           kwlist_name=year
  YEARS_P          sort_key=years_p          kwlist_name=years

=== Correct sort order (strip_p(x[0]).lower()) ===
  DAY_P            sort_key=day              kwlist_name=day
  DAY_HOUR         sort_key=day_hour         kwlist_name=day_hour
  DAYS_P           sort_key=days             kwlist_name=days
  YEAR_P           sort_key=year             kwlist_name=year
  YEAR_MONTH       sort_key=year_month       kwlist_name=year_month
  YEARS_P          sort_key=years            kwlist_name=years
```

**Explanation:** With the PR #19751 sort, the `kwlist_name` column (which is what gets written into `kwlist.hpp`) is **not sorted**: `day` appears after `day_hour`, and `year` appears after `year_month`. Since `ScanKeywordLookup` in `src_common_keywords.cpp` uses `strcmp`-based binary search on these names, it would fail to find `"day"` and `"year"`.

**Step 2: Verify the root cause — `strip_p()` cannot recognize lowercase `_p`**

```Python
def strip_p(x):
    if x.endswith("_P"):
        return x[:-2]
    else:
        return x

# PR #19751: .lower() before strip_p()
print(strip_p("YEAR_P".lower()))   # "year_p" — _P not stripped!

# Correct: strip_p() before .lower()
print(strip_p("YEAR_P").lower())   # "year"   — correct
```

```
year_p
year
```

**Step 3: The 5 unpatched sort sites**

In the current `main` branch of `generate_grammar.py`, lines ~74-78 still use uppercase sorting:

```Python
unreserved_keywords.sort(key=lambda x: strip_p(x))
colname_keywords.sort(key=lambda x: strip_p(x))
func_name_keywords.sort(key=lambda x: strip_p(x))
type_name_keywords.sort(key=lambda x: strip_p(x))
reserved_keywords.sort(key=lambda x: strip_p(x))
```

These should also use `.lower()` for consistency with the `kwlist` sort and with the runtime behavior of `ScanKeywordLookup`.

**Note:** This bug does not manifest in the current DuckDB codebase because no existing underscore-containing keyword happens to be alphabetically adjacent to a `_P`-suffixed keyword in a way that causes an ordering conflict. However, it will be triggered by any future keyword addition that creates such adjacency (e.g., `DAY_HOUR` near `DAY_P`, `YEAR_MONTH` near `YEAR_P`).

### OS:

Any (this is a platform-independent bug in the Python script generate_grammar.py)

### DuckDB Version:

main (the bug is in scripts/generate_grammar.py, not version-specific)

### DuckDB Client:

N/A (this is a build script bug in scripts/generate_grammar.py, not a runtime client issue)

### Hardware:

_No response_

### Full Name:

Zike Wang

### Affiliation:

Tencent

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**ZikeWang:**
**Proposed Fix**

**1. Bug fix (required):** Swap the call order in the kwlist sort:

```diff
  # sorting uppercase is different from lowercase: A-Z < _ < a-z
- kwlist.sort(key=lambda x: strip_p(x[0].lower()))
+ kwlist.sort(key=lambda x: strip_p(x[0]).lower())

```

`strip_p()` checks `x.endswith("_P")` (uppercase), so calling `.lower()` first makes it unable to strip the `_P` suffix. This causes the sort key and the written name (`strip_p(tpl[0]).lower()`) to use different logic, producing an unsorted `kwlist.hpp` that breaks `ScanKeywordLookup`'s `strcmp`-based binary search.

**2. Consistency improvement (optional):** Add `.lower()` to the 5 category list sorts:

```diff
- unreserved_keywords.sort(key=lambda x: strip_p(x))
- colname_keywords.sort(key=lambda x: strip_p(x))
- func_name_keywords.sort(key=lambda x: strip_p(x))
- type_name_keywords.sort(key=lambda x: strip_p(x))
- reserved_keywords.sort(key=lambda x: strip_p(x))
+ unreserved_keywords.sort(key=lambda x: strip_p(x).lower())
+ colname_keywords.sort(key=lambda x: strip_p(x).lower())
+ func_name_keywords.sort(key=lambda x: strip_p(x).lower())
+ type_name_keywords.sort(key=lambda x: strip_p(x).lower())
+ reserved_keywords.sort(key=lambda x: strip_p(x).lower())
```

These 5 sorts are only used for `gram.y` production rules and `%token` declarations — ordering doesn't affect functionality. However, adding `.lower()` makes the sort rule consistent: uppercase ASCII sorts `_` between `Z` and `a` (`S(83) < _(95)`), while lowercase sorts `_` before any letter (`_(95) < s(115)`), so `YEARS < YEAR_MONTH` in uppercase but `year_month < years` in lowercase.

I'm happy to submit a PR if this approach looks good.

**Mytherin:**
Thanks for the analysis - feel free to submit a PR.

**ZikeWang:**
> Thanks for the analysis - feel free to submit a PR.

Thanks! PR submitted: #21423
