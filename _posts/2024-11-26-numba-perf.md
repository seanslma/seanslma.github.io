---
layout: post
tags: ["Python", "Numba"]
---

# Make python loops 5x to 10x faster using numba

Numba is a just-in-time (JIT) compiler for python that translates python code into highly optimized machine code at runtime. It can significantly improve the performance of numerical computations by enabling high-performance execution of functions, particularly those that make heavy use of numpy arrays.

Here we will first briefly explain key features of numba and when to use it, and then provide an example demonstrating how to accelerate code performance by leveraging various numba features. If you are already familiar with numba, go directly to the third section about the demonstration.

## Key features of numba
- **JIT compilation**: Numba compiles python functions into machine code, allowing for efficient code generation tailored to specific hardware and data types.
- **Numerical acceleration**: Numba is particularly well-suited for numerical computations involving arrays and mathematical operations. It can often achieve performance comparable to compiled languages like C or Fortran.
- **Compatibility with numpy**: Numba seamlessly integrates with numpy, to accelerate numpy functions and operations, making them much faster.
- **Parallel computing**: Numba supports parallel execution on multi-core CPUs and GPUs, enabling us to leverage the power of parallel hardware to speed up computations.
- **Custom UDFs**: We can create custom user-defined functions (UDFs) in numba and use them within our python code. These UDFs can be compiled and optimized for performance.

## When to use and to avoid numba
Numba is particularly well-suited for numerical computations involving arrays and mathematical operations. Here are some specific cases where we should consider using numba:
- **Array operations**: If our code heavily involves operations on numpy arrays, such as element-wise arithmetic, matrix multiplication, or reductions, numba can significantly accelerate these computations.
- **Mathematical functions**: Numba can optimize calls to mathematical functions like `sin`, `cos`, `exp`, and `log`, providing a performance boost compared to their python counterparts.
- **Custom functions**: If we have custom functions that perform numerical calculations, numba can compile them into machine code for improved efficiency.
- **Loops**: Numba can often optimize loops that iterate over arrays or perform numerical calculations within the loop body.

However, not all python code can be optimized using numba and thus improve the performance. There are some limitations to consider before using numba:
- **I/O bound operations**: Numba will not help much with operations that are I/O bound, such as reading/writing files or network operations.
- **Dynamic python features**: If our code relies heavily on python's dynamic features (like modifying functions at runtime), numba may not be suitable, as it works best with statically typed, straightforward code.
- **Non-numerical code**: For code that does not involve numerical calculations or array manipulations, other optimization techniques may be more appropriate.
- **Numba can introduce overhead**: If we are working with small datasets or functions that run very quickly, the overhead of JIT compilation might outweigh the performance benefits.

To determine whether numba is appropriate for our use case, we can:
- **Profile our code:** Use profiling tools to identify the bottlenecks in our code and see if they involve numerical computations.
- **Try numba and measure the performance:** Experiment with numba and compare the performance of our code with and without numba.
- **Consider the trade-offs:** Weigh the potential performance benefits against the overhead and limitations of using numba.

Overall, if we have numerical or scientific computations that need to be optimized, numba is a powerful tool that can lead to significant performance improvements with minimal code changes.

## Data for testing demonstration
Let's create a 2D numpy array filled with randomly generated data. Each row represents a scenario and here we will calculate the distance between any two scenarios.
```py
import numpy as np
np.random.seed(11)
arr = np.random.rand(100, 1000)
```

## Initial version
We calculate the distance between two scenarios using the 1-norm, which measures the sum of the absolute differences between corresponding elements.
```py
def calculate_distances1(arr):
    m = arr.shape[0]
    n = arr.shape[1]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            v = 0.0
            for k in range(n):
                 v += abs(arr[i, k] - arr[j, k])
            dist_arr[i, j] = v
            dist_arr[j, i] = v
    return dist_arr
# 2.68 s ± 16.8 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
```
The run time is about 2.68 seconds, for 100 scenarios. If we have 1000 scenarios the time would be 268 seconds. That is too slow and we must improve the performance.

## Using numpy function
Here we update the code to calculate the 1-norm using the numpy function `np.linalg.norm()`.
```py
def calculate_distances2(arr):
    m = arr.shape[0]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            dist_arr[i, j] = np.linalg.norm(arr[i] - arr[j], 1)
            dist_arr[j, i] = dist_arr[i, j]
    return dist_arr
# 40.7 ms ± 1.50 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)
```
Now the run time is 40.7 ms - about `65x` faster! As the numpy function is implemented in C, there is no surprise that the performance has been improved significantly.

## Using numba.njit
Can we improve the performance further? Yes, by using numba, definitely we can.
```py
from numba import njit
@njit(cache=True)
def calculate_distances3(arr):
    ...
# 10.9 ms ± 507 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```
It is great that there is a `4x` performance improvement with numba on the numpy function.

The numba `njit` decorator is used to compile the python function to optimized machine code in nopython mode. We can also use the `jit` decorator, which allows the function to fall back to the original python implementation if numba cannot compile it.

When we set `cache=True`, numba stores the compiled function in a cache on disk. So the next time we execute the script, it can load the precompiled function, avoiding the overhead of recompilation.

## Using numba.njit with data types
Can we do it better? Yes, we need to use numba data type signature.
```py
@njit('float64[:,::1](float64[:,::1])', cache=True)
def calculate_distances4(arr):
    ...
# 10.5 ms ± 208 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```
We explicitly set the data types of the input parameters and the output. In this case, there is only minor performance improvement, most likely that numba can infer data types even without data type signature. More details about the numba data type signature can be found in the numba documents (see References section).

In generall, by specifying data types, numba can generate more efficient machine code. Knowing the exact types allows it to optimize the generated code for those types, leading to faster execution and improved memory management.

## Replacing numpy function with a python loop
As numba is good for loops, here we will replace the numpy function by a `python loop` to further boost performance.
```py
@njit('float64[:,::1](float64[:,::1])', cache=True)
def calculate_distances5(arr):
    m = arr.shape[0]
    n = arr.shape[1]
    dist_arr = np.zeros((m, m))
    for i in range(m):
        for j in range(i):
            v = 0.0
            for k in range(n):
                 v += abs(arr[i, k] - arr[j, k])
            dist_arr[i, j] = v
            dist_arr[j, i] = v
    return dist_arr
# 8.20 ms ± 163 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```
Numba is indeed good for loops. There is a `1.2x` performance improvement now, and it's about `5x` faster than the numpy version.

## Using numba.njit parallel mode
Modern computers often have multiple cores. By leveraging parallel computing, we can significantly reduce execution time.
```py
from numba import njit, prange
@njit('float64[:,::1](float64[:,::1])', cache=True, parallel=True, nogil=True)
def calculate_distances6(arr):
    m = arr.shape[0]
    n = arr.shape[1]
    dist_arr = np.zeros((m, m))
    for i in prange(m):
        for j in range(i):
            v = 0.0
            for k in range(n):
                 v += abs(arr[i, k] - arr[j, k])
            dist_arr[i, j] = v
            dist_arr[j, i] = v
    return dist_arr
# 3.68 ms ± 157 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```
Here we update the code to use numba `parallel mode` with the help of the `prange` function.

By setting `parallel=True`, numba's JIT compiler will analyze the function's code and automatically identify opportunities for parallelization, especially within loops. However, using `prange` provides more explicit control over parallelization and can be more effective in certain cases.

Finally the run time is 3.68 ms (4 cpu cores). It is about `10x` faster compared to the numpy function version without using numba.njit (40.7 ms). It is about `700x` faster compared to the raw python code (2.68 seconds).

## References
- [Numba data type signature](https://numba.pydata.org/numba-doc/dev/reference/types.html)
- [Numba data type signature caveats](https://stackoverflow.com/questions/66205186/python-signature-with-numba)
- [Optimizing python loops using numba](https://pythonspeed.com/articles/slow-numba)
