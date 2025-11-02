---
layout: post
tags: ["Python", "Gurobi"]
---

# Using Gurobi Python matrix API to reduce problem creation time

When doing optimizations using Python, many people choose the popular `pyomo` package to create optimization problems. However, pyomo is known for its slow performance and some other issues. That's why `gurobipy` becomes a more attractive alternative.

We definitely know that `gurobipy` is much faster for creating problems and easier to interact directly with the gurobi solver. But do you know that there is also a Python matrix API in gurobipy? Here I will demonstrate some gurobipy matrix API features that will make your code run even faster and easier to maintain.

## How to use gurobipy
An optimization problem basically contains an objective, some variables and some constraints. So the task to create a problem is creating decision variables, setting variable coefficients to the objective, and adding constraints based on the variables.

Here I will use a basic example to show the whole process. Assume we have a variable demand for one year with 5 minutes intervals. The demand should be provided by two generators (g1: integer outputs with price 2, g2: continuous outputs with price 4). If there is not enough generation to meet the demand, there is a penalty proportional to the demand.

The problem creation time is about 8.8 seconds for the following provided example.

```py
# gurobi version: v12.0.0rc1
import time
import numpy as np
import scipy.sparse as sp
import gurobipy as gp
from gurobipy import GRB

np.random.seed(42)

# Create a model
model = gp.Model('gurobi_test')

# Number of periods (1 year with 5min intervals)
n_period = 365 * 288
periods = list(range(n_period))
gen1 = np.random.randint(0, 6, n_period)
gen2 = np.random.uniform(0, 9, n_period)
demand = np.random.uniform(0, 10, n_period)
penalty = 3.5 * demand

# Record time before creating the problem
t0 = time.time()

# Create variables
v_g1 = {
    i: model.addVar(vtype=GRB.INTEGER, lb=0, ub=gen1[i])
    for i in periods
}
v_g2 = {
    i: model.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=gen2[i])
    for i in periods
}
v_on = {
    i: model.addVar(vtype=GRB.BINARY)
    for i in periods
}

# Set objective
obj_expr = gp.quicksum(
    2 * v_g1[i] + 4 * v_g2[i] + penalty[i] * v_on[i]
    for i in periods
)
model.setObjective(obj_expr, GRB.MINIMIZE)

# Add constraints
r1 = {
    i: model.addConstr(
        v_g1[i] + v_g2[i] + demand[i] * v_on[i] == demand[i]
    ) for i in periods
}

# Update model and print time for creating the problem
model.update()
print(f'Time for creating problem: {time.time() - t0:.3f} seconds')

# Write problem to file in LP format
model.write('c:/test/gurobi_test.lp')

# Optimize the model
model.optimize()

# Check if the optimization was successful
if model.status == GRB.OPTIMAL:
    model.write('c:/test/gurobi_test.sol')
    print('Model is optimal.')
    print(f'Objective value: {model.objVal}')
elif model.status == GRB.INFEASIBLE:
    print('Model is infeasible.')
elif model.status == GRB.UNBOUNDED:
    print('Model is unbounded.')
else:
    print(f'Optimization ended with status {model.status}')
```

## How to use Gurobi Python matrix API
Gurobi matrix API has a function called `model.addMVar`, which has a `shape` parameter. We can use this function to add multiple variables with the same type. Then we can use matrix operations similar to the ones in `numpy` to add objective terms and constraints.

Note that the bounds of the variables and the constraint right-hand sides all can be inputs in the numpy array format. The variable bounds can also be updated using a numpy array. The variable solutions can be extracted into a numpy array as well.

```py
...
# Create variables
v_g1 = model.addMVar(n_period, vtype=GRB.INTEGER, lb=0, ub=gen1)
v_g2 = model.addMVar(n_period, vtype=GRB.CONTINUOUS, lb=0, ub=gen2)
v_on = model.addMVar(n_period, vtype=GRB.BINARY)

# Set objective
obj_expr = (2 * v_g1 + 4 * v_g2 + penalty * v_on).sum()
model.setObjective(obj_expr, GRB.MINIMIZE)

# Add constraints
r1 =  model.addConstr(
    v_g1 + v_g2 + demand * v_on == demand
)
...
```
After using matrix API functions, now the problem creation time is about 1.6 seconds - that's about 5x to 6x faster. At the same time, the code is shorter and cleaner.

If the coefficients of the MVar elements are different in the constraints, we can use an overloaded decorator `@` to do that:
```py
# c[0]:  x[0] + y[0] >= 10
# c[1]: 2x[1] + y[1] >= 11
x = model.addMVar(2, name='x')
y = model.addMVar(2, name='y')
M = sp.diags([1, 2]) # a sparse diagnostic matrix
c = model.addConstr(M@x + y >= np.array([10, 11]), name='c')
```

If we need to add a constraint only using one element of the MVar, this can be easily done:
```py
x = model.addMVar(2, name='x')
y = model.addVar(name='y')
c = model.addConstr(x[0] + y >= 99)
```

## Example of 2D MVars
Assume we have some constraints like:
```
c[0]: x[0,0] + x[0,1] + x[0,2] >= 11
c[1]: x[1,0] + x[1,1] + x[1,2] >= 11
```

To add these constraints to the optimization problem, this can be easily done with 2D MVars:
```py
x = model.addMVar((2,3), name='x')
c = model.addConstr(x.sum(axis=1) >= 11, name='c')

model.setObjective(10 * x.sum(), GRB.MINIMIZE)
```

By default, `MVar.sum()` will add all elements on all directions. By setting `axis=1` it will add all elements in the row direction.

If the objective coefficients are not a constant, we can add the objective like this:
```py
coeffs = np.array([1,2])
model.setObjective(coeffs @ x.sum(axis=1), GRB.MINIMIZE)
```

If the objective coefficients for each elements in the MVar are not the same, we can still use a matrix operation to add the objective:
```py
coeffs = np.array([[1,2,3], [4,5,6]])
model.setObjective((coeffs * x).sum(), GRB.MINIMIZE)
```

## Example of shifted MVars
In many cases we need to add constraints related to the difference of variables between two consecutive time points. This can also be done nicely with MVars.

```py
# x[0] - x[-1] >= 0  # x[-1] = 9 is the initial value of x
# x[1] - x[0]  >= 1
# x[2] - x[1]  >= 2
S = sp.diags(np.ones(3 - 1), -1, shape=(3, 3), format='csr')
# S = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
x0 = np.array([9, 0, 0])
rhs = np.array([0, 1, 2])
c = model.addConstr(x - S@x - x0 >= rhs)
```

## Changing constraint coefficients
If we need to update some constraints, for example, changing some variable coefficients, we can use the method `model.chgCoeff`:
```py
model.chgCoeff(c[0], x[0], 10.0)
```

Compared with other language APIs, there is not a method called `model.chgCoeffs()` in the Python API. Therefore, we can only change one constraint coefficient at a time. Hopefully the method `model.chgCoeffs()` will be added in the future.

## Updating Objective
Think about creating a project using object-oriented programming. In this case, ideally we need to set the objective terms related to each object separately. However, there is not a Python API method that can be used to add the objective terms gradually.

There are two workarounds:
- get the objective using `getObjective()` then add additional terms and set the objective again using `setObjective()`, or
- add objective terms from different objects together and then set the objective using `setObjective()`

Here is an example showing how to do it using the second option:
```py
obj_expr = 0
obj_expr += x.sum()
obj_expr += (coeffs * y).sum()
model.setObjective(obj_expr, GRB.MINIMIZE)
```

Note that setting the variable and constraint names will increase the problem creation time. Thus it's best to do so only for debugging purpose - you can use a flag to enable or disable variable and constraint name setting.

More details about the Gurobi Python matrix API can be found in the manual: https://docs.gurobi.com/projects/optimizer/en/current/index.html
