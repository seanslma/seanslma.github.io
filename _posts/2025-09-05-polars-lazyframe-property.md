---
tags: ["Python", "Polars"]
---

# Polars LazyFrame properties are expensive operations

When using polars LazyFrame, at some point you might need to get the properties such as the column names of the LazyFrame. 
We must be aware that getting LazyFrame properties is expensive. For more details check the discussions here: https://github.com/pola-rs/polars/issues/16328

Here is a list of the some properties for the LazyFrame:
- LazyFrame.columns
- LazyFrame.dtypes
- LazyFrame.schema
- LazyFrame.width

For example when you using `LaztFrame.columns` you will get a warning:
```
PerformanceWarning: Determining the column names of a LazyFrame requires resolving its schema, which is a potentially expensive operation. Use `LazyFrame.collect_schema().names()` to get the column names without this warning.
  d.lazy().columns
```
However, if you take the suggestion of the warning by using the alternative method you will only avoid the warning but nothing else -- the alternative operation is still expensive.

Let's test it by code example:
```py
import polars as pl
d = {f'v{i}':[i] for i in range(10000)}
dxx = pl.DataFrame(d)
dyy = dxx.lazy()

_ = df.columns                  # 1.39 ms ± 45 μs without warning
_ = lf.columns                  # 25.3 ms ± 822 μs with warning
_ = lf.collect_schema().names() # 24.5 ms ± 765 μs without warning
```
So if possible we should get the properties from the DataFrame not the Lazyframe.
