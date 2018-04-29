import arcpy
import os
import math
import random
import numpy
from Tkinter import*



## Definition of required parameters
## NOTE: THE X AND Y FIELDS SHOULD BE USED AS PARAMETER ONLY IF THE INPUT IS
## A TABLE, IF A POINT FEATURE CLASS IS USED, THESE PARAMETERS SHOULD BE OMITTED. 

inFeature = arcpy.GetParameterAsText(0)
x_field = arcpy.GetParameterAsText(1)
y_field = arcpy.GetParameterAsText(2)
t_field = arcpy.GetParameterAsText(3)
id_field = arcpy.GetParameterAsText(4)
c_criteria = arcpy.GetParameterAsText(5)
iter_val = arcpy.GetParameterAsText(6)
    
## Define "spaceTimeDiff" dictionary to store all time space differences
## "tsList" stores a list of tupels as (ID, x, y, time)

tsList = []
spaceTimeDiff = {}

## Accessing Records either for a table or a featureclass
path = inFeature 
desc = arcpy.Describe(path)
if desc.DatasetType == "Table": 
    with arcpy.da.SearchCursor(inFeature,(id_field,x_field,y_field,t_field))as cursor:
        for row in cursor:
            tsList.append((row[0],row[1],row[2],row[3]))

elif desc.DatasetType == "FeatureClass" and desc.shapeType == "Point":   
    with arcpy.da.SearchCursor(inFeature,(id_field,"shape@xy",t_field)) as cursor:
        for row in cursor:
            x_coor = row[1][0]
            y_coor = row[1][1]
            tsList.append((row[0],x_coor,y_coor,row[2]))
else:
    arcpy.AddMessage("Unsupported file format")
            
## Compute space time differences for each pair in the data and store the values
## in the "spaceTimeDiff" dictionary
    
count = 1
for item in tsList:
    print "----------------------------------"
    print item[0]
    print "----------------------------------"
    for j in range (count,len(tsList)):
        spaceVal = math.sqrt(((item[1] - tsList[j][1])**2)+ ((item[2] - tsList[j][2])**2))
        timeVal = abs(item[3] - tsList[j][3])
        key = str(item[0]) + ":" + str(tsList[j][0])
        temp_dic = {key:(spaceVal,timeVal)}
        spaceTimeDiff.update(temp_dic)
    count += 1
    
## Function definition for the calculation of the closness thresholds (mean or median)

def GetMeanVal(dic):
	spaceList= []
	timeList = []
	for key in dic:
		spaceList.append(dic[key][0])
		timeList.append(dic[key][1])
	spaceThreshold = numpy.mean(spaceList)
	timeThreshold = numpy.mean(timeList)
	return(spaceThreshold,timeThreshold)

def GetMedianVal(dic):
	spaceList= []
	timeList = []
	for key in dic:
		spaceList.append(dic[key][0])
		timeList.append(dic[key][1])
	spaceThreshold = numpy.median(spaceList)
	timeThreshold = numpy.median(timeList)
	return(spaceThreshold,timeThreshold)



## Setting the closeness critera based on user input

if c_criteria == "Mean":
    closeness = (GetMeanVal(spaceTimeDiff))
elif c_criteria == "Median":
    closeness = (GetMedianVal(spaceTimeDiff))
    

## Calculation of Chi-Square test and the 2X2 matrix (Logical Structure of knox Index)
## This is where the Monte-Carlo Simulation Starts
    
knoxStructure = {"CS,CT":0,"CS,FT":0,"FS,CT":0,"FS,FT":0}
for key in spaceTimeDiff:
    if spaceTimeDiff[key][0] <= closeness[0] and spaceTimeDiff[key][1] <= closeness[1]:
        knoxStructure["CS,CT"] += 1        
    elif spaceTimeDiff[key][0] <= closeness[0] and spaceTimeDiff[key][1] > closeness[1]:
        knoxStructure["CS,FT"] += 1
    elif spaceTimeDiff[key][0] > closeness[0] and spaceTimeDiff[key][1] <= closeness[1]:
        knoxStructure["FS,CT"] += 1
    else:
        knoxStructure["FS,FT"] += 1
ksList = knoxStructure.values()
     
## Calculation of Expected Frequencies for knox index

n = float(knoxStructure["CS,CT"] + knoxStructure["CS,FT"] + knoxStructure["FS,CT"] + knoxStructure["FS,FT"])
s1 = knoxStructure["CS,CT"] + knoxStructure["CS,FT"]
s2 = knoxStructure["FS,CT"] + knoxStructure["FS,FT"]
s3 = knoxStructure["CS,CT"] + knoxStructure["FS,CT"]
s4 = knoxStructure["CS,FT"] + knoxStructure["FS,FT"]

e1 = s1*s3/n
e2 = s1*s4/n
e3 = s2*s3/n
e4 = s2*s4/n

EKnoxStructure = {"CS,CT":e1,"CS,FT":e2,"FS,CT":e3,"FS,FT":e4}
EksList = EKnoxStructure.values()

## Calculation of Chi-Square test for the four quadrants
total = 0
for i in range(0,4):
    total = total + ((ksList[i] - EksList[i])**2)/EksList[i]
    
print total
arcpy.AddMessage("-------------------------")
arcpy.AddMessage("Chi: " + str(total))
arcpy.AddMessage("-------------------------")

## Monte Carlo Simulation
###**************************************************************************************************
sDiffList = []
tDiffList = []
for key in spaceTimeDiff:
    spaceTimeDiff[key]
    sDiffList.append(spaceTimeDiff[key][0])
    tDiffList.append(spaceTimeDiff[key][1])
sMax = max(sDiffList)
sMin = min(sDiffList)
tMax = max(tDiffList)
tMin = min(tDiffList)

## Simulation function definition, which takes "iteration" as a
## user input

def simulate(iteration):
    chiList = []
    for i in range (1,iteration+1):        
        print "-------------------------------------------"
        print ("Run: " + str(i))
        print "-------------------------------------------"
        for key in spaceTimeDiff:            
            sDiff = random.uniform(sMin,sMax)
            tDiff = random.randint(tMin,tMax)
            diffList = [sDiff,tDiff]
            spaceTimeDiff[key] = diffList

        # Closeness Thresholds for each Run
        closeness = (GetMeanVal(spaceTimeDiff))
        # Compute knoxStructure
        knoxStructure = {"CS,CT":0,"CS,FT":0,"FS,CT":0,"FS,FT":0}
        for key in spaceTimeDiff:
            if spaceTimeDiff[key][0] <= closeness[0] and spaceTimeDiff[key][1] <= closeness[1]:
                knoxStructure["CS,CT"] += 1        
            elif spaceTimeDiff[key][0] <= closeness[0] and spaceTimeDiff[key][1] > closeness[1]:
                knoxStructure["CS,FT"] += 1
            elif spaceTimeDiff[key][0] > closeness[0] and spaceTimeDiff[key][1] <= closeness[1]:
                knoxStructure["FS,CT"] += 1
            else:
                knoxStructure["FS,FT"] += 1
        ksList = knoxStructure.values()
        # Compute Expected knoxStructure
        n = float(knoxStructure["CS,CT"] + knoxStructure["CS,FT"] + knoxStructure["FS,CT"] + knoxStructure["FS,FT"])
        s1 = knoxStructure["CS,CT"] + knoxStructure["CS,FT"]
        s2 = knoxStructure["FS,CT"] + knoxStructure["FS,FT"]
        s3 = knoxStructure["CS,CT"] + knoxStructure["FS,CT"]
        s4 = knoxStructure["CS,FT"] + knoxStructure["FS,FT"]
        e1 = s1*s3/n
        e2 = s1*s4/n
        e3 = s2*s3/n
        e4 = s2*s4/n
        EKnoxStructure = {"CS,CT":e1,"CS,FT":e2,"FS,CT":e3,"FS,FT":e4}
        EksList = EKnoxStructure.values()
        # Compute Chi-Square
        total = 0
        for i in range(0,4):
            total = total + ((ksList[i] - EksList[i])**2)/EksList[i]

        print "Chi: " + str(total)                
        arcpy.AddMessage("Chi: " + str(total))
        chiList.append(total)
        
    return chiList
###**************************************************************************************************
## Invoke the simulation function based on user input
perList = [0.005, 0.01, 0.025, 0.05, 0.1, 0.9, 0.95, 0.975, 0.99, 0.995]

def ComputePercentile(chiList,perList):
    percentile = []
    chiList.sort()
    n = len(chiList)
    for per in perList:
        index = (n*per)-1
        if index < 0:
            index = 0
        if not float(index).is_integer():
            index = int(round(index))
            print ("index is not int: " + str(index))
            temp_per = chiList[index]
        elif float(index).is_integer():
            index = int(index)
            print ("index is int: " + str(index))
            vals = chiList[index],chiList[index]
            temp_per = numpy.mean(vals)
        if temp_per <= min(chiList):
            temp_per = min(chiList)
        percentile.append(temp_per)
    return percentile    

if iter_val:
    chiList = simulate(int(iter_val))
    chiPercentile = ComputePercentile(chiList,perList)
    pairs = len(spaceTimeDiff)
    arcpy.AddMessage("*************************************")
    arcpy.AddMessage("The number of paris is: " + str(pairs))
    for i in range (0,len(chiPercentile)):    
        per = perList[i]*100
        arcpy.AddMessage(str(per) + " Percentile: " + str(chiPercentile[i]))
    
    arcpy.AddMessage("*************************************")
    



        
    


 
 
    
        

    
        
    
    
        
            
            
        
        
        

