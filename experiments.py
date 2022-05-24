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
	Run experiments as described in the paper.
'''

import statistics

from synthetic import generate_hops, probe_hops_direct
from hop import Hop
from plot import plot


def experiment_1(prober, num_target_hops, num_runs_per_experiment, min_num_channels, max_num_channels):
	'''
		Measure the information gain and probing speed for direct and remote probing.

		Generate or choose target hops with various number of channels.
		Probe the target hops in direct and remote mode (if prober is provided), using BS and NBS amount choice methods.
		Measure and plot the final achieved information gain and probing speed.

		Parameters:
		- prober: the Prober object (None to run only direct probing on synthetic hops)
		- num_target_hops: how many target hops to choose / generate
		- num_runs_per_experiments: how many experiments to run (gain and speed are averaged)
		- min_num_channels: the minimal number of channels in hops to consider
		- max_num_channels: the maximal number of channels in hops to consider
		- use_snapshot:
			if False, run only direct probing on synthetic hops; 
			if True, run direct and remote probing on synthetic and snapshot hops.
		- jamming: use jamming (after h and g are fully probed without jamming)

		Return: None (saves the resulting plots)
	'''

	print("\n\n**** Running experiment 1 ****")

	BITCOIN = 100*1000*1000
	MIN_CAPACITY_SYNTHETIC = 0.01 	* BITCOIN
	MAX_CAPACITY_SYNTHETIC = 10 	* BITCOIN
	NUM_CHANNELS_IN_TARGET_HOPS = [n for n in range(min_num_channels, max_num_channels + 1)]
	# Hops with 5+ channels are very rare in the snapshot.

	def run_one_instance_of_experiment_1(jamming, remote_probing, bs):
		'''
			Run experiment for all numbers of channels with one parameter set.
			Yields two lines on two graphs: gains and speeds.
		'''
		gains 	= [0 for _ in range(len(NUM_CHANNELS_IN_TARGET_HOPS))]
		speeds 	= [0 for _ in range(len(NUM_CHANNELS_IN_TARGET_HOPS))]
		for i, num_channels in enumerate(NUM_CHANNELS_IN_TARGET_HOPS):
			#print("\n\nN = ", num_channels)
			gain_list, speed_list = [], []
			for num_experiment in range(num_runs_per_experiment):
				#print("  experiment", num_experiment)
				if prober is not None:
					# pick target hops from snapshot, probe them in direct and remote modes
					target_hops_node_pairs = prober.choose_target_hops_with_n_channels(num_target_hops, num_channels)
					target_hops = [prober.lnhopgraph[u][v]["hop"] for (u,v) in target_hops_node_pairs]
				else:
					# generate target hops, probe them in direct mode
					target_hops = generate_hops(num_target_hops, num_channels, MIN_CAPACITY_SYNTHETIC, MAX_CAPACITY_SYNTHETIC)
				#print("Selected" if prober is not None else "Generated", len(target_hops), "target hops with", num_channels, "channels.")
				if remote_probing:
					assert(prober is not None)
					gain, speed = prober.probe_hops(target_hops_node_pairs, bs=bs, jamming=jamming)
				else:
					gain, speed = probe_hops_direct(target_hops, bs=bs, jamming=jamming)
				gain_list.append(gain)
				speed_list.append(speed)
			gains[i] = gain_list
			speeds[i] = speed_list
		# prepare data for information gains plot
		remote_or_direct = "Remote" if remote_probing else "Direct"
		bs_or_nbs = "non-optimized" if bs else "optimized"
		colors = ["blue", "purple", "red", "orange"]
		color = (colors[3] if bs else colors[2]) if remote_probing else (colors[1] if bs else colors[0])
		lines = ["-", "--", "-.", ":"]
		line = (lines[3] if bs else lines[2]) if remote_probing else (lines[1] if bs else lines[0])
		gains_line = (gains, remote_or_direct + " probing", 
			"-" if not remote_probing else "-.", "blue" if not remote_probing else "red")
		speed_line = (speeds, remote_or_direct + ", " + bs_or_nbs, line, color)
		return gains_line, speed_line
	def run_and_store_result(gains_all_lines, speed_all_lines, pos, jamming, remote_probing, bs):
		gains_line, speed_line = run_one_instance_of_experiment_1(jamming, remote_probing, bs)
		if pos % 2 == 0:
			gains_all_lines[pos // 2] = gains_line
		speed_all_lines[pos] = speed_line
	from multiprocessing import Process, Manager
	procs = []
	manager = Manager()
	y_gains_lines_vanilla = manager.list([0 for _ in range(2)])
	y_gains_lines_jamming = manager.list([0 for _ in range(2)])
	y_speed_lines_vanilla = manager.list([0 for _ in range(4)])
	y_speed_lines_jamming = manager.list([0 for _ in range(4)])
	for i, jamming in enumerate((False, True)):
		for j, remote_probing in enumerate((False, True)):
			for k, bs in enumerate((False, True)):
				gains_results = y_gains_lines_jamming if jamming else y_gains_lines_vanilla
				speed_results = y_speed_lines_jamming if jamming else y_speed_lines_vanilla
				pos = 2 * j + k
				proc = Process(target=run_and_store_result, args=(gains_results, speed_results, pos, jamming, remote_probing, bs, ))
				procs.append(proc)
				proc.start()
	for proc in procs:
		proc.join()
	targets_source = "snapshot" if prober is not None else "synthetic"
	x_label = "\nNumber of channels in target hops\n"
	
	plot(
		x_data 			= NUM_CHANNELS_IN_TARGET_HOPS,
		y_data_lists	= [y_gains_lines_vanilla, y_gains_lines_jamming],
		x_label 		= x_label,
		y_label 		= "Information gain (share of initial uncertainty)\n",
		title			= "",#"Information gain\n",
		filename 		= "gains_" + targets_source)
	plot(
		x_data 			= NUM_CHANNELS_IN_TARGET_HOPS,
		y_data_lists	= [y_speed_lines_vanilla, y_speed_lines_jamming],
		x_label 		= x_label,
		y_label 		= "Probing speed (bits / message)\n", 
		title 			= "",#"Probing speed\n",
		filename 		= "speed_" + targets_source)

	print("\n\n**** Experiment 1 complete ****")


def experiment_2(num_target_hops, num_runs_per_experiment):
	'''
		Measure the information gain and probing speed for different configurations of a 2-channel hop.

		Parameters:
		- num_target_hops: how man target hops to consider
		- num_runs_per_experiment: how many times to run each experiment (results are averaged)

		Return: None (print resulting stats)
	'''

	print("\n\n**** Running experiment 2 ****")

	CAPACITY_BIG = 2**20
	CAPACITY_SMALL = 2**15
	BIG_BIG 	= [CAPACITY_BIG, CAPACITY_BIG]
	BIG_SMALL 	= [CAPACITY_BIG, CAPACITY_SMALL]
	SMALL_BIG	= [CAPACITY_SMALL, CAPACITY_BIG]

	ENABLED_BOTH 	= [0,1]
	ENABLED_FIRST 	= [0]
	ENABLED_SECOND 	= [1]
	ENABLED_NONE 	= []

	def get_hop_2_2():
		return Hop(BIG_BIG, ENABLED_BOTH, ENABLED_BOTH)

	def get_hop_2_2_big_small():
		return Hop(BIG_SMALL, ENABLED_BOTH, ENABLED_BOTH)

	def get_hop_2_2_small_big():
		return Hop(SMALL_BIG, ENABLED_BOTH, ENABLED_BOTH)

	def get_hop_1_1():
		return Hop(BIG_BIG, ENABLED_FIRST, ENABLED_SECOND)

	def get_hop_1_1_big_small():
		return Hop(BIG_SMALL, ENABLED_FIRST, ENABLED_SECOND)

	def get_hop_1_1_small_big():
		return Hop(SMALL_BIG, ENABLED_FIRST, ENABLED_SECOND)

	def get_hop_2_1():
		return Hop(BIG_BIG, ENABLED_BOTH, ENABLED_FIRST)

	def get_hop_2_1_big_small():
		return Hop(BIG_SMALL, ENABLED_BOTH, ENABLED_FIRST)

	def get_hop_2_1_small_big():
		return Hop(SMALL_BIG, ENABLED_BOTH, ENABLED_FIRST)

	def get_hop_2_0():
		return Hop(BIG_BIG, ENABLED_BOTH, ENABLED_NONE)

	def get_hop_2_0_big_small():
		return Hop(BIG_SMALL, ENABLED_BOTH, ENABLED_NONE)

	def get_hop_2_0_small_big():
		return Hop(SMALL_BIG, ENABLED_BOTH, ENABLED_NONE)

	def compare_methods(target_hops):
		gain_bs, 	speed_bs 	= probe_hops_direct(target_hops, bs = True, jamming = False)
		gain_nbs, 	speed_nbs 	= probe_hops_direct(target_hops, bs = False, jamming = False)
		assert(abs((gain_bs-gain_nbs) / gain_nbs) < 0.05), (gain_bs, gain_nbs)
		return gain_nbs, speed_bs, speed_nbs

	all_types = [
	"2_2", "2_2_big_small", "2_2_small_big",
	 "1_1", "1_1_big_small", "1_1_small_big",
	 "2_1", "2_1_big_small", "2_1_small_big", 
	 "2_0", "2_0_big_small", "2_0_small_big"]

	def compare_methods_average(hop_type):
		print("\nHops of type", hop_type)
		if hop_type 	== "2_2":
			get_hop 	= get_hop_2_2
		elif hop_type 	== "2_2_big_small":
			get_hop 	= get_hop_2_2_big_small
		elif hop_type 	== "2_2_small_big":
			get_hop 	= get_hop_2_2_small_big
		elif hop_type 	== "1_1":
			get_hop 	= get_hop_1_1
		elif hop_type 	== "1_1_big_small":
			get_hop 	= get_hop_1_1_big_small
		elif hop_type 	== "1_1_small_big":
			get_hop 	= get_hop_1_1_small_big
		elif hop_type 	== "2_1":
			get_hop 	= get_hop_2_1
		elif hop_type 	== "2_1_big_small":
			print("Big channel enabled in both directions, small channel enabled in one direction")
			get_hop 	= get_hop_2_1_big_small
		elif hop_type 	== "2_1_small_big":
			print("Small channel enabled in both directions, big channel enabled in one direction")
			get_hop 	= get_hop_2_1_small_big
		elif hop_type 	== "2_0":
			get_hop 	= get_hop_2_0
		elif hop_type 	== "2_0_big_small":
			print("Big channel enabled in both directions, small channel enabled in one direction")
			get_hop 	= get_hop_2_0_big_small
		elif hop_type 	== "2_0_small_big":
			print("Small channel enabled in both directions, big channel enabled in one direction")
			get_hop 	= get_hop_2_0_small_big
		else:
			print("Incorrect hop type:", hop_type)
			return
		gain_list, speed_bs_list, speed_nbs_list = [], [], []
		for _ in range(num_runs_per_experiment):
			gain_nbs, speed_bs, speed_nbs = compare_methods([get_hop() for _ in range(num_target_hops)])
			gain_list.append(gain_nbs)
			speed_bs_list.append(speed_bs)
			speed_nbs_list.append(speed_nbs)
		print("Gains (mean):		", 	round(statistics.mean(gain_list),2))
		#print("  stdev:", statistics.stdev(gain_list))
		speed_bs_mean = statistics.mean(speed_bs_list)
		speed_nbs_mean = statistics.mean(speed_nbs_list)
		print("Speed BS (mean):	", round(speed_bs_mean,2))
		#print("  stdev:", statistics.stdev(speed_bs_list))
		print("Speed NBS (mean):	", round(speed_nbs_mean,2))
		#print("  stdev:", statistics.stdev(speed_nbs_list))
		print("Advantage:		", round((speed_nbs_mean-speed_bs_mean)/speed_bs_mean,2))

	for hop_type in all_types:
		compare_methods_average(hop_type)

	print("\n\n**** Experiment 2 complete ****")


def measure_success_rate(prober, targets):
	PAYMENT_AMOUNT = 1_000_000
	max_paths_suggested = 10

	successes = 0
	global_attempts = 0
	for target in targets:
		paths = prober.paths_for_amount(target, PAYMENT_AMOUNT, max_paths_suggested=max_paths_suggested)
		attempts = 0
		while attempts < max_paths_suggested:
			try:
				path = next(paths)
				successes += prober.issue_probe_along_path(path, PAYMENT_AMOUNT)
			except Exception as e:
				break
			attempts += 1
		global_attempts += attempts

	if global_attempts == 0:
		print('all tries failed')
		return 0
	else:
		success_rate = round(successes * 1.0 / global_attempts, 2)
		print('success rate: ', success_rate)
		return success_rate

# Take 100 hops with 2 channels each, and see if any of the paths can forward a given fixed
# amount.
# Then we will do the same, but after jamming some random channels in the network.
def experiment_3(prober):
	num_target_hops = 200
	num_channels = 1
	targets = prober.choose_target_hops_with_n_channels(num_target_hops, num_channels)
	jam_channels_step = 5000
	jammed_channels_total = 0
	jammed_amount_total = 0
	results = []
	for _ in range(20):
		intermediate_result = (jammed_channels_total, jammed_amount_total, measure_success_rate(prober, targets))
		results.append(intermediate_result)
		remaining_targets, jammed_amount = prober.disable_random_channels(jam_channels_step)
		prober.reset_all_estimates()
		jammed_channels_total += (jam_channels_step - remaining_targets)
		jammed_amount_total += jammed_amount
		print('jammed_channels_total: ', jammed_channels_total)
		print('jammed_amount_total: ', jammed_amount_total * 1.0 / 100_000_000)
	print("\n\n**** Experiment 3 complete ****")
	return results

# Take 100 hops with 2 channels each, and see if any of the paths can forward a given fixed
# amount. Then we will do the same, but after jamming top hops in the network.
def experiment_4(prober, top_for_slot_jamming=True):
	num_target_hops = 100
	num_channels = 1
	targets = prober.choose_target_hops_with_n_channels(num_target_hops, num_channels)
	jam_channels_step = 5000
	top_hops = prober.find_top_hops(top_for_slot_jamming)
	print(len(top_hops))
	jammed_channels_total = 0
	jammed_amount_total = 0
	results = []
	for _ in range(20):
		intermediate_result = (jammed_channels_total, jammed_amount_total, measure_success_rate(prober, targets))
		results.append(intermediate_result)
		if len(top_hops) <= 0:
			return results
		top_hops, jammed_amount = prober.disable_hops(top_hops, jam_channels_step)
		prober.reset_all_estimates()
		jammed_channels_total += jam_channels_step
		jammed_amount_total += jammed_amount
		print('jammed_channels_total: ', jammed_channels_total)
		print('jammed_amount_total: ', jammed_amount_total * 1.0 / 100_000_000)
	print("\n\n**** Experiment 4 complete ****")
	return results


