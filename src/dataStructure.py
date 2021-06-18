from copy import deepcopy


class Node():

	def __init__(self, nodeId=0, coords=tuple([0, 0]), start_time=0, end_time=0, service_time=0, demand=0):
		'''nodeId=0, coords=(0, 0), start_time=0, end_time=0, demand=0'''
		self.id = nodeId
		self.coords = coords
		self.start_time = start_time
		self.end_time = end_time
		self.service_time = service_time
		self.demand = demand
		self.served = False
		self.servedAt = -1

	def isServed(self):
		return self.served is True and self.servedAt < self.end_time

	def createFromGraphNode(**kwargs):
		"""print("Kwargs")
		print(kwargs)"""
		return Node(kwargs['nodeId'], kwargs['pos'], kwargs['start_time'], 
					kwargs['end_time'], kwargs['service_time'], kwargs['demand'])

	def __repr__(self):
		return self.__str__()
	
	def __str__(self):
		if self.id == 0:
			return f' (DEOPT) '
		if self.served:
			return f' (node {self.id}, served at {self.servedAt}, window: {self.start_time} {self.end_time}) '
		else:
			return f' (node {self.id}, location: {self.coords}, not served,  window: {self.start_time} {self.end_time}) '

	def __hash__(self):
		return self.id

	def __eq__(self, other):
		if type(other) == type(dict()):
			return self.id == other['nodeId']

		return self.id == other.id

class Vehicle():

	def __init__(self, vehicleId=0, NODES=None, DEPOT=0, CAPACITY=3):
		self.id = vehicleId
		self.position = [NODES[DEPOT]] if NODES else None
		self.capacity = CAPACITY
		self.time = 0
		self.tour = [NODES[DEPOT]] if NODES else None
		self.servableNodes = []

	def getLastPosition(self):
		return self.tour[-1]

	def tourAppend(self, node, graph, NODES, DEPOT=0, checkUpdates=True):
		if self.capacity == 0 and node is not NODES[DEPOT]:
			print('Capacity exceeded')
			return False

		to_depot = True if node == NODES[DEPOT] else False
		if not checkUpdates:
			print(f"get last position: {self.getLastPosition().id}, node.id: {node.id}")
		added_time = graph.get_edge_data(self.getLastPosition().id, node.id)['distance']
		if to_depot is True:
			added_time -= 5

		if self.time + added_time <= node.end_time:
			self.tour.append(node)
			#if we arrived too soon, we wait until start time
			if self.time + added_time <= node.start_time:
				self.time = node.start_time
			else:
				self.time += added_time

			node.servedAt = self.time
			if to_depot:
				self.capacity = 3
			else:
				self.capacity -= 1
				node.served = True
				graph.nodes[node.id]['served'] = True

				if self.capacity == 0:
					self.time += (graph[node.id][DEPOT]['distance']-5)
					self.tour.append(deepcopy(NODES[DEPOT]))
					self.tour[-1].servedAt = self.time
					self.capacity = 3

			self.position = self.getLastPosition()
			if checkUpdates:
				self.servableNodes = self.getServableNodes(graph, NODES)
			return True

		else:
			#print(f'Tour append for {self} not valid')
			return False

	def isServable(arrivalTime, graphNode):
		return graphNode['served'] is False and graphNode['start_time'] <= arrivalTime <= graphNode['end_time']

	def getServableNodes(self, graph, NODES, DEPOT=0):
		possibleEdges = graph.adj[self.getLastPosition().id]

		#print(possibleEdges)
		servableNodes = []
		for key in possibleEdges.keys():
			if graph.nodes[key]['served'] != NODES[key].served and key != DEPOT:
				print(f'Ho trovato un nodo del grafo Vehicle che non è in linea con NODES')
				print(f'{graph.nodes[key]} e {NODES[key]}')
				exit()
			if key != DEPOT and graph.nodes[key]['served'] == False:
				arrivalNodeId = key
				arrivalTime = possibleEdges[key]['distance'] + self.time
				arrivalNode = graph.nodes[arrivalNodeId]
				if Vehicle.isServable(arrivalTime, arrivalNode):
					servableNodes.append(arrivalNode)

		self.servableNodes = servableNodes
		return servableNodes

	def wait(self, graph, NODES, time=1, DEPOT=0):
		if self.getLastPosition() == NODES[DEPOT]:
			self.time += time
			self.servableNodes = self.getServableNodes(graph, NODES)
		else:
			print('Illegal wait')

	def costVisit(self, node, graph):
		if isinstance(node, int):
			return graph.get_edge_data(self.getLastPosition().id, node)['distance']
		return graph.get_edge_data(self.getLastPosition().id, node.id)['distance']

	def tourCost(tour, graph, NODES, DEPOT=0, verbose=False):
		if len(tour) > 0:
			cost = sum( graph[node1.id][node2.id]['distance'] for node1, node2 in zip(tour[:-1], tour[1:]))
			penalties = 0

			for i in range(len(tour)):
				#coming back to the depot you don't pay 5 minutes for the delivery
				if tour[i] == NODES[DEPOT]:
					cost-=5

				elif tour[i-1] != NODES[DEPOT] and tour[i-1].servedAt + graph[tour[i-1].id][tour[i].id]['distance'] < tour[i].start_time:
					penalty = ((tour[i].start_time - (tour[i-1].servedAt + graph[tour[i-1].id][tour[i].id]['distance'])) / 2.0)**2
					penalties += penalty
					#print(f'Passage from {tour[i-1].id} to {tour[i].id} generated {penalty} penalty')

				#else:
				#	penalties += ((tour[i].servedAt + graph[tour[i].id][tour[i+1].id]['distance']) - tour[i+1].start_time)

			if verbose:
				if penalties > 0:
					print(f"Tour cost: {cost + penalties}, tour lenght: {cost}, penalties: {penalties}")
			return cost + penalties
		else:
			return 0

	def __repr__(self):
		return self.__str__()
	
	def __str__(self):
		return f'vehicle id: {self.id}, time: {self.time}, current capacity: {self.capacity}, position: ({self.position})'
