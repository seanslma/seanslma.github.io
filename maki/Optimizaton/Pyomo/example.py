# https://github.com/tum-ens/urbs/blob/master/teaching/01_Electricity_supply_of_an_island.ipynb
import pyomo.environ as pyo

# create a Concretem object
m = pyo.ConcreteModel()
m.name = 'Example'

# Sets: tech, time
tech = ['gas', 'bio'] #gas, biomass
time = [t for t in range(1, 6)]
m.tk = pyo.Set(initialize=tech) 
m.ts = pyo.Set(initialize=time, ordered=True)   

# Param: cap[tech]
cap = [100, 30]
m.cap = pyo.Param(m.tk, initialize=dict(zip(tech, cap)))

# Param: demand[time]
demand = [60, 100, 120, 80, 30]
m.demand = pyo.Param(m.ts, initialize=dict(zip(time, demand)), within=pyo.Any)

# Variables[tech, time]
m.x = pyo.Var(m.tk, m.ts, domain=pyo.NonNegativeReals, initialize=0.0)

# Objective function
m.obj = pyo.Objective(
    expr=sum(50 * m.x['gas', t] + 25 * m.x['bio', t] for t in m.ts)
)

# Constraints
# def gas_cap(m, t):
#     return m.x['gas', t] <= 100
# m.ConGasCap = pyo.Constraint(m.ts, rule=gas_cap)
# def bio_cap(m, t):
#     return m.x['bio', t] <= 30
# m.ConBioCap = pyo.Constraint(m.ts, rule=bio_cap)

@m.Constraint(m.tk, m.ts)
def ConCap(m, k, t):
    return m.x[k, t] <= m.cap[k]

# The supply should at least be equal to the demand
# def min_demand(m, t):
#     return sum(m.x[k, t] for k in m.tk) >= m.demand[t]
# m.ConDem = pyo.Constraint(m.ts, rule=min_demand)
@m.Constraint(m.ts)
def ConDem(m, t):
    return sum(m.x[k, t] for k in m.tk) >= m.demand[t]

# write model
m.write("01_concrete_b.lp", io_options={'symbolic_solver_labels': True})

# display model
m.display()
