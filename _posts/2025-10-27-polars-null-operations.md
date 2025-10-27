---
layout: post
tags: ["Python", "Polars"]
---

# Polars null operations
In Polars, if any of the columns involved in an operation contains `null`, the result of the operation will also be `null` for that row. This behavior is consistent with SQL's `NULL propagation` principle.

Let's create a simple example to demonstrate that:
```py
import polars as pl

# Create a DataFrame with some null values
df = pl.DataFrame({
    'x': [None, 'a', 'b'],  # 'None' represents null in Polars
    'y': ['foo', 'bar', None]
})

# Apply the expression to concatenate 'x' + '_' + 'y'
df_result = df.with_columns(
    (pl.col('x') + pl.lit('_') + pl.col('y')).alias('v')
)

# Show the result
print(df_result)
```

The output is:
```
shape: (3, 3)
┌──────┬──────┬───────┐
│ x    ┆ y    ┆ v     │
│ ---  ┆ ---  ┆ ---   │
│ str  ┆ str  ┆ str   │
╞══════╪══════╪═══════╡
│ null ┆ foo  ┆ null  │
│ a    ┆ bar  ┆ a_bar │
│ b    ┆ null ┆ null  │
└──────┴──────┴───────┘
```

And here is the simple fix -- fill null with and empty string first:
```py
# Apply the expression to concatenate 'x' + '_' + 'y'
df_result = df.with_columns(
    (
      pl.col('x').fill_null('')
      + pl.lit('_')
      + pl.col('y').fill_null('')
    ).alias('v'),
)
```

Now the output is correct:
```py
shape: (3, 3)
┌──────┬──────┬───────┐
│ x    ┆ y    ┆ v     │
│ ---  ┆ ---  ┆ ---   │
│ str  ┆ str  ┆ str   │
╞══════╪══════╪═══════╡
│ null ┆ foo  ┆ _foo  │
│ a    ┆ bar  ┆ a_bar │
│ b    ┆ null ┆ b_    │
└──────┴──────┴───────┘
```
