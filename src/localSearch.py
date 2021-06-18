from copy import deepcopy
import random

from src.dataStructure import *

def initialSolution(param_graph, param_capacity, param_depot, param_nodes, param_nvehicles):
	CAPACITY = deepcopy(param_capacity)
	DEPOT = deepcopy(param_depot)
	NODES = deepcopy(param_nodes)
	NVEHICLES = deepcopy(param_nvehicles)
	g = deepcopy(param_graph)

	toVisit = deepcopy(NODES[:DEPOT] + NODES[DEPOT+1:])
	maximumEndTime = max(toVisit, key=lambda n: n.end_time)
	maximumEndTime = maximumEndTime.end_time

	if maximumEndTime > 240:
		print(f"Qualcosa è andato storto con l'assegnamento delle finestre non ha funzionato {maximumEndTime}")
		exit()

	#initialize all the vehicles to the depot
	VEHICLES = [Vehicle(vehicleId=i, NODES=NODES) for i in range(NVEHICLES)]

	# regret per costruire
	while(len(toVisit) != 0):
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
					else:
						list_regret += [(possible_node_list[1][0] - possible_node_list[0][0], possible_node_list[0][1], possible_node_list[0][2])]
				else:
									#regret cost 				   vehicle id 					 node id
					list_regret += [(possible_node_list[0][0], possible_node_list[0][1], possible_node_list[0][2])]

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
				return (None, None)

		else:
			list_regret.sort(reverse=True)
			choosen_tuple = random.choice(list_regret[:5])
			choosenNodeId = choosen_tuple[2]
			choosenVehicle = choosen_tuple[1]
			VEHICLES[choosenVehicle].tourAppend(NODES[choosenNodeId], g, NODES)
			NODES[choosenNodeId].served = True
			for vehicle in VEHICLES:
				vehicle.getServableNodes(g, NODES)
			toVisit.remove(NODES[choosenNodeId])
			list_regret = []

	for vehicle in VEHICLES:
		if vehicle.getLastPosition() != NODES[DEPOT]:
			vehicle.tourAppend(deepcopy(NODES[DEPOT]), g, NODES)

	param_graph = g
	param_nodes = NODES
	return VEHICLES

def optimize(tour, GRAPH, NODES, DEPOT):

	subtours = []
	i = 0
	while i < len(tour)-1 :
		subtours.append([tour[i]])
		i+=1
		while i < len(tour) and tour[i] != NODES[DEPOT]:
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
			if subtour[i].servedAt == subtour[i].start_time and subtour[i-1] !=  NODES[DEPOT] and subtour[i-1].servedAt + \
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
			optimize(rest_of_the_tour, GRAPH, NODES, DEPOT)
			tour[-len(rest_of_the_tour):] = rest_of_the_tour

		return

def fixTimestamps(sol, GRAPH, NODES, DEPOT, optmized=True):
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

		if optmized:
			optimize(vehicle.tour, GRAPH, NODES, DEPOT)

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
			# tour[i+1].start_time
			if not (time + distance <= tour[i+1].end_time):
				return False

			elif  time + distance < tour[i+1].start_time:
				time = tour[i+1].start_time

			else:
				time += distance

	return True

def swap(sol, GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES, verbose=False, optmized=True):
	
	improvement = True
	while improvement == True:
		improvement = False
		#								Time gained, vehicle1 index, vehicle1 tour index, vehicle2 index, vehicle2 tour index
		# this array will contain tuples like (0,			-1, 			-1, 				-1, 				-1)
		possible_moves = list()
		for vehicle1 in sol:
			for vehicle2 in sol:
				if vehicle1.id < vehicle2.id:
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

										dummyTour1 = deepcopy(tour1)
										dummyTour2 = deepcopy(tour2)
										dummyTour1[index1], dummyTour2[index2] = dummyTour2[index2], dummyTour1[index1]

										object1 = type('', (), {})()
										object2 = type('', (), {})()
										object1.tour = dummyTour1
										object1.id = vehicle1.id
										object2.tour = dummyTour2
										object2.id = vehicle2.id
										fixTimestamps([object1, object2], GRAPH, NODES, DEPOT, optmized=optmized)
										#			  OldTour											  		  - NewTour
										delta_time1 = Vehicle.tourCost(vehicle1.tour, GRAPH, NODES, DEPOT, False) - Vehicle.tourCost(object1.tour, GRAPH, NODES, DEPOT, False)
										delta_time2 = Vehicle.tourCost(vehicle2.tour, GRAPH, NODES, DEPOT, False) - Vehicle.tourCost(object2.tour, GRAPH, NODES, DEPOT, False)
										time_gained = delta_time1 + delta_time2
										
										if time_gained > 0:
											possible_moves.append((time_gained, vehicle1, object1.tour, vehicle2, object2.tour))
											improvement = True

										tour1 = deepcopy(vehicle1.tour)
										tour2 = deepcopy(vehicle2.tour)

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
					sol[vehicle1Index].tour = possibleMove[2]
					vehicle2Index = possibleMove[3].id
					sol[vehicle2Index].tour = possibleMove[4]
					vehicle_is_updated[vehicle1Index] = True
					vehicle_is_updated[vehicle2Index] = True

			if verbose:
				print(f"Tempo guadagnato in totale {time_gained}. Ora la sol vale {evaluateSolution(sol, GRAPH, NODES)}")

	#fixTimestamps(sol, GRAPH, NODES, DEPOT)

def evaluateSolution(vehicles, graph, NODES, verbose=False):
	return sum([Vehicle.tourCost(vehicle.tour, graph, NODES, verbose=verbose) for vehicle in vehicles])

def printSolution(solution, graph=None, nodes=None, depot=None):

	print('Vehicles: \n')
	for vehicle in solution:
		print(f'Vehicle {vehicle.id}, final time at {vehicle.time}: ')
		for node, i in zip(vehicle.tour[:-1], range(len(vehicle.tour))):
			print(f'node {node.id}, start time {node.start_time}, visited at {node.servedAt}, end time {node.end_time}', ' ')
			nextNode = vehicle.tour[i+1]
			distance = graph[node.id][nextNode.id]['distance']
			if nextNode == nodes[depot]:
				distance -= 5
			print(f'link of distance {distance}')

		node = vehicle.tour[-1]
		print(f'node {node.id}, start time {node.start_time}, visited at {node.servedAt}, end time {node.end_time}', ' ')
		print()

def localSearch(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES):

	counter = 0
	sol = (None, None)
	maxAttempts = 3
	while sol == (None, None) and counter <= maxAttempts:
		counter += 1
		sol = initialSolution(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES)

	if counter > maxAttempts:
		return (None, None, None)

	initialValue = evaluateSolution(sol, GRAPH, NODES, verbose=False)
	print(f'Initial solution value: {initialValue} after {counter} attempts')

	print("Process in swap")
	swap(sol, GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES)
	finalValue = evaluateSolution(sol, GRAPH, NODES, verbose=False)

	return (sol, finalValue, initialValue)


def vanillaLocalSearch(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES):

	counter = 0
	sol = (None, None)
	maxAttempts = 3
	while sol == (None, None) and counter <= maxAttempts:
		counter += 1
		sol = initialSolution(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES)

	if counter > maxAttempts:
		return (None, None, None)

	initialValue = evaluateSolution(sol, GRAPH, NODES, verbose=False)
	print(f'Initial solution value: {initialValue} after {counter} attempts')

	print("Process in swap")
	swap(sol, GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES, optmized=False)
	finalValue = evaluateSolution(sol, GRAPH, NODES, verbose=False)

	return (sol, finalValue, initialValue)


def comparisonBetweenVanillaOptimized(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES, nComp=100):

	print("Be careful, call this comparison on small graphs, otherwise execution time will be high")
	optimized_counter = 0
	vanilla_counter = 0
	vanilla_improvement = 0
	optimized_improvement = 0
	draw_counter = 0
	solution_optimized = 0
	solution_vanilla = 0
	for _ in range(nComp):
		print(f"try number {_+1}: ")
		counter = 0
		sol = (None, None)
		maxAttempts = 3
		while sol == (None, None) and counter <= maxAttempts:
			counter += 1
			sol = initialSolution(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES)

		if counter > maxAttempts:
			continue

		initialValue = evaluateSolution(sol, GRAPH, NODES, verbose=False)

		optimized_sol = deepcopy(sol)
		vanilla_sol = deepcopy(sol)
		swap(vanilla_sol, GRAPH, CAPACITY, DEPOT, deepcopy(NODES), NVEHICLES, optmized=False)
		swap(optimized_sol, GRAPH, CAPACITY, DEPOT, deepcopy(NODES), NVEHICLES, optmized=True)
		vanilla_value = evaluateSolution(vanilla_sol, GRAPH, NODES, verbose=False)
		opt_value = evaluateSolution(optimized_sol, GRAPH, NODES, verbose=False)

		if vanilla_value > opt_value:
			optimized_counter += 1
			
		elif vanilla_value < opt_value:
			vanilla_counter += 1
		else:
			draw_counter += 1

		solution_vanilla += vanilla_value
		solution_optimized += opt_value

		vanilla_improvement += initialValue - vanilla_value
		optimized_improvement += initialValue - opt_value

		print(f'Optimized: {opt_value}, Vanilla: {vanilla_value}')

	print(f'On average Vanilla method produces a solution of {solution_vanilla*1.0/nComp}')
	print(f'On average Optimized method produces a solution of {solution_optimized*1.0/nComp}')
	
	print(f'On average Vanilla method improves the initial solution of {vanilla_improvement*1.0/nComp} points')
	print(f'On average Optimized method improves the initial solution of {optimized_improvement*1.0/nComp} points')

	print(f'Vanilla method won {vanilla_counter} times')
	print(f'Optimized method won {optimized_counter} times')


	if draw_counter > 0:
		print(f'The methods are even in {draw_counter} attempts')

	return optimized_counter