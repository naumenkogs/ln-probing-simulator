#! /usr/bin/python3

'''
This file is part of Lightning Network Probing Simulator.

Copyright © 2020-2021 University of Luxembourg

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all
	copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
	SOFTWARE.

SPDX-FileType: SOURCE
SPDX-FileCopyrightText: 2020-2021 University of Luxembourg
SPDX-License-Identifier: MIT
'''

'''
	Auxiliary operations with the LN graph.
'''

from hop import Hop, dir0, dir1

import networkx as nx
import json


class Channel:
	def __init__(self, source, destination, capacity, dir0_enabled, dir1_enabled):
		self.source = source
		self.destination = destination
		self.capacity = capacity
		self.dir0_enabled = dir0_enabled
		self.dir1_enabled = dir1_enabled


def create_multigraph_from_snapshot(snapshot_filename):
	'''
		Create a NetworkX multigraph from a clightning's listchannels.json snapshot.
		Multigraph means each edge corresponds to an edge (parallel edges allowed).

		Parameters:
		- snapshot_filename: path to the snapshot

		Return: the multigraph (the maximal connected component only).
	'''
	print("Creating LN graph from file:", snapshot_filename, "...")
	with open(snapshot_filename, 'r') as snapshot_file:
		network = json.load(snapshot_file)
	edges_set, nodes_set = set(), set()
	edges, channels = [], dict()
	# cid -> Channel
	for channel_direction in network["channels"]:
		cid = channel_direction["short_channel_id"]
		direction = channel_direction["source"] < channel_direction["destination"]
		if direction == dir0:
			source = channel_direction["source"]
			destination = channel_direction["destination"]
		else:
			source = channel_direction["destination"]
			destination = channel_direction["source"]
		if cid not in channels:
			#print("creating new channel for", cid)
			dir0_enabled, dir1_enabled = (channel_direction["active"], False) if direction == dir0 else (False, channel_direction["active"])
			channel = Channel(source, destination, channel_direction["satoshis"], dir0_enabled, dir1_enabled)
			channels[cid] = channel
		else:
			#print("updating existing channels for", cid)
			channel = channels[cid]
			if direction == dir0:
				channel.dir0_enabled = channel_direction["active"]
			else:
				channel.dir1_enabled = channel_direction["active"]
	# count how many uni-directional channels we have
	num_bidirectional = sum([1 for cid in channels if channels[cid].dir0_enabled and channels[cid].dir1_enabled ])
	print("Total channels:", len(channels))
	print("Bidirectional channels:", num_bidirectional)
	for cid in channels:
		channel = channels[cid]
		edges.append((channel.source, channel.destination, cid,
			{
			"capacity": channel.capacity,
			"dir0_enabled": channel.dir0_enabled,
			"dir1_enabled": channel.dir1_enabled,
			}))
		edges_set.add(cid)
		nodes_set.add(source)
		nodes_set.add(destination)
	nodes = list(nodes_set)
	g = nx.MultiGraph()
	g.add_nodes_from(nodes)
	g.add_edges_from(edges)
	print("LN snapshot contains:", g.number_of_nodes(), "nodes,", g.number_of_edges(), "channels.")
	# continue with the largest connected component
	components = sorted(nx.connected_components(g), key=len, reverse=True)
	print("Components:", len(components), ". Continuing with the largest component.")
	def connected_component_subgraphs(G):
		# https://github.com/rkistner/chinese-postman/issues/21#issuecomment-568980233
		for c in nx.connected_components(G):
			yield G.subgraph(c)
	# create a new MultiGraph to unfreeze
	g = nx.MultiGraph(max(connected_component_subgraphs(g), key=len))
	print("LN graph created with", g.number_of_nodes(), "nodes,", g.number_of_edges(), "channels.")
	return g, len(channels)


def ln_multigraph_to_hop_graph(ln_multigraph):
	'''
		Generate a hopgraph from an LN multigraph.
		A hopgraph doesn't allow parallel edges.
		Instead, parallel channels are encoded in edge attributes.

		Parameters:
		- ln_multigraph: LN model multigraph

		Return:
		- hop_graph: a non-directed graph where each edge models a hop
	'''
	hop_graph = nx.Graph()
	# initialize hop graph with nodes and empty edge attributes
	for n1, n2 in ln_multigraph.edges():
		hop_graph.add_nodes_from([n1, n2])
		hop_graph.add_edge(n1, n2)
	for n1, n2, k, d in ln_multigraph.edges(keys=True, data=True):
		multi_edge = ln_multigraph[n1][n2]
		cids = [cid for cid in multi_edge]
		capacities, e_dir0, e_dir1 = [], [], []
		for i, cid in enumerate(cids):
			capacities.append(multi_edge[cid]["capacity"])
			if multi_edge[cid]["dir0_enabled"]:
				e_dir0.append(i)
			if multi_edge[cid]["dir1_enabled"]:
				e_dir1.append(i)
		hop_graph[n1][n2]["hop"] = Hop(capacities, e_dir0, e_dir1)
	return hop_graph

	