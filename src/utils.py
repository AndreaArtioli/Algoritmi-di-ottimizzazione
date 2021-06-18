
import json
import networkx as nx
from networkx.readwrite import json_graph
from math import sqrt
from colour import Color
import numpy as np
import os

import xlrd
import matplotlib.pyplot as plt

from src.dataStructure import *

def distanceMeters(node1, node2):
	return sqrt( (node1.coords[0] - node2.coords[0])**2 + (node1.coords[1] - node2.coords[1])**2 )

def distanceMinutes(node1, node2):
	'''distance in meters between 2 nodes / VECHICLE_SPEED plus the service time for the arrival node'''
	return round(distanceMeters(node1, node2)/VEHICLE_SPEED + node2.service_time)

def createGraph(NODES):
	g = nx.Graph()
	g.add_nodes_from([(node.id, {'nodeId': node.id, 'pos': (node.coords[0], node.coords[1]), 'start_time': node.start_time, 'end_time': node.end_time, 
									'service_time': node.service_time, 'demand': node.demand, 'served': node.served} ) for node in NODES])
	g.add_edges_from([(node1.id, node2.id, {'distance': distanceMinutes(node1, node2)}) for node1 in NODES for node2 in NODES if node1.id != node2.id])
	return g

def calculateDistancesFromDepot(NODES):
	distance_from_depot = list()
	node1 = NODES[DEPOT] 
	for node2 in NODES:
		if node1.id != node2.id:
			distance_from_depot.append(distanceMeters(node1, node2))

	return distance_from_depot

def calculateSpeed(distance_from_depot):
	avg_distance = sum(distance_from_depot)/(len(distance_from_depot))
	speed = avg_distance/7.5
	print(f'Average distance: {avg_distance}')
	print(f'Vehicle speed: {speed}')
	return speed

def assignTimeWindow(NODES, plot_distribution = False):
	division = [start for start in range(0, 240, 15)]
	mu, sigma = len(division)/2, 3 # mean and standard deviation
	s = np.random.normal(mu, sigma, 3*len(NODES))

	counter = 0
	for node in NODES:
		if node != NODES[DEPOT]:
			if 0 <= int(s[counter]) < len(division)-1:
				#print(f'è stato estratto uno start time di {division[int(s[counter])]}')
				node.start_time = division[int(s[counter])]
				node.end_time = node.start_time + 30
			else:
				counter += 1
				while 0 > int(s[counter]) and  int(s[counter]) >= len(division)-1:
					counter +=1
				node.start_time = division[int(s[counter])]
				node.end_time = node.start_time + 30
			counter += 1
		else:
			node.start_time = 0
			node.end_time = 10000

	if plot_distribution:
		count, bins, ignored = plt.hist(s, 30, density=True)
		plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) * np.exp( - (bins - mu)**2 / (2 * sigma**2) ), linewidth=2, color='r')
		plt.show()

def read_json_file(filename):
    with open(filename) as f:
        js_graph = json.load(f)
    return json_graph.node_link_graph(js_graph)

def read_info_file(filename):
	nvehicles = 0
	capacity = 0
	with open(filename) as f:
		line = f.read().split()
		nvehicles = int(line[0])
		capacity = int(line[1])
		depot = int(line[2])
		print(f"dal file di info ho letto nvehicles: {nvehicles}, capacity: {capacity}, depot: {depot}")

	return nvehicles, capacity, depot

def getNodesFromGraph(g):
	NODES = []
	for node in g.nodes.data():
		data = node[1]
		NODES.append(Node(nodeId=node[0], coords=tuple(data['pos']), start_time=data['start_time'], end_time=data['end_time'], 
							service_time=data['service_time'], demand=data['demand']))
	return NODES

def drawSolution(SOLUTION, g, title, save=False, path=None, subpath="", depot=0):
	graph = nx.Graph()
	COLOR_LIST = list(Color('red').range_to(Color('purple'), len(SOLUTION)+1))
	nodeColorList = [None for _ in range(g.number_of_nodes())] #len(NODES)
	for node in g.nodes(data=True):
		graph.add_node(node[1]['nodeId'], pos=node[1]['pos']) 

	counter = 0
	for vehicle in SOLUTION:
		for node in vehicle.tour:
			nodeColorList[node.id] = COLOR_LIST[counter].hex_l

		counter += 1
		edges = [(node1.id, node2.id) for node1, node2 in zip(vehicle.tour[:-1], vehicle.tour[1::])]
		graph.add_edges_from(edges)

	pos = {node:(x, y) for (node, (x, y)) in nx.get_node_attributes(graph, 'pos').items()}
	nx.draw_networkx(graph, pos, with_labels=True)
	counter = 0
	for vehicle in SOLUTION:
		nodes = []
		for node in vehicle.tour:
			nodes.append(node.id)
		edges = [(node1.id, node2.id) for node1, node2 in zip(vehicle.tour[:-1], vehicle.tour[1::])]
		color = COLOR_LIST[counter]
		counter += 1
		nx.draw_networkx_nodes(graph, pos, nodelist=nodes, node_color=color.hex_l, label=f'vehicle {vehicle.id}')
		nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=color.hex_l)#, width=1.0)	
	
	#nx.draw_networkx_nodes(graph,pos, nodelist=[i for i in range(len(nodeColorList))], node_color=nodeColorList)
	nx.draw_networkx_nodes(graph, pos, nodelist=[depot], node_color=COLOR_LIST[-1].hex_l) 	
	plt.axis('equal')
	plt.title(title)
	plt.legend(loc="upper left")

	if save:
		dirname = path.split('/')[1].split('.')[0]
		dirname += subpath
		if not os.path.exists(dirname):
			os.makedirs(dirname)
		plt.savefig(dirname + '/' + title + '.png', format="PNG")
		print("Saved in " + dirname + '/' + title + '.png')
	else:
		plt.show()

	plt.clf()

################## DATASET PARSER ##################

def hombergerParser(dataset):
	CAPACITY = 0
	DEPOT = 0
	NODES = []
	NVEHICLES = 0

	with open(dataset) as file:
		print(dataset)
		iterator = file.__iter__()
		line = iterator.__next__()
		try:
			while (True):
				line = iterator.__next__()
				if line.startswith("NUMBER     CAPACITY"):
					line = iterator.__next__()
					NVEHICLES = int(line.split()[0])
					'''Always 3 orders at maximum'''
					CAPACITY = 3
					DEPOT = 0
				elif line.startswith("CUST NO.  XCOORD.    YCOORD.    DEMAND   READY TIME  DUE DATE   SERVICE TIME"):
					line = iterator.__next__()
					while(True):
						line = iterator.__next__()
						info = line.split()
						NODES.append(Node(nodeId=int(info[0]), coords=tuple([int(info[1]), int(info[2])]), 
							demand=1, start_time=int(info[4]), end_time=int(info[5]), service_time=5))
					NODES[DEPOT].service_time = 0
		
		except StopIteration:
			print(f'NVEHICLES: {NVEHICLES}, CAPACITY: {CAPACITY}')
			print(f'Graph creation finished. {len(NODES)} nodes found. Depot at: {DEPOT}')

	return CAPACITY, DEPOT, NODES, NVEHICLES

def l_vrpParser(dataset):
	CAPACITY = 0
	DEPOT = 0
	NODES = []
	NVEHICLES = 0

	with open(dataset) as file:
		iterator = file.__iter__()
		line = iterator.__next__()
		while (line != "EOF"):

			if line.startswith("DIMENSION"):
				DIMENSION = int(line.split()[2])

			if line.startswith("CAPACITY"):
				CAPACITY = 3

			if line.startswith("VEHICLES"):
				NVEHICLES = int(line.split()[2])
				#COLOR_LIST = list(Color('red').range_to(Color('purple'), NVEHICLES+1))

			if line.startswith("NODE_COORD_SECTION"):	
				for i in range(DIMENSION):
					line = iterator.__next__()
					coords = ()
					try:
						coords = (int(line.split()[1]), int(line.split()[2]))
					except ValueError:
						coords = (float(line.split()[1]), float(line.split()[2]))

					NODES.append(Node(nodeId=i, coords=coords, start_time=0, end_time=0, service_time=5))

			if line.startswith("DEMAND_SECTION"):
				for i in range(DIMENSION):
					line = iterator.__next__()

			if line.startswith("DEPOT_SECTION"):
				line = iterator.__next__()

			try:
				line = iterator.__next__()
			except StopIteration:
				line = "EOF"

	return CAPACITY, DEPOT, NODES, NVEHICLES