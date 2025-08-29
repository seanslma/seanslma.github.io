---
tags: ["Python", "Feature Selection"]
---

# Improve VarianceThreshold performance in ML feature selection
For Machine Learning feature selection, one of the basic and efficient methods is using feature's variance to drop features that are almost constant -- these features will not provide any useful information for the target prediction.

## scikit-learn implementation is slow
The `VarianceThreshold` class implemented in `sciki-learn` is super slow. Here is the example showing how to use it.
```py
import polars as pl
from sklearn.feature_selection import VarianceThreshold
def sklearn_variance_threshold(
    X: pl.DataFrame,
    threshold: float = 0.0,
) -> pl.DataFrame:
    selector = VarianceThreshold(threshold=0.0)
    _ = selector.fit_transform(X)
    df = X[selector.get_support()]
    return df
```

## polars implementation is much faster
The `polars` is a `pandas` equivalent data processing package that is implemented using the `Rust` language. Note that `Rust` is popular for its performance and other great features such as parallelization and memory management.

Here is the implementation using `polars` that is about 20x faster.
```py
import polars as pl
def polars_variance_threshold(
    X: pl.DataFrame,
    threshold: float = 0.0,
) -> pl.DataFrame:
    stats = X.select([
        pl.var(col).alias(col) for col in X.columns
    ])
    variances = stats.row(0)  # get variances as a list
    df = X.select([
        col for col, var in zip(X.columns, variances)
        if var > threshold
    ])
    return df
```

## Test it
To compare the performance of the two different implementations we can again use the method I created to generate dummy data for testing.
```py
import pandas as pd
import polars as pl
# create dataset
df_pandas = create_dummy_df()
df = pl.from_pandas(df_pandas)
X = df.select(pl.exclude('target'))
Y = df['target']

X_sklearn = sklearn_variance_threshold(X)
X_polars = polars_variance_threshold(X)
X_sklearn.equals(X_polars)
```
