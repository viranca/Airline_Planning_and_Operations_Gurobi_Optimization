# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 15:25:14 2020

@author: Daan Kerstjens
"""
import pandas as pd
import numpy as np
import ast
from tqdm import tqdm

# Information regarding crew types, quantities and salary
briefPeriod = 25 #(de)brief periods in minutes
crewTypes = ['Captain','FO','FA']
qty = np.array([1,1,3]) #No. of each crewtype needed aboard
fixedSalary = np.array([98,35,15])
dutyPay = np.array([120,55,18])
# base = 'LFPG'

# Printing author information
print('Group 26 \nViranca Balsingh 4554000 \nEdward Hyde 4285174 \nDaan Kerstjens 4299418')

# Importing data, save it as DataFrame
dfTimetable = pd.read_csv('1_Timetable_Group_26.csv', index_col=0,parse_dates=['Departure Time','Arrival Time'],infer_datetime_format=True)
dfDutyPeriods = pd.read_csv('2_Duty_Periods_Group_26.csv', index_col=0)
dfHotelCosts = pd.read_csv('3_Hotel_Costs_Group_26.csv', index_col=0)
dfHotelCosts = dfHotelCosts.rename(columns={'Per Night Cost Per Room (in MU)': 'cost'})

# Calculate Duty Time per flight
dfTimetable['Duty Time'] = dfTimetable['Arrival Time'] - dfTimetable['Departure Time']
dfTimetable['Duty Time'] += pd.Timedelta(minutes=2*briefPeriod)
for i in range(len(dfTimetable)):
    if dfTimetable['Duty Time'].iloc[i] < pd.Timedelta(hours=0):
        dfTimetable['Duty Time'].iloc[i] += pd.Timedelta(days=1)


# Calculate Duty Time and Hotel costs per duty period
duties = []
overnight = []
destinations = []
origins = []
dep = []
arr = []
for flights in tqdm(dfDutyPeriods['Flights']):
    flights = ast.literal_eval(flights)
    dutyTime = pd.Timedelta(hours=0)
    for flight in flights:
        dutyTime += dfTimetable.loc[flight,'Duty Time']
    duties.append(dutyTime)
    home = dfTimetable.loc[flights[0],'Origin']
    dest = dfTimetable.loc[flight,'Destination']
    origins.append(home)
    destinations.append(dest)
    arr.append(dfTimetable.loc[flight,'Arrival Time'])
    dep.append(dfTimetable.loc[flights[0],'Departure Time'])
    if dest != home: # If the duty does not finish at the crew home base, hotel costs are added
        overnight.append(sum(qty)*dfHotelCosts.loc[dest,'cost'])
    else:
        overnight.append(0)
dfDutyPeriods['Origin'] = origins
dfDutyPeriods['Destination'] = destinations
dfDutyPeriods['Departure'] = dep
dfDutyPeriods['Arrival'] = arr
dfDutyPeriods['Departure'] = dfDutyPeriods['Departure'].dt.time
dfDutyPeriods['Arrival'] = dfDutyPeriods['Arrival'].dt.time
dfDutyPeriods['Duty Time'] = duties
dfDutyPeriods['Overnight'] = overnight # hotel costs

# Total duty costs
costs  = dfDutyPeriods['Overnight'].copy() # Hotel costs
costs += np.dot(qty,fixedSalary) #fixed costs
costs += np.dot(qty,dutyPay) * pd.to_numeric(dfDutyPeriods['Duty Time']) / 3600 / 10**9
dfDutyPeriods['Cost'] = costs
dfDutyPeriods.to_csv('2_dutyCosts.csv')


# Give Duty Costs of some duties
needed = [100,500,750,1200,2000]
for i in needed:
    print('Duty',i,'costs',dfDutyPeriods['Cost'].loc[i])