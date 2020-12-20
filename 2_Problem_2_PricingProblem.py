# -*- coding: utf-8 -*-
"""
Created on Wed Dec 16 15:02:49 2020

@author: Daan Kerstjens
"""
import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt
import datetime
from tqdm import tqdm
import gurobipy as gp 
from gurobipy import GRB
# Input variables
timeLimit = 100 # Time limit on the gurobi runtime in seconds, just to prevent an endless loop
rows = 141 # the first 141 rows of the duty periods contain the single flights

# Printing author information
print('Group 26 \nViranca Balsingh 4554000 \nEdward Hyde 4285174 \nDaan Kerstjens 4299418')

# Reading data from files
dutyCostsTotal = pd.read_csv('2_dutyCosts.csv',parse_dates=['Departure','Arrival'],index_col=0)
timeTable = pd.read_csv('1_Timetable_Group_26.csv')
# dutyPeriodsTotal = pd.read_csv('2_Duty_Periods_Group_26.csv')

# Creating variables needed initially
dutyCosts = dutyCostsTotal.loc[:rows]
# dutyPeriods = dutyPeriodsTotal.iloc[:rows]
NoOfDuties = len(dutyCosts)
NoOfFlights = len(timeTable)
cp = dutyCosts['Cost'].values

# Creating delta_f^p: matrix containing all flights and all duty 
# periods, with delta_fpTotal[i,j] = 1 if flight i is serviced in duty j
delta_fpTotal = np.zeros([len(timeTable),len(dutyCostsTotal)])
flights = timeTable['Flight No.'].values
Flnrs = dutyCostsTotal['Flights']
pairsperflight = []

for i in tqdm(range(len(Flnrs))):
    q = ast.literal_eval(Flnrs.iloc[i])
    for r in q:
        # print(r)
        flnr = np.where(flights == r)[0][0]
        delta_fpTotal[flnr,i] = 1


# Dual problem
n = gp.Model('PricingProblem')
n.Params.timeLimit = timeLimit

# Make Gurobi variables
y = n.addMVar(NoOfFlights) # the variables pi_f, though y is easier to write
n.update()

# Make Constraints
delta_fp = delta_fpTotal[:,:NoOfDuties] # only single leg duties are used
delta_pf = delta_fp.transpose()
n.addConstr(delta_pf @y <= cp)
n.update()

# Make objective
one = np.ones([1,NoOfFlights])
n.setObjective(one @ y,GRB.MAXIMIZE)
n.update()

n.optimize()


# Column generation
start = datetime.datetime.now() # start time of column generation
cpTot = dutyCostsTotal['Cost'].values # total duty cost per pair
k = 0 # Total iterations
l = 0 # Consecutive iterations with less than 0.001 MU difference
objectives = [n.objVal] # list containing the objective value for each iteration
oud = 0
active = 1
columns = list(range(NoOfDuties))
while active > 0:
    Pi_f = np.array(n.getAttr(GRB.Attr.X,n.getVars()))
    slackness = cpTot - (delta_fpTotal.transpose() @ Pi_f)
    newColumns = list(slackness.argsort()[:50])
    columns += newColumns
    cp = dutyCostsTotal['Cost'].iloc[newColumns].values
    delta_fp = delta_fpTotal[:,newColumns]
    delta_pf = delta_fp.transpose()
    n.addConstr(delta_pf @y <= cp)
    n.update()
    n.optimize()
    k += 1
    
    # Keep track of the intermediate objective values, and how fast it changes
    objectives.append(n.objVal)
    diff = abs(oud-n.objVal)
    oud = n.objVal
    
    # If the change in objective value is less than 0.001 MU 6 times in a row
    if diff < 0.001:
        l += 1
    else:
        l = 0
    if l == 6:
        active = 0 # if the change is less than 0.001 for 6 times in a row, the column generation is finished
    if k > 100:
        print('ERROR: More than 100 iterations needed')
        break

# Plot the objective over iterations
finished = datetime.datetime.now() # Time column generation is finished
xvalues = range(len(objectives))
plt.figure()
plt.plot(xvalues,objectives,'x')
plt.xlabel('Iteration')
plt.xticks(np.arange(min(xvalues), max(xvalues)+2, 2))
plt.ylabel('Objective value')
plt.savefig('2_Problem2_objectiveIteration.png')
plt.title('Objective versus the iterations')
plt.show()

# Plot the change in objectives
objectiveChange = np.array(objectives[1:]) - np.array(objectives[:-1])
x2 = xvalues[1:]
plt.figure()
plt.plot(x2,objectiveChange,'x')
plt.xlabel('Iteration')
plt.xticks(np.arange(min(x2), max(x2)+2, 2))
plt.ylabel('Change in objective value')
plt.savefig('2_Problem2_objectiveChangeIteration.png')
plt.title('Improvement versus the iterations')
plt.show()

chosenPairings = n.getAttr(GRB.Attr.Pi)
print('The (relaxed) pricing problem has the following pairings scheduled:')
for i in range(len(chosenPairings)):
    if chosenPairings[i] > 0:
        print('Duty',i,':',chosenPairings[i])

print('Since the binary conditions are not met, the primal model is run again, with the extra variables')
NoOfDuties = len(columns)
dutyCosts = dutyCostsTotal.iloc[columns]
m = gp.Model('Crew_pairing')
m.Params.timeLimit = timeLimit



# Make variables
x = m.addMVar(NoOfDuties,vtype=GRB.BINARY) # make a variable for each pairing, constraining it to be binary

# Make constraints
# Make sure each flight is in only one used pairing. The binary condition is already implemented in the variable addition
delta_fp = delta_fpTotal[:,columns]
b = np.ones(NoOfFlights)
m.addConstr(delta_fp@x == b)


# Make objective
cp = dutyCosts['Cost'].values
cpT = cp.transpose()
m.setObjective(cpT @ x)
m.update()

m.optimize()



# Let's print some results 
chosenPairings = m.getAttr(GRB.Attr.X) # value of each variable, 1 depicts a chosen pairing, 0 it is not chosen
dutyNumbers = [] # list with actual duties occupied
crewbases = [] # list with origin of each duty, which is by assumption the crew base
destins = []
uniqueCrewbases = []
uniqueDestins = []
overnights = 0 # Number of duties not returning to crewbase
overnightCosts = 0
print('\n The (binary) crew pairing problem has the following pairings scheduled:')
for i in range(len(chosenPairings)):
    if chosenPairings[i] > 0:
        print('Duty',i)
        dutyNumbers.append(i)
        if dutyCostsTotal['Overnight'].loc[i] > 0:
            overnights += 1
            overnightCosts += dutyCostsTotal['Overnight'].loc[i]
        if dutyCostsTotal['Origin'].loc[i] not in crewbases:
            uniqueCrewbases.append(dutyCostsTotal['Origin'].loc[i])
        if dutyCostsTotal['Destination'].loc[i] not in destins:
            uniqueDestins.append(dutyCostsTotal['Destination'].loc[i])
        crewbases.append(dutyCostsTotal['Origin'].loc[i])
        destins.append(dutyCostsTotal['Destination'].loc[i])

for i in uniqueCrewbases:
    print(i,'needs',crewbases.count(i),'entire crews')
for i in uniqueDestins:
    print(i,'receives',destins.count(i),'entire crews')
print('NB: a crew consists of 1 captain, 1 first officer and 3 flight attendants')
print('The Final Objective Value is',m.objVal,',obtained after',k,'iterations, which took [h:mm:ss]:',finished-start)
print('A total of',len(dutyNumbers),'duties are included, with',overnights,'duties not returning at its crew base, giving hotel costs of MU',overnightCosts)

dutynrs = dutyNumbers[:20]
flightnr = dutyCostsTotal.loc[dutynrs,'Flights']
hotel = dutyCostsTotal.loc[dutynrs,'Overnight']
cost = dutyCostsTotal.loc[dutynrs,'Cost']

print('Duty #, #flights,first flight, hotelcost, total duty cost')
for i in range(len(dutynrs)):
    flnr = ast.literal_eval(flightnr.iloc[i])
    print(dutynrs[i],len(flnr),flnr[0],crewbases[i],hotel.iloc[i],cost.iloc[i])