---
layout: post
tags: ["Python", "CSV"]
---

# Read CSV Files 10x to 40x Faster Using pyarrow and polars

CSV (comma-separated values) files have been widely used in different areas. They can be easily exported from almost all programming languages. They can also be loaded into all text editors and many other applications. However, the main disadvantage is that CSV files are usually larger than files with other formats and it is slow to load them into memory.

Here we compare different options for reading CSV files by using the `pandas`, `polars` and `pyarrow` Python packages. We test the loading performance for CSV files each with a different data type. Based on the test results, we should be able to determine which option to use when we need reading CSV files faster.

## Creating test data
CSV files with three data types, `string`, `float`, and `datetime`, have been used to test the file reading performance. All the testing CSV files were created using the scripts in <a href="https://medium.com/@sean.lma/how-to-create-dummy-pandas-dataframes-for-testing-cf03c52878e3">my previous post</a>; each CSV file has 10 million rows and three columns with the same data type and a size of about 500 MB.

The `string` type CSV file was created with:
```py
df_str = gen_rand_df(
    nrow=10000000,
    str_cols={
        'count': 3,
        'name': ['c1', 'c2', 'c3'],
        'str_len': [10, (1,15), (1,50)],
        'str_count': [1000, 500, 100],
    },
)
df_str.to_csv(filename, index=False)
```

The `float` type CSV file was created with:
```py
df_flt = gen_rand_df(
    nrow=10000000,
    float_cols={
        'count': 3,
        'name': ['c1', 'c2', 'c3'],
        'low': [0, -100, 0],
        'high': [1, 100, 1e5],
    },
)
df_flt.to_csv(filename, index=False)
```

The `datetime` type CSV file was created with:
```py
df_dts = gen_rand_df(
    nrow=10000000,
    ts_cols={
        'count': 3,
        'name': ['c1', 'c2', 'c3'],
        'start_date': ['2020-01-01', '2021-01-01', '2022-01-01'],
        'end_date': ['2021-01-01', '2022-01-01', '2023-01-01'],
        'freq': 's',
        'random': False,
    },
)
df_dts.to_csv(filename, index=False)
```

## Reading CSV files using `pandas`
In pandas, when reading CSV files, there are three types of parsers that are available (`python`, `c`, and `pyarrow`). The parser can be set via the parameter `engine`. There are also two backend data types (backend_dtype: `numpy_nullable` and `pyarrow`) for storing the data. We will check the performance of the combinations of different parsers and backend data types.

The data types passed to the functions are a dictionary like this: `dtype = {'c1': type, 'c2': type, 'c3': type}`.
- For `string` values the type is `str`. There are also two string data types available for pyarrow (dtype_pa): `pd.ArrowDtype(pa.string())` and `string[pyarrow]` (dtype_pa_str2); the latter supports NumPy-backed nullable types.
- For `float` values the type is `float` and `float64[pyarrow]`, for `numpy_nullable` and `pyarrow` backends respectively.
- For `datatime` values the type is `datetime64[s]` and `pd.ArrowDtype(pa.timestamp('s'))`. Notice that, when using the pandas datetime data types such as `datetime64[s]`, the datetime type columns must be passed to the function separately. While using the `pyarrow` data types, all types can be passed to the function in the same format.

The following options are tested:
- c + numpy_nullable + dtype_str + astype
  ```py
  import pandas as pd
  pd.read_csv(
      file, engine='c', dtype_backend='numpy_nullable', dtype=dtype_str
  ).astype(dtype)
  ```
- c + numpy_nullable + dtype

  For `string/float`:
  ```py
  pd.read_csv(
      file, engine='c', dtype_backend='numpy_nullable', dtype=dtype
  )
  ```
  For `datetime`:
  ```py
  pd.read_csv(
      file, engine='c', dtype_backend='numpy_nullable',
      parse_dates=['c1','c2','c3'],
  )
  ```
- c + pyarrow + dtype

  For `string/float`:
  ```py
  pd.read_csv(
      file, engine='c', dtype_backend='pyarrow', dtype=dtype
  )
  ```
  For `datetime`:
  ```py
  pd.read_csv(
      file, engine='c', dtype_backend='pyarrow',
      parse_dates=['c1','c2','c3'],
  )
  ```
- c + pyarrow + dtype_pa
  ```py
  pd.read_csv(
      file, engine='c', dtype_backend='pyarrow', dtype=dtype_pa
  )
  ```
- pyarrow + numpy_nullable + dtype

  For `string/float`:
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='numpy_nullable', dtype=dtype
  )
  ```
  For `datetime`:
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='numpy_nullable',
      parse_dates=['c1','c2','c3'],
  )
  ```
- pyarrow + pyarrow + dtype
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='pyarrow', dtype=dtype
  )
  ```
- pyarrow + pyarrow + string[pyarrow]
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='pyarrow', dtype=dtype_pa_str2
  )
  ```
- pyarrow + pyarrow + dtype_pa
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='pyarrow', dtype=dtype_pa
  )
  ```
- pyarrow + pyarrow + dtype_pa + to numpy_nullable
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='pyarrow', dtype=dtype_pa
  ).convert_dtypes(dtype_backend='numpy_nullable')
  ```
- pyarrow + pyarrow
  ```py
  pd.read_csv(
      file, engine='pyarrow', dtype_backend='pyarrow'
  )
  ```

The performance results for these options are as follows:
<div class="scroll">
```text
                                                         str    float  datetime performance_order_for_float
c       + numpy_nullable + dtype_str + astype            3.93s  18.2s  18.5s    10
c       + numpy_nullable + dtype                         3.88s  3.29s  15.4s     6
c       + pyarrow        + dtype                         3.27s  3.55s  16.6s     7
c       + pyarrow        + dtype_pa                      5.17s  16.8s  53.2s     9
pyarrow + numpy_nullable + dtype                         3.50s  0.54s  1.15s     4
pyarrow + pyarrow        + dtype                         7.62s  0.50s  1.67s     3
pyarrow + pyarrow        + string[pyarrow]               4.05s  15.8s  11.1s     8
pyarrow + pyarrow        + dtype_pa                      0.39s  0.48s  0.44s     2
pyarrow + pyarrow        + dtype_pa + to numpy_nullable  2.74s  2.68s  1.64s     5
pyarrow + pyarrow                                        0.48s  0.47s  0.37s     1
```
</div>

Based on the test results, we can conclude that:
- We can get the best performance when using `pyarrow` for the parser, backend and dtype (`pyarrow + pyarrow + dtype_pa`).
- The `pyarrow + pyarrow + dtype_pa` option is about 10x, 7x, and 35x faster than the default option (`c + numpy_nullable + dtype`) for `string`, `float` and `datetime`, separately.
- Compared to the `c` parser, the `pyarrow` parser is a little faster for `string`, 6x faster for `float`, and 10-14x faster for `datetime`.
- Using the `pyarrow` backend with the `c` parser, there are no performance improvements; if also using the `pyarrow` dtype the performance is much worse.
- The `pd.ArrowDtype(pa.string())` string data type is about 10x faster than the `string[pyarrow]` string data type.
- The `pyarrow` parser can automatically determine the data types without any performance loss; this is especially useful when you do not know the data types in the CSV files.

We should understand that the `pyarrow` parser works in parallel mode while the `c` parser is not. Also converting the data from the `numpy_nullable` to `pyarrow` dtype or vice versa might be time-consuming.

## Reading CSV files using `polars`
The `polars` package is relatively new. But it becomes popular recently due to its performance both in speed with vectorized execution and memory efficiency using `arrow`. Also it is designed with a clean and concise API for handling large datasets with lazy evaluation.

The data types passed to the `polars` functions are a dictionary like this: `dtypes = {'c1': dtype, 'c2': dtype, 'c3': dtype}`.
- For `string` values the dtype is `pl.Utf8`.
- For `float` values the dtype is `pl.Float64`.
- For `datatime` values the dtype is `pl.Datetime`.

The following options are tested:
- default: without providing the dtypes parameter. Note that if some columns with `float` type have empty values, the data type will be parsed as `string` - not smart enough compared to `pyarrow.csv`.
  ```py
  import polars as pl
  pl.read_csv(file)
  ```
- eager: the default mode, any operations are executed immediately
  ```py
  pl.read_csv(file, dtypes=dtypes)
  ```
- lazy: operations are not executed until you explicitly call the `collect()` method
  ```py
  pl.scan_csv(file, dtypes=dtypes).collect()
  ```
- streaming: it processes the data in batches instead of loading everything at once, good for handling large datasets that might exceed available memory
  ```py
  pl.scan_csv(file, dtypes=dtypes).collect(streaming=True)
  ```
- sql api eager: interact with data using familiar SQL syntax
  ```py
  pl.SQLContext(
      data=pl.scan_csv(file, dtypes=dtypes)
  ).execute('select * from data', eager=True)
  ```
- sql api eager + to pandas
  ```py
  pl.SQLContext(
      data=pl.scan_csv(file, dtypes=dtypes)
  ).execute(
      'select * from data', eager=True
  ).to_pandas(use_pyarrow_extension_array=False)
  ```
- sql api eager + to pandas pyarrow
  ```py
  pl.SQLContext(
      data=pl.scan_csv(file, dtypes=dtypes)
  ).execute(
      'select * from data', eager=True
  ).to_pandas(use_pyarrow_extension_array=True)
  ```

The tested performance results are as follows:
```
                                          str    float  datetime
default                                   0.52s  0.38s  0.37s
eager                                     0.46s  0.40s  0.39s
lazy                                      0.45s  0.38s  0.41s
streaming                                 0.42s  0.40s  0.42s
sql api eager                             0.46s  0.38s  0.40s
sql api eager + to pandas                 1.59s  0.47s  0.48s
sql api eager + to pandas pyarrow         0.99s  0.43s  0.45s
```

It is obvious from the results that:
- The performance is quite consistent for all the options using `polars`.
- The `polars` CSV reading has a similar performance compared to `pandas` with `pyarrow`.
- If we need a `numpy_nullable` pandas DataFrame, `polars` can still be a better option.

## Reading CSV files using `pyarrow.csv`
The module, `pyarrow.csv`, is one of the great modules within the `pyarrow` library that specifically deals with reading and writing CSV files. It offers robust functionalities to efficiently process CSV data with some great features, such as inferring data types during reading and supporting various file formats.

Here we test the performance of the `pyarrow.csv` module with three data types in the format `convert_options = pv.ConvertOptions(column_types={'c1': dtype, 'c2': dtype, 'c3': dtype})`.
- For `string` values the dtype is `pa.string()`.
- For `float` values the dtype is `pa.float64()`.
- For `datatime` values the dtype is `pa.timestamp('s')`.

The following options are tested and compared:
- default
  ```py
  import pyarrow.csv as pv
  pv.read_csv(file)
  ```
- default + to pandas
  ```py
  pv.read_csv(file).to_pandas()
  ```
- default + to pandas pyarrow
  ```py
  pv.read_csv(file).to_pandas(types_mapper=pd.ArrowDtype)
  ```
- dtype
  ```py
  pv.read_csv(file, convert_options=convert_options)
  ```
- dtype + to pandas
  ```py
  pv.read_csv(file, convert_options=convert_options).to_pandas()
  ```
- dtype + to pandas pyarrow
  ```py
  pv.read_csv(file, convert_options=convert_options).to_pandas(types_mapper=pd.ArrowDtype)
  ```

The performance results for the previous options are shown here:
```
                               str    float  datetime
default                        0.39s  0.44s  0.38s
default + to pandas            1.07s  0.45s  0.42s
default + to pandas pyarrow    0.48s  0.43s  0.33s
dtype                          0.39s  0.40s  0.36s
dtype   + to pandas            0.99s  0.45s  0.41s
dtype   + to pandas pyarrow    0.39s  0.42s  0.37s
```

From these results we can conclude that:
- The `pyarrow.csv` module has a similar performance compared to `polars`.
- If we need to load CSV files into a `pandas` DataFrame, `pyarrow.csv` is the fastest option.

## Best options from `pandas`, `polars`, and `pyarrow`
There is no surprise that all options using `arrow` to store data have a similar performance for reading CSV files; `polars` also uses `arrow` to save the data in memory. The `arrow` package is not just faster by parallelizing the reading, it is also more memory efficient.

The `polars` package is relatively new compared to `pandas`. It has some great new features but might not have the functions we need. It's entirely up to us to decide which package to use. If we use `polars` do all our data manipulations I would suggest we stick to `polars` for reading CSV files.

If `pandas` is still our preference, to load CSV files efficiently, we should use the `pyarrow` parser, backend and dtype or `pyarrow.csv` to improve the performance further. If we also need to use the `numpy_nullable` backend, it is best to read CSV files using `pyarrow.csv` and then convert the backend to `numpy_nullable`.
