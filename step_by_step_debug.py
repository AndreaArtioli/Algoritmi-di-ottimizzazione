from colour import Color
from copy import deepcopy, copy 

import random
import networkx as nx
import numpy as np
import os

from src.dataStructure import *
from vrptw import drawSolution, read_json_file, getNodesFromGraph, read_info_file

DATASET = '2l_cvrp_0/E016-03m.dat'
#DATASET = '2l_cvrp_0/E051-05e.dat'
#DATASET = 'homberger_200_customer_instances/C1_2_1.TXT'

DATASET = '../datasets/' + DATASET

os.chdir('./runs/')

def optimize(tour, GRAPH):

	subtours = []
	i = 0
	while i < len(tour)-1 :
		subtours.append([tour[i]])
		i+=1
		while i < len(tour) and tour[i].id != 0:
			subtours[-1].append(tour[i])
			i+=1

	critical_index = 0
	withPenalty = True
	timeDistance = 0
	edgeDistance = -1
	subtourIndex = -1
	for index in range(len(subtours)):
		subtour = subtours[index]
		if len(subtour) == 2:
			critical_index += 2
			continue

		for i in range(len(subtour)):
			if subtour[i].servedAt == subtour[i].start_time and subtour[i-1].id != 0 and subtour[i-1].servedAt + \
			 GRAPH[subtour[i].id][subtour[i-1].id]['distance'] < subtour[i].start_time:
				withPenalty = False
				timeDistance = subtour[i].start_time - subtour[i-1].servedAt
				edgeDistance = GRAPH[subtour[i].id][subtour[i-1].id]['distance']
				subtourIndex = index
				break
			else:
				critical_index += 1

		if not withPenalty:
			break

	if critical_index >= len(tour)-1:
		return
	else:

		nearestDepot = critical_index-2
		while NODES[DEPOT] != tour[nearestDepot]:
			nearestDepot -= 1

		if timeDistance - edgeDistance > 30:
			timeDistance = 30
		else:
			timeDistance -= edgeDistance

		for i in range(len(tour[nearestDepot+1:critical_index])):
			tour[nearestDepot+1+i].servedAt += timeDistance

		rest_of_the_tour = []
		for subtour in subtours[subtourIndex+1:]:
			for elem in subtour:
				rest_of_the_tour.append(elem)

		if len(rest_of_the_tour) > 1:
			rest_of_the_tour.append(tour[-1])
			optimize(rest_of_the_tour, GRAPH)
			tour[-len(rest_of_the_tour):] = rest_of_the_tour

		return

def fixTimestamps(sol, GRAPH, NODES, DEPOT):
	for vehicle in sol:
		time = 0
		list_of_penalties = []
		for i in range(len(vehicle.tour)-1):
			distance = GRAPH[vehicle.tour[i].id][vehicle.tour[i+1].id]['distance']

			if vehicle.tour[i+1] == NODES[DEPOT]:
				distance -= 5
				time += distance
				vehicle.tour[i+1].servedAt = time

			elif time + distance > vehicle.tour[i+1].end_time:
				print("Solution not feaseble")
				return

			elif time + distance <= vehicle.tour[i+1].start_time:
				list_of_penalties.append(vehicle.tour[i+1].id)
				time = vehicle.tour[i+1].start_time
			else:
				time += distance

			vehicle.tour[i+1].servedAt = time
		optimize(vehicle.tour, GRAPH)


def evaluateSolution(vehicles, graph, NODES, verbose=False):
	return sum([Vehicle.tourCost(vehicle.tour, graph, NODES, verbose=verbose) for vehicle in vehicles])

#Effettua lo scambio dei nodi e poi cerca di capire se la soluzione che salta fuori è effettivamente feaseble
def swapIsPossible(tour1, index1, tour2, index2, GRAPH, DEPOT, NODES):
	tour1_copy = deepcopy(tour1)
	tour2_copy = deepcopy(tour2)
	tour1_copy[index1], tour2_copy[index2] = tour2_copy[index2], tour1_copy[index1]
	tours = [tour1_copy, tour2_copy]
	for tour in tours:
		time = 0
		capacity = 3
		for i in range(len(tour)-1):
			distance = GRAPH[tour[i].id][tour[i+1].id]['distance']

			if tour[i+1] == NODES[DEPOT]:
				capacity = 3
				distance -= 5
			else:
				capacity -= 1

			if not (time + distance <= tour[i+1].end_time):
				return False

			elif  time + distance < tour[i+1].start_time:
				time = tour[i+1].start_time

			else:
				time += distance

	return True

if __name__ == '__main__':

	NVEHICLES = None 
	CAPACITY = None
	DEPOT = None
	NODES = None
	g = None
	graphfile = ''
	infofile = ''
	if DATASET.lower().find('.txt') > 0:
		graphfile = DATASET.lower().replace('.txt', '.graph')
		infofile = DATASET.lower().replace('.txt', '.info')

	elif DATASET.lower().find('.dat') > 0:
		graphfile = DATASET.lower().replace('.dat', '.graph')
		infofile = DATASET.lower().replace('.dat', '.info')

	print(f'graphfile: {graphfile}')

	try:
		g = read_json_file(graphfile)
		NODES = getNodesFromGraph(g)
		NVEHICLES, CAPACITY, DEPOT = read_info_file(infofile)

	except FileNotFoundError:
		print("The specified file does not exists")
		exit()

	#number of iteration
	iteration = 0

	#initialize all the vehicles to the depot
	VEHICLES = [Vehicle(vehicleId=i, NODES=NODES) for i in range(NVEHICLES)]
	toVisit = deepcopy(NODES[:DEPOT] + NODES[DEPOT+1:])

	print("############## Initial solution algorithm ##############")

	# regret per costruire
	while(len(toVisit) != 0):
		iteration+=1
		maximumEndTime = max(toVisit, key=lambda node: node.end_time)
		maximumEndTime = maximumEndTime.end_time
		solutionIsPossible = False

		list_regret = []
		possible_node_list = []
		grouped_list = []
		for vehicle in VEHICLES:
			if len(vehicle.servableNodes) > 0:
				solutionIsPossible = True
			else:
				if vehicle.getLastPosition() != NODES[DEPOT]:
					vehicle.tourAppend(deepcopy(NODES[DEPOT]), g, NODES)

				while(vehicle.time < maximumEndTime and len(vehicle.servableNodes) == 0):
					vehicle.wait(g, NODES)
					
			if vehicle.time < maximumEndTime:
				solutionIsPossible = True
				for possibleNode in vehicle.servableNodes:
					if possibleNode in toVisit:
						possible_node_list += [(vehicle.costVisit(possibleNode['nodeId'], g), vehicle.id, possibleNode['nodeId'])]
						solutionIsPossible = True
						print("Iteration " + str(iteration) + ": vehicle " + str(vehicle.id) + " (time " + str(vehicle.time) + ") can visit " + str(possibleNode['nodeId']) + " (deliver time window: " + str(possibleNode['start_time']) + "  to " + str(possibleNode['end_time']) + ") with cost " + str(vehicle.costVisit(possibleNode['nodeId'], g)))

		if len(possible_node_list) != 0:
			set_of_nodes = set(map(lambda x:x[2], possible_node_list))
			grouped_list = [[elem for elem in possible_node_list if elem[2]==node] for node in set_of_nodes]
			for possible_node_list in grouped_list:
				if len(possible_node_list) > 1:
					possible_node_list.sort(key=lambda x: x[0])
					if max(possible_node_list[:2], key=lambda x: x[0]) == min(possible_node_list[:2], key=lambda x: x[0]):
						chosen_one = random.choice(possible_node_list[:2])
						chosen_tuple = (0, chosen_one[1], chosen_one[2])
						list_regret += [chosen_tuple]
						print(f'The 2 best paths that can reach node {chosen_tuple[2]} can do it at the same cost. A random vehicle will be selected and regret cost is 0 -> vehicle {chosen_tuple[1]}')
					else:
						list_regret += [(possible_node_list[1][0] - possible_node_list[0][0], possible_node_list[0][1], possible_node_list[0][2])]
						print(f'For node {possible_node_list[0][2]} the two most efficent paths come from vehicle {possible_node_list[0][1]} at cost {possible_node_list[0][0]} and {possible_node_list[1][1]} at cost {possible_node_list[1][0]}. So regret is {list_regret[-1][0]}')
				else:
									#regret cost 				   vehicle id 					 node id
					list_regret += [(possible_node_list[0][0], possible_node_list[0][1], possible_node_list[0][2])]
					print(f'For node {possible_node_list[0][2]} the most efficent path come come from vehicle {possible_node_list[0][1]} at cost {possible_node_list[0][0]}. So regret is {list_regret[-1][0]} ')

		#Try to understand if it is still possible to find a feaseble solution
		if len(list_regret) == 0 and len(toVisit) != 0:
			for vehicle in VEHICLES:
				vehicle.getServableNodes(g, NODES)
				if len(vehicle.servableNodes) == 0:
					if vehicle.getLastPosition() != NODES[DEPOT]:
						vehicle.tourAppend(deepcopy(NODES[DEPOT]), g, NODES)

					while(vehicle.time < maximumEndTime and len(vehicle.servableNodes) == 0):
						vehicle.wait(g, NODES)
					
					if vehicle.time < maximumEndTime:
						solutionIsPossible = True

			if solutionIsPossible is False:
				print("Solution not possible")

		else:
			list_regret.sort(reverse=True)
			choosen_tuple = random.choice(list_regret[:5])
			choosenNodeId = choosen_tuple[2]
			choosenVehicle = choosen_tuple[1]
			VEHICLES[choosenVehicle].tourAppend(NODES[choosenNodeId], g, NODES)
			print("regret cost, vehicle id, node id")
			for elem in list_regret:
				print(f'{elem[0]} {elem[1]} {elem[2]}')

			print(f'Choosen vehicle: {choosenVehicle}, choosen node: {choosenNodeId}')

			drawSolution(VEHICLES, g, "Iteration " + str(iteration) + " vehicle " + str(choosenVehicle) + " choosen", save=True, path='/'.join(DATASET.split('/')[2:]), subpath='/construction_algorithm')
			NODES[choosenNodeId].served = True
			for vehicle in VEHICLES:
				vehicle.getServableNodes(g, NODES)
			toVisit.remove(NODES[choosenNodeId])
			list_regret = []

	for vehicle in VEHICLES:
		if vehicle.getLastPosition() != NODES[DEPOT]:
			vehicle.tourAppend(deepcopy(NODES[DEPOT]), g, NODES)

	print()
	print("############## Local Search ##############")

	sol = VEHICLES
	GRAPH = g
	verbose = True

	iteration = 0

	improvement = True
	while improvement == True:
		iteration += 1
		improvement = False
		#								Time gained, vehicle1 index, vehicle1 tour index, vehicle2 index, vehicle2 tour index
		# this array will contain tuples like (0,			-1, 			-1, 				-1, 				-1)
		possible_moves = list()
		for vehicle1 in sol:
			for vehicle2 in sol:
				if vehicle1.id < vehicle2.id:
					print("Current vehicles:")
					print(vehicle1.id)
					print(vehicle1.tour)
					print(vehicle2.id)
					print(vehicle2.tour)
					tour1 = deepcopy(vehicle1.tour)
					tour2 = deepcopy(vehicle2.tour)
					lastDepot1 = 0
					lastDepot2 = 0
					for node1, index1 in zip(tour1, range(len(tour1))):
						if node1 != NODES[DEPOT]:
							for node2, index2 in zip(tour2, range(len(tour2))):
								if node2 != NODES[DEPOT]:
									# if is possible this func returns True
									if swapIsPossible(tour1, index1, tour2, index2, GRAPH, DEPOT, NODES):
										print(f"swap between {node1.id} form vehicle1 and {node2.id} form vehicle2 is possible:")

										dummyTour1 = deepcopy(tour1)
										dummyTour2 = deepcopy(tour2)
										dummyTour1[index1], dummyTour2[index2] = dummyTour2[index2], dummyTour1[index1]

										object1 = type('', (), {})()
										object2 = type('', (), {})()
										object1.tour = dummyTour1
										object1.id = vehicle1.id
										object2.tour = dummyTour2
										object2.id = vehicle2.id
										fixTimestamps([object1, object2], GRAPH, NODES, DEPOT)
										#			  OldTour											  		  - NewTour
										delta_time1 = Vehicle.tourCost(vehicle1.tour, GRAPH, NODES, DEPOT, False) - Vehicle.tourCost(object1.tour, GRAPH, NODES, DEPOT, False)
										delta_time2 = Vehicle.tourCost(vehicle2.tour, GRAPH, NODES, DEPOT, False) - Vehicle.tourCost(object2.tour, GRAPH, NODES, DEPOT, False)
										time_gained = delta_time1 + delta_time2

										print(f"Time gained: {time_gained}")
										tmp_sol = [vehicle for vehicle in sol if vehicle.id != vehicle1.id and vehicle.id != vehicle2.id]
										tmp_sol.append(object1)
										tmp_sol.append(object2)
										tmp_sol.sort(key=lambda e: e.id)
										drawSolution(tmp_sol, g, f'Iteration {iteration}. Swap between {node1.id} form vehicle {vehicle1.id} and {node2.id} form vehicle {vehicle2.id}', save=True, path='/'.join(DATASET.split('/')[2:]), subpath=f'/local_search/iteration_{iteration}/possible_moves')
										drawSolution(sol, g, f'Current Solution', save=True, path='/'.join(DATASET.split('/')[2:]), subpath=f'/local_search/iteration_{iteration}/possible_moves')
										
										if time_gained > 0:
											possible_moves.append((time_gained, vehicle1, object1.tour, vehicle2, object2.tour))
											improvement = True

										tour1 = deepcopy(vehicle1.tour)
										tour2 = deepcopy(vehicle2.tour)
									else:
										print(f"swap between {node1.id} form vehicle1 and {node2.id} form vehicle2 is not possible.")
			print()	

		if improvement:
			possible_moves.sort(key=lambda tup: tup[0], reverse=True)
			vehicle_is_updated = dict((elem.id, False) for elem in sol)
			if verbose:
				print(f"Solution now is {evaluateSolution(sol, GRAPH, NODES)}")
			time_gained = 0
			for possibleMove in possible_moves:
				if not vehicle_is_updated[possibleMove[1].id] and not vehicle_is_updated[possibleMove[3].id]:

					time_gained += possibleMove[0]
					vehicle1Index = possibleMove[1].id
					for elem1, elem2 in zip(sol[vehicle1Index].tour, possibleMove[2]):
						if elem1.id != elem2.id:
							print(f'Swap between {elem1.id} from vehicle {vehicle1Index} ', end='')
							break
					sol[vehicle1Index].tour = possibleMove[2]

					vehicle2Index = possibleMove[3].id
					for elem1, elem2 in zip(sol[vehicle2Index].tour, possibleMove[4]):
						if elem1.id != elem2.id:
							print(f'and {elem1.id} from vehicle {vehicle2Index} ')
							break
					sol[vehicle2Index].tour = possibleMove[4]
					vehicle_is_updated[vehicle1Index] = True
					vehicle_is_updated[vehicle2Index] = True
					print(f'Time gained: {possibleMove[0]}')

			if verbose:
				print(f"Total time gained: {time_gained}. Now solution is evaluated {evaluateSolution(sol, GRAPH, NODES)}")
			print()

	print(f"Finished: solution is {evaluateSolution(sol, GRAPH, NODES)}")
	drawSolution(sol, g, f'Final Solution {evaluateSolution(sol, GRAPH, NODES)}' , save=True, path='/'.join(DATASET.split('/')[2:]))
