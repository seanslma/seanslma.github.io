---
layout: post
tags: ["Python", "Pandas"]
---

# Reduce a python app run time from two hours to 20 seconds
Pandas `df.groupby.apply` is too slow for two Dataframes.

We have a Python app that was too slow. It took about two hours to extract product forecast data from a database and to merge it with actual records. After some refactorization and optimization, I managed to reduce the run time to less than 20 seconds.

Assume we have some products and each has some daily sales revenue, the actual records. We also have daily forecast revenue. The task is to merge the actual and forecast data together.

Once there are missing records in the actual data, we believe that the actual revenue from that day are not reliable and they should be replaced with forecast data.

To finish this task, for each product, we need to first find the last consecutive date in the actual data and then get the forecast data after that date so we can merge the actual and forecast data together.

## Dummy data for testing
The performance of different implementations has been tested using some dummy data. I created dummy data using a function `gen_rand_df` that is described in [my previous post](https://medium.com/@sean.lma/how-to-create-dummy-pandas-dataframes-for-testing-cf03c52878e3). I also used a function `explode_date_range` in [my another post](https://python.plainenglish.io/how-to-explode-date-ranges-in-a-pandas-dataframe-30x-faster-cb76519c7acf) to explode date ranges.

Firstly, we create some product info with `product_id`, `start_date` and `end_date` for the actual sales records and expand the date ranges to daily records.
```py
nrow = 5000
d1 = gen_rand_df(
    nrow=nrow,
    str_cols={
        'count': 1,
        'name': 'product_id',
        'str_len': 10,
        'str_cnt': nrow,
    },
    ts_cols={
        'count': 2,
        'name': ['start_date', 'end_date'],
        'start_date': '2025-01-01',
        'end_date': '2035-01-01',
        'freq': 'D',
        'random': True,
    },
)
df1 = explode_date_range(
    df=d1.query('start_date < end_date').drop_duplicates(subset=['product_id']),
    start_date_col='start_date',
    end_date_col='end_date',
    freq='D',
)
```

Secondly, we create some sales forecast info for products that has actual sales data.
```py
d2 = gen_rand_df(
    nrow=nrow,
    str_cols={
        'count': 1,
        'name': 'product_id',
        'col_strs': d1['product_id'].unique(),
    },
    ts_cols={
        'count': 2,
        'name': ['start_date', 'end_date'],
        'start_date': '2025-01-01',
        'end_date': '2035-01-01',
        'freq': 'D',
        'random': True,
    },
)
df2 = explode_date_range(
    df=d2.query('start_date < end_date').drop_duplicates(subset=['product_id']),
    start_date_col='start_date',
    end_date_col='end_date',
    freq='D',
)
```

Then, we create some dummy product sales revenue for both the actual and forecast records.
```py
d3 = gen_rand_df(
    nrow=max(df1.shape[0], df2.shape[0]),
    float_cols={
        'count': 2,
        'name': ['daily_revenue1', 'daily_revenue2'],
        'low': 0,
        'high': 1e3,
        'missing_pct': [0.1, 0],
    },
)
```

Finally, we add the sales revenue to the actual and forecast data.
```py
df_actual = (
    df1
    .assign(daily_revenue=d3['daily_revenue1'].values[:df1.shape[0]])
    .set_index(['product_id', 'daily_revenue'])
)
df_forecast = (
    df2
    .assign(daily_revenue=d3['daily_revenue2'].values[:df2.shape[0]])
    .set_index(['product_id', 'daily_revenue'])
)
```

Here are the first few lines of the actual sales data:
```
                      daily_revenue
product_id date
P3hLcLj43u 2025-01-26    128.570203
           2025-01-27    499.277862
           2025-01-28    601.498358
```

## Getting last consecutive date
The function used to get the last consecutive date from a date series has been implemented as follows:
```py
def get_last_consecutive_date(dates: pd.Series) -> np.datetime64 | None:
    # Empty input
    if dates.empty:
        return None

    dates = np.unique(dates)

    # Only one unique element in the list
    if len(dates) == 1:
        return dates[0]

    diffs = np.diff(dates).astype('timedelta64[D]').astype(int)
    last_consecutive_day_index = np.where(diffs > 1)[0]
    if len(last_consecutive_day_index) == 0:
        return dates[-1] # all dates are consecutive
    else:
        return dates[last_consecutive_day_index[0]]
```

## Using Pandas `df.groupby.apply`
As we have to perform the same task for each group of products, naturally we can use Pandas `df.groupby.apply`. But this function generally only works for one DataFrame. Here we have two DataFrames and one option is passing the second DataFrame as a parameter.

Here is the implementation:
```py
def keep_records_after_consecutive_dates_v1(
    df_forecast: pd.DataFrame,
    df_actual: pd.DataFrame,
) -> pd.DataFrame:
    product_id = df_forecast.index.values[0][df_forecast.index.names.index('product_id')]
    dates = df_actual.query('product_id == @product_id & daily_revenue.notna()').index.unique('date')
    # Get last consecutive date and filter df_forecast
    if len(dates) > 0:
        last_consecutive_date = get_last_consecutive_date(dates)
        df_forecast = df_forecast.query('date > @last_consecutive_date')
    return df_forecast

df_v1 = (
    df_forecast
    .groupby('product_id', group_keys=False)
    .apply(keep_records_after_consecutive_dates_v1, df_actual)
)
```
The run time is **327 seconds**.

## Avoiding repeated query and filtering
By checking the previous implementation, we can observe that we have a repeated query and filtering for each product on the actual sales DataFrame. That is likely to slow down the process.

Now we do the query for all products and group the product records in advance. Hopefully this will make it much faster.

Here is the updated version:
```py
def keep_records_after_consecutive_dates_v2(
    df_forecast: pd.DataFrame,
    df_actual: DataFrameGroupBy,
) -> pd.DataFrame:
    product_id = df_forecast.index.values[0][df_forecast.index.names.index('product_id')]
    if product_id in df_actual.groups:
        dates = df_actual.get_group(product_id).index.unique('date')
        # Get last consecutive date and filter df_forecast
        if len(dates) > 0:
            last_consecutive_date = get_last_consecutive_datex(dates)
            df_forecast = df_forecast.query('date > @last_consecutive_date')
    return df_forecast

grp_actual = df_actual.query('daily_revenue.notna()').groupby('product_id')
df_v2 = (
    df_forecast
    .groupby('product_id', group_keys=False)
    .apply(keep_records_after_consecutive_dates_v2, grp_actual)
)
```
Now the run time is **17.6 seconds** --- that's about **18x** faster.

## Using a Python for-loop
The `.apply()` often has some overhead compared to a pure Python for-loop. We now replace the `.apply()` with a for-loop. At the same time we can remove the index parsing for all product groups.
```py
def keep_records_after_consecutive_dates_v3(
    df_forecast: pd.DataFrame,
    df_actual: pd.DataFrame,
) -> pd.DataFrame:
    dates = df_actual.index.unique('date')
    # Get last consecutive date and filter df_forecast
    if len(dates) > 0:
        last_consecutive_date = get_last_consecutive_datex(dates)
        df_forecast = df_forecast.query('date > @last_consecutive_date')
    return df_forecast

dfs = []
grp_actual = df_actual.query('daily_revenue.notna()').groupby('product_id')
grp_forecast = df_forecast.groupby('product_id')
product_ids = df_forecast.index.unique('product_id')
for product_id in product_ids:
    if product_id in grp_actual.groups:
        df = keep_records_after_consecutive_dates_v3(
            grp_forecast.get_group(product_id),
            grp_actual.get_group(product_id),
        )
    else:
        df = grp_forecast.get_group(product_id)
    dfs.append(df)
df_v3 = pd.concat(dfs, axis=0)
```
The run time is **9.8 seconds** --- that's about **1.8x** faster than version #2.

## Vectorized process without for-loop
It's obvious that we can vectorize the calculation of the last consecutive date for all products. Pandas `groupby().apply()` on a Series can be very efficient, as it often operates on NumPy arrays internally.

We can also avoid the for-loop by using vectorized join and filtering operations. By doing that we don't need to join small DataFrames for all products using `pd.concat`.

The final optimized version is showing as follows:
```py
def keep_records_after_consecutive_dates_v4(
    df_forecast: pd.DataFrame,
    df_actual: pd.DataFrame,
) -> pd.DataFrame:
    # Get last consecutive date for each product
    last_consecutive_dates = (
        df_actual
        .query('daily_revenue.notna()')
        .reset_index('date')
        .groupby('product_id')['date']
        .apply(get_last_consecutive_date)
        .to_frame()
        .rename(columns={'date': 'last_consecutive_date'})
    )
    # Filter df_forecast
    df_forecast = (
        df_forecast
        .join(last_consecutive_dates, on='product_id', how='left')
        .fillna({'last_consecutive_date': pd.Timestamp.min})
        .query('date > last_consecutive_date')
        .drop(columns='last_consecutive_date')
    )
    return df_forecast

df_v4 = keep_records_after_consecutive_dates_v4(df_forecast, df_actual)
```
The final run time is **2.4 seconds** - that's about **4x** faster than version #3 and about **130x** faster than the original version #1 (**327 seconds**).

## summary
By avoiding repeated query and filtering operations and vectorization of some other operations, I successfully made a Python process running 130x faster. I also did some similar optimization for extracting forecast data from a database. Ultimately the application total execution time was reduced from over two hours to less than 20 seconds.
