from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import json

# load graph from json file and return series of graph-related variables
def init_graph(file_path, graph_num):
	graph_obj = json.loads(open(file_path,'r').read())
	graph_obj = graph_obj["graph" + graph_num]
	adjacency_list = graph_obj['diagraphModel']['adjacencyList']
	edges = graph_obj['diagraphModel']['edges']
	nodes = graph_obj['diagraphModel']['nodes']
	depiction_level = graph_obj['diagraphView']['depictionLevel']

	# remove all parents except one fron 'nodes' for coordinate-generation purposes
	for node in nodes:
		while len(nodes[node]["parent"]) > 1:
			par = nodes[node]["parent"].pop()
			nodes[par]["child"].remove(node)

	return (graph_obj, edges, nodes, adjacency_list, depiction_level)

# conduct depth-first traversal of graph to build list of childless nodes
def build_childless_list(l, present_node, nodes):
	# base case: if list is empty, simply add node
	if nodes[present_node]["child"] == []:
		l.append(present_node)
	else:
		for node in nodes[present_node]["child"]:
			if int(nodes[present_node]["_level"]) < int(nodes[node]["_level"]):
				build_childless_list(l, node, nodes)

# generate x-coordinates given adjacency_list and H
def generate_x_coordinates(depiction_level, H):
	inith = 0.0
	x_coord_dict = defaultdict(set)
	for level in depiction_level:
		for node in depiction_level[level]:
			n1 = len(depiction_level[level])
			x_coord_dict[node] = inith + (n1-1)*H
		inith += n1 * H

	return x_coord_dict

# adjust y-coordinates for proximity
def adjust_proximity(y_coord_dict, nodes, edges, mode = 'vertical'):
	for edge in edges:
		node1, node2 = edge.split("::")
		proxim = edges[edge]["proximity"]
		if proxim:
			# distance between the centres of the two nodes
			if mode == 'horizontal':
				dist = (nodes[node1]["height"] + nodes[node2]["height"]) / 2
			if mode == 'vertical':
				dist = (nodes[node1]["width"] + nodes[node2]["width"]) / 2 
			if y_coord_dict[node1] < y_coord_dict[node2]:
				y_coord_dict[node2] = y_coord_dict[node1] + dist
			elif y_coord_dict[node1] > y_coord_dict[node2]:
				y_coord_dict[node2] = y_coord_dict[node1] - dist

	return y_coord_dict

# generate y-coordinates given depiction_level, nodes, edges, childless_list and V
def generate_y_coordinates(nodes, edges, depiction_level, childless_list, V, mode='vertical'):
	n = len(depiction_level)
	y_coord_dict = defaultdict(set)

	# set equally spaced y-coords for childless nodes: shadow points
	n1 = len(childless_list)
	Y_MAX = (n1//2) * V
	y_coords = list(np.linspace(-Y_MAX, Y_MAX, num = n1))
	for i in range(n1):
		node = childless_list[i]
		y_coord_dict[node] = y_coords[i]

	# based on positions of childless nodes, take averages of children to get y-coordinates of parent nodes
	for i in range(n-2,-1,-1):
		current_layer = depiction_level[str(i)]
		for node in current_layer:
			if node not in y_coord_dict:
				y_children = [y_coord_dict[i] for i in nodes[node]["child"] if i not in current_layer]
				y_coord_dict[node] = np.mean(y_children)

	y_coord_dict = adjust_proximity(y_coord_dict, nodes, edges, mode)

	return y_coord_dict

# generate all coordinates
def generate_coordinates(nodes, edges, depiction_level, childless_list, mode = 'vertical'):
	n = len(depiction_level) 
	coord_dict = defaultdict(set)

	# set V, H based on max height, width of nodes
	maxHeight = 5
	maxWidth = 10
	for node in nodes:
		if nodes[node]["height"] > maxHeight:
			maxHeight = nodes[node]["height"]
		if nodes[node]["width"] > maxWidth:
			maxWidth = nodes[node]["width"]

	if mode == 'horizontal':
		V = maxHeight*3/4
		H = max(2*V, maxWidth)
	if mode == 'vertical':
		V = maxWidth*3/4
		H = max(2*V, maxHeight)
	
	x_coord_dict = generate_x_coordinates(depiction_level, H)
	y_coord_dict = generate_y_coordinates(nodes, edges, depiction_level, childless_list, V)

	for node in x_coord_dict:
		if mode == 'horizontal':
			coord_dict[node] = (x_coord_dict[node], y_coord_dict[node])
		if mode == 'vertical':
			coord_dict[node] = (y_coord_dict[node], -x_coord_dict[node])

	return coord_dict

# generates desired graph from given graph, coordinates
def plot_coord_graph(adjacency_list, depiction_level, coord_dict, nodes, mode='vertical'):
	fig = plt.figure()
	ax = fig.add_subplot(111)

	# plot nodes
	for node in coord_dict:
		height, width = nodes[node]["height"], nodes[node]["width"]
		startx = coord_dict[node][0] - width/2
		starty = coord_dict[node][1] - height/2
		ax.add_patch( Rectangle((startx, starty), width, height, fc='b', ec='black', lw=0.5) )
		if mode == 'vertical':
			ax.annotate(node, (startx+width/2, starty-height))
		if mode == 'horizontal':
			ax.annotate(node, (startx+width/2, starty+height))

	# generate list of edges
	edge_list = []
	for cons in list(adjacency_list.values()):
		for i in cons:
			node1, node2 = i.split('::')
			edge_list.append((node1, node2))

	# plot arrows between connections, parent to child
	for node1, node2 in edge_list:
		x,y = coord_dict[node1]
		x1,y1 = coord_dict[node2][0], coord_dict[node2][1]
		posx, posy = (x+x1)/2, (y+y1)/2
		y_step = 0.05 * (y1-y)
		x_step = 0.05 * (x1-x)
		line = plt.plot([x,x1],[y,y1],color='black')[0]
		#plt.arrow(posx, posy, x_step, y_step, shape='full', length_includes_head=True, head_width=0.001)
		line.axes.annotate("", xy=(posx+x_step,posy+y_step), xytext=(posx, posy), arrowprops=dict(arrowstyle="-|>"))

	# show graph
	plt.show()

def main():
	# input file_path and graph_num
	file_path = input("Enter graph file path: ")
	graph_num = input("Enter graph number: ")
	# load graph
	graph_obj, edges, nodes, adjacency_list, depiction_level = init_graph(file_path, graph_num)

	# build childless_list
	childless_list = []
	for i in depiction_level["0"]:
		build_childless_list(childless_list, i, nodes)

	mode = input("Enter view (vertical/horizontal): ")
	coord_dict = generate_coordinates(nodes, edges, depiction_level, childless_list, mode)

	# plot graph
	plot_coord_graph(adjacency_list, depiction_level, coord_dict, nodes, mode)

main()