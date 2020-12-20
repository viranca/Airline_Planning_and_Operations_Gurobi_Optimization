from gurobipy import *
from gurobipy import GRB
from gurobipy import quicksum
from gurobipy import Model
import pandas as pd
import numpy as np

# Printing author information
print('Group 26 \nViranca Balsingh 4554000 \nEdward Hyde 4285174 \nDaan Kerstjens 4299418')

"""
=============================================================================
Setup parameters and demand/distance matrix:
=============================================================================
"""

Airports = ['London', 'Paris', 'Amsterdam',	'Frankfurt', 'Madrid',	'Barcelona', 'Munich', 
            'Rome', 'Dublin', 'Stockholm', 'Lisbon', 'Berlin', 'Helsinki', 'Warsaw', 'Edinburgh', 'Bucharest', 
            'Heraklion', 'Reykjavik',	'Palermo', 'Madeira']

Airport_runway = [3200, 3100, 3400, 3400, 3600, 2700, 2800, 2800, 2600, 2700, 2600, 2900, 2700, 2500, 2200, 
                  1900, 1800, 2200, 2300, 1900]


Aircraft  = [0,1,2,3]
Aircraft_leasecost  = [15000, 34000, 80000, 190000]
Aircraft_seats = [45, 70, 150, 320]
Aircraft_speed = [550, 820, 850, 870]
Aircraft_TAT = [25/60, 35/60, 45/60, 60/60]
Aircraft_range = [1500, 3300, 6300, 12000]
Aircraft_runway_required = [1400, 1600, 1800, 2600]


airports = range(len(Airports))
#CASK = 0.12                                            #unit operation cost per ASK flown  	    (given in matrix below)
LF = 0.8                                                #average load factor                        (given in list above)
#s = 120                                                #number of seats per aicraft                (given in list above)  	       	      	    
#sp = 870                                               #speed of aicraft                           (given in list above)
#LTO = 20/60                                            #same as turn around time                   (given in list above)
BT = 10*7                                               #Aircraft utilisation times 7 for weekly
#AC = len(Aircraft_n)                                   #number of aircraft types                   (given by the optimization below)
#y = 0.18                                               #yield                                      (given in matrix below)                                             
B = 10000                                               #Budget                                     (Constraint 6 budget is relaxed)
g = [1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]           #Paris is the hub
g_inv = [1,1.5,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]     #Turn around time to paris is 1.5x higher

"""
=============================================================================
demand, distance and yield for every flight leg:
=============================================================================
"""
with open('1_q_demand.csv', 'r') as f:
    df_demand = pd.read_csv(f, sep=';', header=0)
q = np.array(df_demand)


with open('1_distance_df.csv', 'r') as f:
    df_distance = pd.read_csv(f, sep=',', header=0)
distance = np.array(df_distance)

#Appendix B
Yield = 5.9 * (df_distance ** -0.76) + 0.043
Yield = np.array(Yield)
for i in range(len(Yield)):
    for j in range(len(Yield)):
        if i == j:
            Yield[i][j] = 0
            
            
            
"""
=============================================================================
Compute a costmatrix for each aircraft type at each flight leg.
=============================================================================
"""
#Appendix D
#aircraft 0
#fixed cost
C_X_0 = 300
#time-based cost in hours
c_T_0 = 750
V_0 = Aircraft_speed[0]
C_T_0 = c_T_0 * (df_distance / V_0)
#fuel cost
c_F_0 = 1
f = 1.42
C_F_0 = ((c_F_0 * f)/1.5) * df_distance
C_0 = C_X_0 + C_T_0 + C_F_0 

#aircraft 1
#fixed cost
C_X_1 = 600
#time-based cost
c_T_1 = 775
V_1 = Aircraft_speed[1]
C_T_1 = c_T_1 * (df_distance / V_1)
#fuel cost
c_F_1 = 2
f = 1.42
C_F_1 = ((c_F_1 * f)/1.5) * df_distance
C_1 = C_X_1 + C_T_1 + C_F_1 

#aircraft 2
#fixed cost
C_X_2 = 1250
#time-based cost
c_T_2 = 1400
V_2 = Aircraft_speed[2]
C_T_2 = c_T_2 * (df_distance / V_2)
#fuel cost
c_F_2 = 3.75
f = 1.42
C_F_2 = ((c_F_2 * f)/1.5) * df_distance
C_2 = C_X_2 + C_T_2 + C_F_2 

#aircraft 3
#fixed cost
C_X_3 = 2000
#time-based cost
c_T_3 = 2800
V_3 = Aircraft_speed[3]
C_T_3 = c_T_3 * df_distance / V_3
#fuel cost
c_F_3 = 9.0
f = 1.42
C_F_3 = ((c_F_3 * f)/1.5) * df_distance
C_3 = C_X_3 + C_T_3 + C_F_3 
  
#accounting economies of scale (departing and arriving from hub)
C_0 = np.array(C_0)           
for i in range(len(C_0)):
    for j in range(len(C_0)):
        if i == 1 and j != 1:
            C_0[i][j] = 0.7*C_0[i][j]
        if j == 1:
            C_0[i][j] = 0.7*C_0[i][j]

C_1 = np.array(C_1)
for i in range(len(C_1)):
    for j in range(len(C_1)):
        if i == 1 and j != 1:
            C_1[i][j] = 0.7*C_1[i][j]
        if j == 1:
            C_1[i][j] = 0.7*C_1[i][j]
           
C_2 = np.array(C_2)
for i in range(len(C_2)):
    for j in range(len(C_2)):
        if i == 1 and j != 1:
            C_2[i][j] = 0.7*C_2[i][j]
        if j == 1:
            C_2[i][j] = 0.7*C_2[i][j]
            
C_3 = np.array(C_3)            
for i in range(len(C_3)):
    for j in range(len(C_3)):
        if i == 1 and j != 1:
            C_3[i][j] = 0.7*C_3[i][j]
        if j == 1:
            C_3[i][j] = 0.7*C_3[i][j]
           

"""
=============================================================================
Defining a_ij (range) matrix for each aircraft type:
=============================================================================
"""
a_0 = np.array(df_distance-Aircraft_range[0])
for i in range(len(a_0)):
    for j in range(len(a_0)):
        if a_0[i][j] >= 0:
            a_0[i][j] = 0
        else:
            a_0[i][j] = 10000

a_1 = np.array(df_distance-Aircraft_range[1])
for i in range(len(a_1)):
    for j in range(len(a_1)):
        if a_1[i][j] >= 0:
            a_1[i][j] = 0
        else:
            a_1[i][j] = 10000
            
a_2 = np.array(df_distance-Aircraft_range[2])
for i in range(len(a_2)):
    for j in range(len(a_2)):
        if a_2[i][j] >= 0:
            a_2[i][j] = 0
        else:
            a_2[i][j] = 10000

a_3 = np.array(df_distance-Aircraft_range[3])
for i in range(len(a_3)):
    for j in range(len(a_3)):
        if a_3[i][j] >= 0:
            a_3[i][j] = 0
        else:
            a_3[i][j] = 10000

"""
=============================================================================
Defining R_ij (runway) matrix for each aircraft type:
=============================================================================
"""
r_0 = np.zeros(shape=(20,20))
for i in range(len(r_0)):
    for j in range(len(r_0)):
        r_0[i][j] = Airport_runway[j] - Aircraft_runway_required[0]       
        if r_0[i][j] >= 0:
            r_0[i][j] = 10000
        else:
            r_0[i][j] = 0
           
r_1 = np.zeros(shape=(20,20))
for i in range(len(r_1)):
    for j in range(len(r_1)):
        r_1[i][j] = Airport_runway[j] - Aircraft_runway_required[1]       
        if r_1[i][j] >= 0:
            r_1[i][j] = 10000
        else:
            r_1[i][j] = 0
                       
r_2 = np.zeros(shape=(20,20))
for i in range(len(r_2)):
    for j in range(len(r_2)):
        r_2[i][j] = Airport_runway[j] - Aircraft_runway_required[2]       
        if r_2[i][j] >= 0:
            r_2[i][j] = 10000
        else:
            r_2[i][j] = 0
                     
r_3 = np.zeros(shape=(20,20))
for i in range(len(r_3)):
    for j in range(len(r_3)):
        r_3[i][j] = Airport_runway[j] - Aircraft_runway_required[3]       
        if r_3[i][j] >= 0:
            r_3[i][j] = 10000
        else:
            r_3[i][j] = 0


"""
=============================================================================
Objective function: max revenue
=============================================================================
"""
# Start modelling optimization problem
m = Model('APO1B')
x = {}
z = {}
C = {}
z_0 = {}
z_1 = {}
z_2 = {}
z_3 = {}
aircraft_type_amount = {}
w = {}

for i in airports:
    for j in airports:
        ij = str(i) + '_' + str(j)
        x[i,j] = m.addVar(obj = Yield[i][j]*distance[i][j],lb=0,
                           vtype=GRB.INTEGER , name='x_'+ij)
        w[i,j] = m.addVar(obj = Yield[i][j]*distance[i][j],lb=0,
                           vtype=GRB.INTEGER , name='w_'+ij)        
        z_0[i,j] = m.addVar(obj = -C_0[i][j], lb=0,
                           vtype=GRB.INTEGER, name='z_0_'+ij)
        z_1[i,j] = m.addVar(obj = -C_1[i][j], lb=0,
                           vtype=GRB.INTEGER, name='z_1_'+ij)
        z_2[i,j] = m.addVar(obj = -C_2[i][j], lb=0,
                           vtype=GRB.INTEGER, name='z_2_'+ij)
        z_3[i,j] = m.addVar(obj = -C_3[i][j], lb=0,
                           vtype=GRB.INTEGER, name='z_3_'+ij)        


aircraft_type_0_amount = m.addVar(obj = -Aircraft_leasecost[0], lb=0,
                                  vtype=GRB.INTEGER, name='k0')
aircraft_type_1_amount = m.addVar(obj = -Aircraft_leasecost[1], lb=0,
                                  vtype=GRB.INTEGER, name='k1')
aircraft_type_2_amount = m.addVar(obj = -Aircraft_leasecost[2], lb=0,
                                  vtype=GRB.INTEGER, name='k2')
aircraft_type_3_amount = m.addVar(obj = -Aircraft_leasecost[3], lb=0,
                                  vtype=GRB.INTEGER, name='k3')

m.update()
m.setObjective(m.getObjective(), GRB.MAXIMIZE)  # The objective is to maximize revenue

"""
=============================================================================
Constraints:
=============================================================================
"""
for i in airports:
    for j in airports:
        m.addConstr(x[i,j] + w[i,j], GRB.LESS_EQUAL, q[i][j]) #C1
        m.addConstr(w[i,j], GRB.LESS_EQUAL, q[i][j] * g[i] * g[j]) #C1*
        
        m.addConstr(x[i,j] + quicksum((w[i,m]*(1-g[j])) for m in airports) + quicksum((w[m,j]*(1-g[i])) for m in airports) ,
                    GRB.LESS_EQUAL, (z_0[i,j]*Aircraft_seats[0]+z_1[i,j]*Aircraft_seats[1]+
                                      z_2[i,j]*Aircraft_seats[2]+z_3[i,j]*Aircraft_seats[3])*LF) #C2

        
        
        m.addConstr(quicksum((z_0[i,j]) for j in airports), GRB.EQUAL, quicksum((z_0[j, i]) for j in airports)) #C3 k=0
        m.addConstr(quicksum((z_1[i,j]) for j in airports), GRB.EQUAL, quicksum((z_1[j, i]) for j in airports)) #C3 k=1
        m.addConstr(quicksum((z_2[i,j]) for j in airports), GRB.EQUAL, quicksum((z_2[j, i]) for j in airports)) #C3 k=2
        m.addConstr(quicksum((z_3[i,j]) for j in airports), GRB.EQUAL, quicksum((z_3[j, i]) for j in airports)) #C3 k=3

m.addConstr(quicksum(quicksum((((distance[i][j]/Aircraft_speed[0]+Aircraft_TAT[0]*(g_inv[j]))*(z_0[i,j]))) for i in airports) for j in airports),
            GRB.LESS_EQUAL, BT*aircraft_type_0_amount) #C4 k=0
m.addConstr(quicksum(quicksum((((distance[i][j]/Aircraft_speed[1]+Aircraft_TAT[1]*(g_inv[j]))*(z_1[i,j]))) for i in airports) for j in airports),
            GRB.LESS_EQUAL, BT*aircraft_type_1_amount) #C4 k=1
m.addConstr(quicksum(quicksum((((distance[i][j]/Aircraft_speed[2]+Aircraft_TAT[2]*(g_inv[j]))*(z_2[i,j]))) for i in airports) for j in airports),
            GRB.LESS_EQUAL, BT*aircraft_type_2_amount) #C4 k=2
m.addConstr(quicksum(quicksum((((distance[i][j]/Aircraft_speed[3]+Aircraft_TAT[3]*(g_inv[j]))*(z_3[i,j]))) for i in airports) for j in airports),
            GRB.LESS_EQUAL, BT*aircraft_type_3_amount) #C4 k=3

#constraint 5:
for i in airports:
    for j in airports:
        m.addConstr(z_0[i,j], GRB.LESS_EQUAL, a_0[i][j])
        m.addConstr(z_1[i,j], GRB.LESS_EQUAL, a_1[i][j])
        m.addConstr(z_2[i,j], GRB.LESS_EQUAL, a_2[i][j])
        m.addConstr(z_3[i,j], GRB.LESS_EQUAL, a_3[i][j])

#runway constraint
for i in airports:
    for j in airports:
        m.addConstr(z_0[i,j], GRB.LESS_EQUAL, r_0[i][j])
        m.addConstr(z_1[i,j], GRB.LESS_EQUAL, r_1[i][j])
        m.addConstr(z_2[i,j], GRB.LESS_EQUAL, r_2[i][j])
        m.addConstr(z_3[i,j], GRB.LESS_EQUAL, r_3[i][j])



#constraint 6: budget   
# m.addConstr(Aircraft_leasecost[0] * aircraft_type_0_amount + Aircraft_leasecost[1] * aircraft_type_1_amount +
#             Aircraft_leasecost[2] * aircraft_type_2_amount + Aircraft_leasecost[3] * aircraft_type_3_amount, 
#             GRB.LESS_EQUAL, B)    
    

"""
=============================================================================
Optimise and print results:
=============================================================================
"""
    
m.update()
m.write('1_Problem1B_LP.lp')
# Set time constraint for optimization (5minutes)
#m.setParam('TimeLimit', 1 * 60)
m.setParam('MIPgap', 0.005)
m.optimize()
# m.write("testout.sol")
status = m.status

solution = []   
for v in m.getVars():
      solution.append([v.varName,v.x])
print(solution)



if status == GRB.Status.UNBOUNDED:
    print('The model cannot be solved because it is unbounded')

elif status == GRB.Status.OPTIMAL or True:
    f_objective = m.objVal
    print('***** RESULTS ******')
    print('\nObjective Function Value: \t %g' % f_objective)
    print("amount of aicraft for each type: ", aircraft_type_0_amount.x, aircraft_type_1_amount.x, 
                                             aircraft_type_2_amount.x, aircraft_type_3_amount.x)
    
elif status != GRB.Status.INF_OR_UNBD and status != GRB.Status.INFEASIBLE:
    print('Optimization was stopped with status %d' % status)


# Print out Solutions
print()
print("Frequencies:----------------------------------")
print()
for i in airports:
    for j in airports:
        if z_0[i,j].X >0:
            print(Airports[i], ' to ', Airports[j], z_0[i,j].X, z_1[i,j].X, z_2[i,j].X, z_3[i,j].X)
 
#%%
"""
=============================================================================
Compute performance indicators:
=============================================================================
"""
#compute the utilization of each ac type
utilization_0 = 0
z_0_total_hours = 0
for i in airports:
    for j in airports:
        utilization_0 += (((distance[i][j]/Aircraft_speed[0]+Aircraft_TAT[0]*(g_inv[j]))*(z_0[i,j].X)))
z_0_total_hours += 3 * BT    
print(utilization_0/z_0_total_hours) 

utilization_1 = 0
z_1_total_hours = 0
for i in airports:
    for j in airports:
        utilization_1 += (((distance[i][j]/Aircraft_speed[1]+Aircraft_TAT[1]*(g_inv[j]))*(z_1[i,j].X)))
z_1_total_hours += 1 * BT   
print(utilization_1/z_1_total_hours)  

utilization_2 = 0
z_2_total_hours = 0
for i in airports:
    for j in airports:
        utilization_2 += (((distance[i][j]/Aircraft_speed[2]+Aircraft_TAT[2]*(g_inv[j]))*(z_2[i,j].X)))
z_2_total_hours += 4 * BT   
print(utilization_2/z_2_total_hours)   

utilization_3 = 0
z_3_total_hours = 0
for i in airports:
    for j in airports:
        utilization_3 += (((distance[i][j]/Aircraft_speed[3]+Aircraft_TAT[3]*(g_inv[j]))*(z_3[i,j].X)))      
z_3_total_hours += 0 * BT   
print(utilization_3)
print(z_3_total_hours)


#%%
#compute the percentage of filled seats
seats_used = 0
seats_available = 0
for i in airports:
    for j in airports:
        seats_used += x[i,j].X
        for m in airports:
            seats_used += (w[i,m].X*(1-g[j]))+ (w[m,j].X*(1-g[i]))
        seats_available += (z_0[i,j].X*Aircraft_seats[0]+z_1[i,j].X*Aircraft_seats[1]+ z_2[i,j].X*Aircraft_seats[2]+z_3[i,j].X*Aircraft_seats[3])*LF
            
print(seats_used/seats_available)       































            