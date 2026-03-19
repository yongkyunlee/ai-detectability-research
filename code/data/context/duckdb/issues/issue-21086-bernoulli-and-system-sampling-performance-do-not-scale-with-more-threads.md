# Bernoulli and system sampling performance do not scale with more threads

**Issue #21086** | State: closed | Created: 2026-02-25 | Updated: 2026-03-04
**Author:** thalassemia
**Labels:** reproduced

### What happens?

The `RESERVOIR` sampling method appears to be the only one whose performance scales with more threads. The `BERNOULLI` and `SYSTEM` sampling methods take the same amount of time to run regardless of how many threads they are given. I first noticed this issue running on an aarch64 EC2 instance reading data stored on S3. I then created the reproducer below and confirmed my findings on my Mac.

### To Reproduce

```python
import os
import shutil
import time

import duckdb
import numpy as np
import polars as pl

def generate_test_data(output_dir: str = "sampling_reprex_data"):
    """Generate small hive-partitioned test dataset."""
    print("Generating test data...")
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    rng = np.random.default_rng(42)
    
    # Create 500 partitions with 200K rows each = 100M rows total
    for partition in range(500):
        data = {
            'id': np.arange(200_000),
            'value': rng.random(200_000),
            'category': rng.integers(0, 100, 200_000),
        }
        
        df = pl.DataFrame(data)
        partition_path = os.path.join(output_dir, f"partition={partition}")
        os.makedirs(partition_path, exist_ok=True)
        df.write_parquet(os.path.join(partition_path, "data.parquet"))
    
    print("Generated 100M rows across 500 partitions\n")

def benchmark_sampling(data_path: str, method: str, threads: int, runs: int = 3) -> np.floating:
    """Benchmark a single sampling method with specified thread count."""
    conn = duckdb.connect()
    conn.execute(f"SET threads = {threads}")
    
    query = f"""
    SELECT * FROM read_parquet(
        '{data_path}/**/*.parquet',
        hive_partitioning = true
    ) USING SAMPLE {method}(1 PERCENT)
    """
    
    # Warmup
    conn.sql(query).fetchall()
    
    # Benchmark
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        conn.sql(query).fetchall()
        times.append(time.perf_counter() - start)
    
    conn.close()
    return np.mean(times)

def main():
    """Run minimal reproducible example."""
    data_path = "sampling_reprex_data"
    
    # Generate test data
    generate_test_data(data_path)
    
    print("=" * 70)
    print("DuckDB Sampling Thread Scaling Comparison")
    print("=" * 70)
    print("Dataset: 100M rows, 1% sample, mean of 3 runs\n")
    
    methods = ['BERNOULLI', 'SYSTEM', 'RESERVOIR']
    thread_counts = [1, 2, 4, 8]
    
    # Collect results
    results = {}
    for method in methods:
        results[method] = {}
        for threads in thread_counts:
            elapsed = benchmark_sampling(data_path, method, threads)
            results[method][threads] = elapsed
            print(f"{method:12s} {threads} thread(s): {elapsed:.3f}s")
        print()
    
    # Show speedup analysis
    print("=" * 70)
    print("Speedup Analysis (relative to 1 thread)")
    print("=" * 70)
    
    for method in methods:
        baseline = results[method][1]
        print(f"\n{method}:")
        for threads in thread_counts:
            speedup = baseline / results[method][threads]
            efficiency = (speedup / threads) * 100
            print(f"  {threads} threads: {speedup:.2f}x speedup ({efficiency:.0f}% efficiency)")
    
    # Cleanup
    print(f"\nCleaning up {data_path}...")
    shutil.rmtree(data_path)

if __name__ == "__main__":
    main()
```

### OS:

macOS 26.3, aarch64

### DuckDB Version:

1.4.4

### DuckDB Client:

Python

### Hardware:

M4, 16GB RAM

### Full Name:

Sean Cheah

### Affiliation:

Stanford University

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**wordhardqi:**
```
PhysicalOperator &PhysicalPlanGenerator::CreatePlan(LogicalSample &op) {
	D_ASSERT(op.children.size() == 1);

	auto &plan = CreatePlan(*op.children[0]);
	if (!op.sample_options->seed.IsValid()) {
		auto &random_engine = RandomEngine::Get(context);
		op.sample_options->SetSeed(random_engine.NextRandomInteger());
	}

``` 
will set the seed and in physical_streaming_sample.cpp, the ParallelOperation() will always return `false` since isValid is true and repeatable is false. 
```

bool PhysicalStreamingSample::ParallelOperator() const {
	return !(sample_options->repeatable || sample_options->seed.IsValid());
}

```

**thalassemia:**
Thanks for the comment @wordhardqi ! I already implemented the fix in my fork (see the commit above your comment). Just waiting for CI to complete before making the PR.
