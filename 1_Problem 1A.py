import numpy as np
import math
# from scipy import special, stats
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
import statsmodels.formula.api as smf

# Printing author information
print('Group 26 \nViranca Balsingh 4554000 \nEdward Hyde 4285174 \nDaan Kerstjens 4299418')

gen_df = pd.read_csv("1_Assignment1_Problem1_Datasheets_General.csv", sep=";")
group_df = pd.read_csv("1_Assignment1_Problem1_Datasheets_Group_26.csv", sep=";")
# print(gen_df)
# print(group_df)

'''
# Make function of haversine for calculating great circle distance between two points
'''


def distance(o_lat, o_lon, d_lat, d_lon):
    r = 6371  # Volumetric mean radius [km]
    o_lat = np.deg2rad(o_lat)  # Convert degrees to radians
    o_lon = np.deg2rad(o_lon)
    d_lat = np.deg2rad(d_lat)
    d_lon = np.deg2rad(d_lon)
    delta_lat = (d_lat - o_lat)
    delta_lon = (d_lon - o_lon)
    a = math.sin(delta_lat / 2) * math.sin(delta_lat / 2) + math.cos(o_lat) \
        * math.cos(d_lat) * math.sin(delta_lon / 2) * math.sin(delta_lon / 2)
    c = 2 * math.atan2(np.sqrt(a), math.sqrt(1 - a))
    d = r * c
    return d  # [km]


'''
# Parameters
'''
demand = group_df.loc[:, 'EGLL':'LPMA'].values
airports = group_df.loc[:, 'ICAO Code'].values
population = gen_df.loc[:, '2015_pop':'2018_pop'].values
GDP = gen_df.loc[:, '2015_gdp':'2018_gdp'].values
latitudes = group_df.loc[:, ['Latitude (deg)']].values
longitudes = group_df.loc[:, ['Longitude (deg)']].values

'''
# Logarithms of gravity model
# ln(Dij) = ln(k) + b1*ln(pop_i*pop_j) + b2*ln(GDP_i*GDP_j) - b3*ln(f*d_ij) 
'''
Demand = np.zeros(shape=(latitudes.size, latitudes.size))
# Demand = pd.DataFrame(0, index=range(latitudes.size), columns=range(latitudes.size))
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        if demand[i, j] > 0:
            if i != j:
                Demand[i, j] = np.log(demand[i, j])
                Demand[j, i] = Demand[i, j]
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        Demand[j-1, i] = Demand[j, i]
Demand.resize(latitudes.size-1, latitudes.size)
Demand = Demand.flatten()
# =
# ln k?
# +
b1 = np.zeros(shape=(latitudes.size, latitudes.size))
# b1 = pd.DataFrame(0, index=range(latitudes.size), columns=range(latitudes.size))
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        if i != j:
            b1[i, j] = np.log(population[i, 0] * population[j, 0])
            b1[j, i] = b1[i, j]
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        b1[j-1, i] = b1[j, i]
b1.resize(latitudes.size-1, latitudes.size)
b1 = b1.flatten()
# +
b2 = np.zeros(shape=(latitudes.size, latitudes.size))
# b2 = pd.DataFrame(0, index=range(latitudes.size), columns=range(latitudes.size))
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        if i != j:
            b2[i, j] = np.log(GDP[i, 0] * GDP[j, 0])
            b2[j, i] = b2[i, j]
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        b2[j-1, i] = b2[j, i]
b2.resize(latitudes.size-1, latitudes.size)
b2 = b2.flatten()
# -
# distances = pd.DataFrame(0, index=range(latitudes.size), columns=range(latitudes.size))
distances = np.zeros(shape=(latitudes.size, latitudes.size))
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        if i != j:
            distances[i, j] = distance(latitudes[i, 0], longitudes[i, 0], latitudes[j, 0], longitudes[j, 0])
            distances[j, i] = distances[i, j]
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        distances[j-1, i] = distances[j, i]
distances.resize(latitudes.size-1, latitudes.size)
# distance_df = pd.DataFrame(distances)
# distance_df.to_csv('distance_df')
# print(distance_df)
cost = 1.42
b3 = np.zeros(shape=(latitudes.size, latitudes.size))
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        if i != j:
            b3[i, j] = np.log(cost*distances[i, j])
            b3[j, i] = b3[i, j]
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        b3[j-1, i] = b3[j, i]
b3.resize(latitudes.size-1, latitudes.size)
b3 = b3.flatten()
'''
# 1.A.1: Calibrate the gravity model
'''
# OLS model
Y = Demand
X = np.column_stack((b1, b2, b3))
X = sm.add_constant(X)

model = sm.OLS(Y, X)
fit = model.fit()
print(fit.summary())


'''
# 1.A.2: Forecast the population and GDP
'''

pop_2020 = np.zeros(shape=(latitudes.size, 1))
for i in range(latitudes.size):
    pop_2020[i] = population[i, 1] + (2020-2018)*((population[i, 1] - population[i, 0])/(2018-2015))

GDP_2020 = np.zeros(shape=(latitudes.size, 1))
for i in range(latitudes.size):
    GDP_2020[i] = GDP[i, 1] + (2020-2018)*((GDP[i, 1] - GDP[i, 0])/(2018-2015))
print(pop_2020)
print(GDP_2020)
'''
# 1.A.3: Future demand with calibrated gravity model
'''
k = fit.params[0]
b1 = fit.params[1]
b2 = fit.params[2]
b3 = -fit.params[3]
pop_2015 = gen_df['2015_pop']
gdp_2015 = gen_df['2015_gdp']
pop_2018 = gen_df['2018_pop']
gdp_2018 = gen_df['2018_gdp']

Demand_2020 = np.zeros(shape=(latitudes.size, latitudes.size))
for i in range(latitudes.size):
    for j in range(i+1, latitudes.size):
        if i != j:
            Demand_2020[i, j] = np.exp(k) * ((((pop_2020[i]*pop_2020[j]) ** (b1)) * ((GDP_2020[i]*GDP_2020[j]) ** (b2))) / ((cost*distances[i, j]) ** (b3)))
            Demand_2020[j, i] = Demand_2020[i, j]
Demand_2020.resize(latitudes.size-1, latitudes.size)
dem2020_df = pd.DataFrame(Demand_2020)
# dem2020_df.to_excel('dem2020_df.xlsx')
print(dem2020_df.iloc[:5, :5])

# for i in range(latitudes.size):
#     for j in range(i+1, latitudes.size):
#         Demand_2020[j-1, i] = Demand_2020[j, i]
# Demand_2020.resize(latitudes.size-1, latitudes.size)
# dem2020_df = pd.DataFrame(Demand_2020)
# dem2020_df.to_excel('dem2020_df.xlsx')
# print(dem2020_df)