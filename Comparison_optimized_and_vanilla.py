from src.dataStructure import *
from src.utils import *
from src.localSearch import comparisonBetweenVanillaOptimized

################## DATASET SELECTION ##################

#DATASET = 'homberger_200_customer_instances/C1_2_1.TXT'
#DATASET = 'homberger_200_customer_instances/C1_2_2.TXT'
#DATASET = 'homberger_200_customer_instances/C2_2_1.TXT'
#DATASET = 'homberger_200_customer_instances/R1_2_1.TXT'
#DATASET = 'homberger_200_customer_instances/R2_2_1.TXT'
#DATASET = 'homberger_200_customer_instances/RC1_2_1.TXT'
#DATASET = 'homberger_200_customer_instances/RC2_2_1.TXT'
#DATASET = 'homberger_400_customer_instances/C1_4_1.TXT'
#DATASET = '2l_cvrp_0/E016-03m.dat'
#DATASET = '2l_cvrp_0/E021-04m.dat'
#DATASET = '2l_cvrp_0/E022-04g.dat'
#DATASET = '2l_cvrp_0/E023-03g.dat'
#DATASET = '2l_cvrp_0/E026-08m.dat'
#DATASET = '2l_cvrp_0/E031-09h.dat'
#DATASET = '2l_cvrp_0/E033-03N.dat'
DATASET = '2l_cvrp_0/E036-11h.dat'
#DATASET = '2l_cvrp_0/E041-14h.dat'
#DATASET = '2l_cvrp_0/E076A10r.dat'

## da qui in poi serve aumentare i veicoli
#DATASET = '2l_cvrp_0/E200-17b.dat'

################## GLOBAL VARIABLES AND FUNCTIONS ##################

DATASET = 'datasets/' + DATASET

################## MAIN PROCEDURE ##################

if __name__ == '__main__':

	global DEPOT
	global NVEHICLES
	global CAPACITY
	global NODES 
	global VEHICLE_SPEED
	global GRAPH

	graphfile = ''
	infofile = ''
	if DATASET.lower().find('.txt') > 0:
		graphfile = DATASET.lower().replace('txt', 'graph')
		infofile = DATASET.lower().replace('txt', 'info')

	elif DATASET.lower().find('.dat') > 0:
		graphfile = DATASET.lower().replace('.dat', '.graph')
		infofile = DATASET.lower().replace('.dat', '.info')

	print(f'graphfile: {graphfile}')

	try:
		GRAPH = read_json_file(graphfile)
		NODES = getNodesFromGraph(GRAPH)
		NVEHICLES, CAPACITY, DEPOT = read_info_file(infofile)
		#VEHICLE_SPEED = calculateSpeed(calculateDistancesFromDepot(NODES))

	except FileNotFoundError:
		# crea il grafo partendo dal dataset indicato. Calcola la velocità adatta al dataset. Crea una distribuzione normale centrata a 120 minuti 
		# e l'assegna come start_time/end_time. Una volta fatto ciò, salva il problema così creato come un nuovo graphfile, 
		# con lo stesso nome del dataset indicato ma con estensione .graph
		if DATASET.find('homberger') >= 0:
			CAPACITY, DEPOT, NODES, NVEHICLES = hombergerParser(DATASET)
		elif DATASET.find('2l_cvrp_0') >= 0:
			CAPACITY, DEPOT, NODES, NVEHICLES = l_vrpParser(DATASET)

		print(f'capacity: {CAPACITY}, depot: {DEPOT}, node number: {len(NODES)}, nvehicles: {NVEHICLES}')
		CAPACITY = 3
		DEPOT = 0

		''' Carpi si percorre da parte a parte in macchina in un quarto d'ora. La distanza MEDIA dal depot deve essere di 7.5 minuti e la massima di 15 min
			per far si che sia vero viene chiamata questa funzione per calcolare la velocità adatta'''
		VEHICLE_SPEED = calculateSpeed(calculateDistancesFromDepot(NODES))
		assignTimeWindow(NODES, False)
		data = json_graph.node_link_data(createGraph(NODES))
		with open(graphfile, 'w') as outfile:
			json.dump(data, outfile)

		with open(infofile, 'w') as outfile:
			outfile.write(str(NVEHICLES))
			outfile.write(" ")
			outfile.write(str(CAPACITY))
			outfile.write(" ")
			outfile.write(str(DEPOT))

		GRAPH = createGraph(NODES)
		pos = {node:(x, y) for (node, (x, y)) in nx.get_node_attributes(GRAPH, 'pos').items()}
		nx.draw_networkx(GRAPH, pos, with_labels=True)
		plt.axis('equal')
		plt.title('grafo letto da file')
		plt.show()

	counter = comparisonBetweenVanillaOptimized(GRAPH, CAPACITY, DEPOT, NODES, NVEHICLES, nComp=100)

	print(f'Optimized method won {counter} times')