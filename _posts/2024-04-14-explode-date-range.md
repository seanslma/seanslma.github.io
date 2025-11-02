---
layout: post
tags: ["Python", "Pandas"]
---

# Explode date ranges in a pandas DataFrame 30x faster

During data analysis, it is very common that we need to convert our data to the interval resolution from a lower time resolution such as quarterly or monthly to half hourly data.

We can do the conversion easily in Python using pandas. However, we know that the pandas `df.explode` function is very slow. Here I will show how we can make this process **30x** faster without using another Python package.

## Pandas DataFrame for testing
For testing the code performance, I used the `gen_rand_df` function in <a href="https://medium.com/@sean.lma/how-to-create-dummy-pandas-dataframes-for-testing-cf03c52878e3">my previous post</a> to create a dummy pandas DataFrame:
```py
df = gen_rand_df(
    nrow=100,
    str_cols={
        'count': 2,
        'name': ['id', 'category'],
        'str_len': [8, (5,20)],
        'str_count': [100, 30],
    },
    ts_cols={
        'count': 2,
        'name': ['start_date', 'end_date'],
        'start_date': ['2020-01-01', '2023-01-01'],
        'end_date': ['2023-01-01', '2025-01-01'],
        'freq': 'MS',
        'random': True,
    },
    float_cols={
        'count': 2,
        'low': 0.0,
        'high': 100.0,
        'missing_pct': 0.1,
    },
)
```
Here are the first two rows of the 100 rows of the created DataFrame:
```
         id    category start_date   end_date        f1         f2
0  8v5KSoKX       jIMki 2020-01-01 2023-07-01  35.20661  76.041564
1  ihXEKLSb  bws6TOEr06 2020-05-01 2023-02-01       NaN  26.725758
```

## Initial solution from ChatGPT and Google Gemini
We need to explode the date range (from start_date to end_date) of each row in the DataFrame to half hourly and keep all other columns.

To do that, I got solutions from ChatGPT and Google Gemini after a few iterations (they are basically the same):
```py
df['ts'] = df.apply(lambda row:
    pd.date_range(row['start_date'], row['end_date'], freq='30min'), axis=1
)
df = df.explode('ts')
```
And the first two rows of the result DataFrame are:
```
         id category start_date   end_date        f1         f2                  ts
0  8v5KSoKX    jIMki 2020-01-01 2023-07-01  35.20661  76.041564 2020-01-01 00:00:00
0  8v5KSoKX    jIMki 2020-01-01 2023-07-01  35.20661  76.041564 2020-01-01 00:30:00
```

The solution works but it is very slow. The time for creating the `ts` column is `703 ms ± 6.57 ms` and exploding is `691 ms ± 7.47 ms`, for a DataFrame with only 100 rows.

I tried different prompts to get a faster solution from the AI applications but failed; the solution either is wrong or has errors. My suggestion would be that only use the AI applications to give you some ideas or a draft solution. The best solution can only be created by a person with some knowledge in that domain.

## Using a `for-loop` instead of the `df.apply` function
We know that the `df.apply` is slow so I will replace it by a `for-loop`.
There are a couple of ways to iterate over the DataFrame rows. Let us check them:
```py
# 351 µs ± 57.8 µs
for (_, row) in df.iterrows(): pass
# 271 µs ± 65.7 µs
for row in df.to_records(index=False): pass
# 26.5 µs ± 12.9 µs
for start, end in zip(df['start_date'], df['end_date']): pass
# 10.4 µs ± 2.55 µs
for start, end in zip(df['start_date'].values, df['end_date'].values): pass
```
The last version is **34x** faster than `df.iterrows()`. The improvement will be even larger for a DataFrame with many more rows.


The improved version for creating the `ts` column is:
```py
df['ts'] = [
    pd.date_range(start, end, freq='30min')
    for start, end in zip(df['start_date'].values, df['end_date'].values)
]
```
Now the time for the improved version is `684 ms ± 12.6 ms`; it is still too slow.

## Implementing a custom `df.explode` function
Seems there is not much we can do for creating the `ts` column much faster.

Now let us be focusing on the `df.explode` part. We will implement our own version for exploding the lists in the `ts` column.

We know that the `df.reindex` function can be used to resample rows of a DataFrame based on provided new index. Here we will use this function to implement a new `explode` function.

First we can create the new index and `ts` column, using `pd.concat` to merge the DataFrames created from each row:
```py
d = (
    df
    .get(['ts'])
    .reset_index(drop=True)
    .rename_axis('i', axis=0)
    .reset_index()
)
dt = pd.concat([
    pd.DataFrame({'i': i, 'ts': ts})
    for (i, ts) in zip(d['i'].values, d['ts'].values)
]).set_index('i').rename_axis(None, axis=0)
```

Then we use the `df.reindex` function to sample the other columns in the original DataFrame and add the exploded `ts` column:
```py
df = df.drop(columns='ts').reindex(dt.index)
df['ts'] = dt.ts
```

Putting the two parts together, here is the custom `explode` function:
```py
def explode_df_column(df):
    dt = pd.concat([
        pd.DataFrame({'i': i, 'ts': ts})
        for (i, ts) in enumerate(df['ts'].values)
    ]).set_index('i').rename_axis(None, axis=0)
    df = df.drop(columns='ts').reindex(dt.index)
    df['ts'] = dt.ts
    return df
```

The time for this function is `22 ms ± 285 µs`, **30x** faster compared to the `df.explode` function that has a time of `691 ms ± 7.47 ms`.

## Creating a `ts` column with value of lists not required
For our use case, creating a intermediate column with a list of timestamps for each value is not required. We can merge this step into the step for creating the `dt` DataFrame.

Here is the final solution based on this idea:
```py
# Create a DataFrame with new index and the 30min ts column
dt = pd.concat([
    pd.DataFrame({'i': i, 'ts': pd.date_range(start, end, freq='30min')})
    for i, (start, end) in enumerate(zip(df['start_date'], df['end_date']))
]).set_index('i').rename_axis(None, axis=0)

# Resample original df based on new index and add the exploded ts column
df = df.reindex(dt.index).assign(ts=dt.ts)
```

Great! The time for this solution is `49.8 ms ± 932 µs`, about **30x** faster than the initial solution that has a time of `1.394s` (`703 ms ± 6.57 ms` + `691 ms ± 7.47 ms`).

We can wrap the method into a function and add other parameters used for limiting the min/max datetime and keeping the original DataFrame index or not. It is up to you to do the remaining work.

In summary, we improved a method **30x** faster, used to explode datetime ranges in a DataFrame to a new timestamp column and copy other columns. At the same time, we created a new function that is also about **30x** faster than the pandas `df.explode` function.

## Polars version
What about using polars, is it faster?

This link might be helpful:
https://stackoverflow.com/questions/73161185/repeating-a-date-in-polars-and-exploding-it
