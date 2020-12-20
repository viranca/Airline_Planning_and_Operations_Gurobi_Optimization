# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:56:23 2020

@author: Daan Kerstjens
"""
import pandas as pd
import numpy as np
import ast
import matplotlib.pyplot as plt
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
dutyPeriodsTotal = pd.read_csv('2_Duty_Periods_Group_26.csv')

# Creating variables needed initially
dutyCosts = dutyCostsTotal.iloc[:rows]
dutyPeriods = dutyPeriodsTotal.iloc[:rows]
NoOfDuties = len(dutyCosts)
NoOfFlights = len(timeTable)
cp = dutyCosts['Cost'].values

# Creating delta_f^p: matrix containing all flights and all duty 
# periods, with delta_fpTotal[i,j] = 1 if flight i is serviced in duty j
delta_fpTotal = np.zeros([len(timeTable),len(dutyPeriodsTotal)])
flights = timeTable['Flight No.'].values
Flnrs = dutyPeriodsTotal['Flights']
pairsperflight = []

for i in tqdm(range(len(Flnrs))):
    q = ast.literal_eval(Flnrs[i])
    for r in q:
        # print(r)
        flnr = np.where(flights == r)[0][0]
        delta_fpTotal[flnr,i] = 1

# The Gurobi Model
m = gp.Model('Crew_pairing')
m.Params.timeLimit = timeLimit



# Make variables
x = m.addMVar(NoOfDuties,vtype=GRB.BINARY)

# Make constraints
# Make sure each flight is in only one used pairing
delta_fp = delta_fpTotal[:,:NoOfDuties] # only single leg duties are used
b = np.ones(NoOfFlights)
m.addConstr(delta_fp@x == b)


# Make objective
cpT = cp.transpose()
m.setObjective(cpT @ x)
m.update()

m.optimize()