# DELETE crashes with 'invalid node type for ART ARTScanner: 0' on index created by older DuckDB version

**Issue #21236** | State: open | Created: 2026-03-09 | Updated: 2026-03-09
**Author:** marcodelpin

### What happens?

DELETE on a table with ART indexes crashes with `INTERNAL Error: invalid node type for ART ARTScanner: 0` when the database was originally created by DuckDB v1.1.3 and is now opened by DuckDB v1.4.4.

SELECT operations work fine. Only write operations (DELETE, possibly UPDATE) on indexed columns trigger the crash.

### Root Cause

The ART index was created by DuckDB v1.1.3. When v1.4.4 reads the index for queries, it works. But when v1.4.4 attempts to modify the index during DELETE, the `ARTScanner` encounters node type `0` which is not recognized in the current `NType` enum.

### Workaround

Dropping and recreating all ART indexes on the table fixes the issue:

```sql
DROP INDEX idx_name;
CREATE INDEX idx_name ON table(column);
-- After rebuild, DELETE works correctly
```

### To Reproduce

1. Create a database with DuckDB v1.1.3 containing a table with ART indexes and >100K rows
2. Open the same database with DuckDB v1.4.4
3. Attempt to DELETE rows from the table

```sql
-- This crashes:
DELETE FROM files WHERE is_available=false AND parent_id IN (SELECT id FROM dirs WHERE disk_id=50);
```

### Error Output

```
INTERNAL Error: invalid node type for ART ARTScanner: 0
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.

Stack Trace:
[0x12bd886]
[0x12bd944]
[0x12c2ca1]
[0x1561c87]
...
```

The process terminates with SIGABRT.

### Environment

- **Database created with**: DuckDB v1.1.3 (via go-duckdb v1.8.5, `marcboeker/go-duckdb`)
- **Opened with**: DuckDB v1.4.4 (via `duckdb/duckdb-go/v2` v2.5.5, bindings v0.3.3)
- **Table**: ~79M rows, 3 ART indexes (on `parent_id`, `(parent_id, name)`, `size`)
- **OS**: Alpine Linux 3.21 (x86_64), 16GB RAM
- **Confirmed**: Same crash occurs both via Go driver and via standalone Go binary using `database/sql` directly (no HTTP layer)

### Observations

- Small DELETEs (15K-21K rows) sometimes succeed, sometimes crash — depends on which index partitions are touched
- The crash always happens during `duckdb_execute_pending` → ART scan
- SELECT with the same WHERE clause works perfectly
- After `DROP INDEX` + `CREATE INDEX`, DELETE works flawlessly on the same data
- Related to #18190 (also ART/NType issues), but this is specifically about cross-version index compatibility

### Suggested Fix

DuckDB should either:
1. Automatically upgrade ART indexes on first write after version change (transparent migration)
2. Detect old-format ART nodes gracefully and trigger an index rebuild instead of crashing
3. At minimum, raise a clear error message suggesting `DROP INDEX` + `CREATE INDEX` instead of SIGABRT

### OS:

Alpine Linux 3.21 (x86_64)

### DuckDB Version:

v1.4.4

### DuckDB Client:

Go (duckdb/duckdb-go/v2 v2.5.5)

### Hardware:

x86_64, 16GB RAM, 4 cores

## Comments

**marcodelpin:**
## Root Cause Analysis

I dug into the C++ source code to understand why this crash occurs. The root cause is a **missing `HasMetadata()` safety check** in `ARTScanner::Scan()` that was present in v1.1.3's recursive `Node::Free` but dropped in v1.4.4's iterative replacement.

### v1.1.3: Defensive `Node::Free` (safe)

In v1.1.3, `Node::Free` ([src/execution/index/art/node.cpp:51-85](https://github.com/duckdb/duckdb/blob/v1.1.3/src/execution/index/art/node.cpp#L51-L85)) had an explicit guard:

```cpp
void Node::Free(ART &art, Node &node) {
    if (!node.HasMetadata()) {
        return node.Clear();  // Gracefully handles NType(0)
    }
    auto type = node.GetType();
    // ... switch on type ...
}
```

Similarly, `Prefix::Free` ([src/execution/index/art/prefix.cpp:88-100](https://github.com/duckdb/duckdb/blob/v1.1.3/src/execution/index/art/prefix.cpp#L88-L100)) used:

```cpp
while (node.HasMetadata() && node.GetType() == PREFIX) { ... }
```

Both paths were safe against encountering nodes with metadata byte 0.

### v1.4.4: `ARTScanner` replaces recursive `Free` (unsafe)

In v1.4.4, `Node::FreeTree` ([src/execution/index/art/node.cpp:57-86](https://github.com/duckdb/duckdb/blob/v1.4.4/src/execution/index/art/node.cpp#L57-L86)) uses `ARTScanner` to iteratively traverse and free the tree. The scanner's `Scan()` loop ([src/include/duckdb/execution/index/art/art_scanner.hpp:35-78](https://github.com/duckdb/duckdb/blob/v1.4.4/src/include/duckdb/execution/index/art/art_scanner.hpp#L35-L78)) calls `entry.node.GetType()` at line 44 **without first checking `HasMetadata()`**:

```cpp
void Scan(FUNC &&handler) {
    while (!s.empty()) {
        auto &entry = s.top();
        // ...
        const auto type = entry.node.GetType();  // ← No HasMetadata() guard!
        switch (type) {
        // ...
        default:
            throw InternalException("invalid node type for ART ARTScanner: %d", type);
        }
    }
}
```

When `GetType()` is called on a node with metadata byte 0, it returns `NType(0)` which hits the `default` case and throws.

### How NType(0) nodes enter the tree

During `Node4::DeleteChild` ([src/execution/index/art/base_node.cpp:79-101](https://github.com/duckdb/duckdb/blob/v1.4.4/src/execution/index/art/base_node.cpp#L79-L101)), when a Node4 drops to 1 child, the code:

1. Calls `Node::FreeTree(art, n.children[child_pos])` on the deleted child's subtree (line 46 of `DeleteChildInternal`)
2. Frees the Node4 itself with `Node::FreeNode(art, node)` which calls `node.Clear()` — setting metadata to 0
3. Calls `Prefix::Concat(art, parent, node, child, ...)` to compress the remaining child into the parent prefix chain

The `node` reference now points to a cleared node (metadata = 0). If the child subtree being freed in step 1 contains old-format serialized data where some `Node*` pointers reference segments that haven't been fully initialized (old FixedSizeAllocator segments may contain stale data), the ARTScanner will encounter NType(0) and crash.

Additionally, `Emplace()` for `POP` handling ([art_scanner.hpp:82-91](https://github.com/duckdb/duckdb/blob/v1.4.4/src/include/duckdb/execution/index/art/art_scanner.hpp#L82-L91)) unconditionally pushes nodes to the stack without any metadata check:

```cpp
void Emplace(FUNC &&handler, NODE &node) {
    if (HANDLING == ARTScanHandling::EMPLACE) { ... }  // Only for EMPLACE mode
    s.emplace(node);  // For POP mode, pushes unconditionally — may have metadata 0
}
```

### All node iterators are safe

I verified all node iterators:
- `BaseNode::Iterator` visits exactly `count` children — safe
- `Node48::Iterator` checks `EMPTY_MARKER` — safe  
- `Node256::Iterator` checks `HasMetadata()` — safe
- `Leaf::DeprecatedFree` uses `while (next.HasMetadata())` — safe

The issue is specifically in the scanner loop itself, not the iterators.

### Suggested minimal fix

Add a `HasMetadata()` check in `ARTScanner::Scan()` before calling `GetType()`:

```cpp
// In art_scanner.hpp, Scan() method:
const auto type = entry.node.GetType();
// becomes:
if (!entry.node.HasMetadata()) {
    s.pop();
    continue;
}
const auto type = entry.node.GetType();
```

And/or in `Emplace()` for safety:

```cpp
void Emplace(FUNC &&handler, NODE &node) {
    if (!node.HasMetadata()) {
        return;  // Don't push nodes without metadata
    }
    if (HANDLING == ARTScanHandling::EMPLACE) { ... }
    s.emplace(node);
}
```

This restores the defensive behavior that v1.1.3 had in its recursive `Node::Free`.

### Reproduction notes

- The crash only occurs on ART indexes **created by v1.1.3** and **modified by v1.4.4** — pure v1.4.4 indexes work fine
- SELECT operations don't trigger the crash because they don't call `FreeTree`/`ARTScanner`
- The crash is non-deterministic for small DELETEs because it depends on which index partitions contain old-format nodes
- Workaround: `DROP INDEX` + `CREATE INDEX` rebuilds the index in v1.4.4 format

**szarnyasg:**
Hello, thanks for submitting the issue. While the extensive analysis is nice, could you please submit a reproducer script for this issue that uses DuckDB v1.1 and v1.4 to demonstrate the crash?
