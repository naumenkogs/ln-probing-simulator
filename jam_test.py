#! /usr/bin/python3

import argparse
import time
import matplotlib.pyplot as plt

from scipy.ndimage.filters import gaussian_filter1d

from experiments import experiment_1, experiment_2, experiment_3, experiment_4
from prober import Prober
from random import sample

SNAPSHOT_FILENAME = "./snapshots/listchannels-2021-12-09.json"
ENTRY_CHANNEL_CAPACITY = 10_000_000
ENTRY_NODES = [
	"02ad6fb8d693dc1e4569bcedefadf5f72a931ae027dc0f0c544b34c1c6f3b9a02b",
	"03864ef025fde8fb587d989186ce6a4a186895ee44a926bfc370e2c366597a3f8f",
	"0217890e3aad8d35bc054f43acc00084b25229ecff0ab68debd82883ad65ee8266",
	"0331f80652fb840239df8dc99205792bba2e559a05469915804c08420230e23c7c",
	"0242a4ae0c5bef18048fbecf995094b74bfb0f7391418d71ed394784373f41e4f3",
	"03bb88ccc444534da7b5b64b4f7b15e1eccb18e102db0e400d4b9cfe93763aa26d",
	"03abf6f44c355dec0d5aa155bdbdd6e0c8fefe318eff402de65c6eb2e1be55dc3e",
	"02004c625d622245606a1ea2c1c69cfb4516b703b47945a3647713c05fe4aaeb1c",
	"0395033b252c6f40e3756984162d68174e2bd8060a129c0d3462a9370471c6d28f",
	"0390b5d4492dc2f5318e5233ab2cebf6d48914881a33ef6a9c6bcdbb433ad986d0"
]

def main():
	part_entry_nodes = sample(ENTRY_NODES, 3)
	TOTAL_CAPACITY = 3270

	# prober = Prober(SNAPSHOT_FILENAME, "PROBER", part_entry_nodes, ENTRY_CHANNEL_CAPACITY)
	# resuling_success_rates3 = experiment_3(prober)
	# channels_locked_percent3 = [round(data[0] * 100.0 / prober.n_channels) for data in resuling_success_rates3]
	# amount_locked_percent3 = [round(data[1] * 100.0 / TOTAL_CAPACITY) for data in resuling_success_rates3]
	# x_data3 = amount_locked_percent3
	# payment_successes_percent3 = [round(data[2] * 100.0) for data in resuling_success_rates3]
	# plt.plot(x_data3, payment_successes_percent3, label = 'Jam random channels')

	# prober = Prober(SNAPSHOT_FILENAME, "PROBER", part_entry_nodes, ENTRY_CHANNEL_CAPACITY)
	# resuling_success_rates4 = experiment_4(prober)
	# channels_locked_percent4 = [round(data[0] * 100.0 / prober.n_channels) for data in resuling_success_rates4]
	# amount_locked_percent4 = [round(data[1] * 100.0 / TOTAL_CAPACITY) for data in resuling_success_rates4]
	# x_data4 = amount_locked_percent4
	# payment_successes_percent4 = [round(data[2] * 100.0) for data in resuling_success_rates4]
	# plt.plot(x_data4, payment_successes_percent4, label = 'Jam top channels (by slots)')

	# prober = Prober(SNAPSHOT_FILENAME, "PROBER", part_entry_nodes, ENTRY_CHANNEL_CAPACITY)
	# resuling_success_rates4 = experiment_4(prober, top_for_slot_jamming=False)
	# channels_locked_percent4 = [round(data[0] * 100.0 / prober.n_channels) for data in resuling_success_rates4]
	# amount_locked_percent4 = [round(data[1] * 100.0 / TOTAL_CAPACITY) for data in resuling_success_rates4]
	# x_data4 = amount_locked_percent4
	# payment_successes_percent4 = [round(data[2] * 100.0) for data in resuling_success_rates4]
	# plt.plot(x_data4, payment_successes_percent4, label = 'Jam top channels (by amounts)')

	# plt.xlabel('Jammed amount, %')
	# plt.ylabel('Payment success rate, %')
	# plt.title("How jamming affects the ability of LN to forward payments?")
	# plt.legend(loc="upper left")
	# plt.show()

	prober = Prober(SNAPSHOT_FILENAME, "PROBER", part_entry_nodes, ENTRY_CHANNEL_CAPACITY)
	print(prober.estimate_rebalance_and_jam())




if __name__ == "__main__":
	start_time = time.time()
	main()
	end_time = time.time()
	print("Completed in", round(end_time - start_time), "seconds.")
