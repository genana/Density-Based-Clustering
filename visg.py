from matplotlib import animation as a
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import copy
import math

import warnings
warnings.filterwarnings('ignore')

file_name = ("./GlobalLandTemperatures/GlobalLandTemperaturesByMajorCity.csv")
data = pd.read_csv(file_name, parse_dates=['dt'])

data = data[data.dt.dt.year >= 1900]
data.City = data.City.str.cat(data.Country, sep=', ')
cmeans = data.groupby([data.City, data.dt.dt.year])['AverageTemperature'].mean().unstack()
data = data[['City', 'Country', 'Latitude', 'Longitude']].drop_duplicates()
cities = data['City']

fig = plt.figure(figsize=(13, 7), edgecolor='k')

START_YEAR = 2000 #min 1743
LAST_YEAR = 2013 #max 2013

UNCLASSIFIED = -2
NOISE = -1

class Point:
    def __init__(self, city, temps):
        self.city = city
        self.temps = temps
        self.cluster_id = UNCLASSIFIED

    def change_cluster_id(self, cluster_id):
    	self.cluster_id = cluster_id

    def display(self, i, year):
        print ('{}, Temp: {}'.format(self.city, self.temps[year]))
        plt.text(i-0.5, self.temps[year]-0.9, self.city.split(',')[0], size=6, alpha=1)
        return self.temps[year]


def w_card(points):
    return len(points)

def n_pred(p1, p2, year):
    return abs(p1.temps[year] - p2.temps[year]) < 1

def getNeighbors(points, point, year, n_pred):
    return list(filter(lambda x: n_pred(point, x, year), points))

def expand_cluster(points, point, year, cluster_id, n_pred, min_card, w_card):
    
    if w_card([point]) <= 0:
        point.change_cluster_id(UNCLASSIFIED)
        return False

    seeds = getNeighbors(points, point, year, n_pred)
    if w_card(seeds) < min_card:
        point.change_cluster_id(NOISE)
        return False

    seeds1 = (p for p in seeds if p != point) # seeds.remove(point)
    seeds = list(seeds1)

    while len(seeds) > 0:
        current_point = seeds[0]
        results = getNeighbors(points, current_point, year, n_pred)
        if w_card(results) >= min_card:
            for result in results:
                if w_card([result]) > 0 and result.cluster_id in [UNCLASSIFIED, NOISE]:
                    if result.cluster_id == UNCLASSIFIED:
                        seeds.append(result)
                    result.change_cluster_id(cluster_id)
        
        seeds1 = (p for p in seeds if p != current_point)
        seeds=list(seeds1)

    return True

def GDBSCAN(points, year, n_pred, min_card, w_card):
    
    points = copy.deepcopy(points)
    cluster_id = 0
    clusters = {}
    for point in points:
        if point.cluster_id == UNCLASSIFIED:
            if expand_cluster(points, point, year, cluster_id, n_pred, min_card, w_card):
                cluster_id = cluster_id + 1

    for point in points:
        key = point.cluster_id
        if key in clusters:
            clusters[key].append(point)
        else:
            clusters[key] = [point]

    return clusters


X = []

for i, city in enumerate(cities):
    temps = cmeans.loc[city]
    point = Point(city, temps)
    X.append(point)

def update(frame_number):

    plt.cla()
    current_year = START_YEAR + (frame_number % (LAST_YEAR - START_YEAR + 1))
    plt.text(30, 1, str(current_year), fontsize=100, alpha=0.25)
        
    for point in X:
        point.cluster_id = -2

    clusters = GDBSCAN(X, current_year, n_pred, 4, w_card)

    i=0
    colors = plt.cm.gist_ncar(np.linspace(0, 1, len(clusters)))
    
    col=[]
    x=[]
    y=[]
    for key, color in zip(clusters, colors):
        if key == -1:
            print ('Outliers:')
            color='k'
        else:
            print ('Cluster: %d' % int(key+1))

        for p in clusters[key]:
            q=p.display(i, current_year)
            y.append(q)
            col.append(color)
            x.append(i)
            i+=1
        print ("\n")

    plt.scatter(x, y, c = col, s=40, edgecolor='k', alpha=0.8)
    plt.title('GDBSCAN\nNumber of clusters: %d' % int(len(clusters) - 1))
    plt.xlabel('X')
    plt.ylabel('Mean Temperature/yr\n')
    plt.ylim([0, 34])

ani = a.FuncAnimation(fig, update, interval=60, frames=LAST_YEAR-START_YEAR+1)

plt.show()
