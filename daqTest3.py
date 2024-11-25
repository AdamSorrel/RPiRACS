#!/home/signal/Programs/daqEnv/bin/python
#
# MCC 118 example program
# Read and display analog input values
#

import sys, os, sched, time, json, redis
from daqhats import hat_list, HatIDs, OptionFlags, mcc128, AnalogInputMode, AnalogInputRange
from sys import stdout
from time import sleep, perf_counter
import numpy as np

sys.path.append("/home/signal/Programs/daqhats/examples/python/mcc128/")

from daqhats_utils import chan_list_to_mask

READ_ALL_AVAILABLE = -1

CURSOR_BACK_2 = '\x1b[2D'
ERASE_TO_END_OF_LINE = '\x1b[0K'

class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def main():
	# Connecting to the REDIS database
	r = redis.Redis(host="192.168.222.233",password="redisRacs233",port=6379,decode_responses=True)
	if r.ping():
		print("Connection with the REDIS database established.")
	else:
		print("ERROR: Connection to REDIS was not established. Quitting.")
		quit()
	
	# get hat list of MCC daqhat boards
	board_list = hat_list(filter_by_id = HatIDs.ANY)
	if not board_list:
		print("No boards found")
		sys.exit()

	# Loading the board class
	# Only set up for 1 board
	entry = board_list[0]
	print(f"Connected device: {entry.product_name}")
	if entry.id == HatIDs.MCC_128:    
		board = mcc128(entry.address)
	else:
		print("Error: Board not recognized.")
		sys.exit()

	board.blink_led(3)

	print(f"Last calibration date: {board.calibration_date()}")

	print(f"Actual read frequency: {board.a_in_scan_actual_rate(3, 10000)} Hz")

	channels = [0,1,2]
	channelMask = chan_list_to_mask(channels)
	scanRate = 10000.0
	samplesPerChannel = 10000

	# Single ended mode
	#input_mode = AnalogInputMode.SE
	# Differential mode
	input_mode = AnalogInputMode.DIFF

	input_range = AnalogInputRange.BIP_10V

	board.a_in_mode_write(input_mode)
	board.a_in_range_write(input_range)

	# Starting scan
	board.a_in_scan_start(channel_mask = channelMask, samples_per_channel = samplesPerChannel, sample_rate_per_channel = scanRate, options=OptionFlags.CONTINUOUS)

	# Display the header row for the data table.
	print('Samples Read', end='')
	for chan, item in enumerate(channels):
		print('    Channel ', item, sep='', end='')
	print('    Delta time ', end='')
	#print('    ActualTime ', end='')
	print('')

	try:
		read_and_display_data(board, len(channels),r)
			
			
			 
	except KeyboardInterrupt:
		# Clear the '^C' from the display.
		print(CURSOR_BACK_2, ERASE_TO_END_OF_LINE, '\n')
		print('Stopping')
		board.a_in_scan_stop()
		board.a_in_scan_cleanup()

def retrieveTime():
	#now = float(time.time_ns())
	now = float(time.clock_gettime_ns(time.CLOCK_REALTIME))
	return now / 1e9	# Returning time in seconds

        
def read_and_display_data(hat, num_channels, r):
	"""
	Reads data from the specified channels on the specified DAQ HAT devices
	and updates the data on the terminal display.  The reads are executed in a
	loop that continues until the user stops the scan or an overrun error is
	detected.

	Args:
		hat (mcc128): The mcc128 HAT device object.
		num_channels (int): The number of channels to display.

	Returns:
		None

	"""
	total_samples_read = 0
	read_request_size = READ_ALL_AVAILABLE

	# When doing a continuous scan, the timeout value will be ignored in the
	# call to a_in_scan_read because we will be requesting that all available
	# samples (up to the default buffer size) be returned.
	timeout = 5.0

	# Read all of the available samples (up to the size of the read_buffer which
	# is specified by the user_buffer_size).  Since the read_request_size is set
	# to -1 (READ_ALL_AVAILABLE), this function returns immediately with
	# whatever samples are available (up to user_buffer_size) and the timeout
	# parameter is ignored.
	s = sched.scheduler(timefunc=retrieveTime, delayfunc=time.sleep)
	requestedTime = retrieveTime()
	
	while True:
		requestedTime = requestedTime + 0.1

		s.enterabs(time=requestedTime,priority=10,action=readVoltages, argument=(read_request_size, timeout, hat, num_channels, total_samples_read, requestedTime,r))
		s.run(blocking=True)

	print('\n')


def readVoltages(read_request_size, timeout, hat, num_channels, total_samples_read, requestedTime,r):
	# First retrieving time. The idea is to prepend time measurement to 
	# the package and calculate timing from that. 
	# Retrieving data takes an unpredictable and irregular amount of time, 
	# which makes calculation of time stamps unprecise. 
	currentTime = retrieveTime()
	
	read_result = hat.a_in_scan_read(read_request_size, timeout)
	# currentTime = retrieveTime()

	# Check for an overrun error
	if read_result.hardware_overrun:
		print('\n\nHardware overrun\n')
		quit()
	elif read_result.buffer_overrun:
		print('\n\nBuffer overrun\n')
		quit()
	
	encodedData = json.dumps(np.array(read_result.data), cls=NumpyArrayEncoder)
	
	r.set(f"data_{currentTime}", encodedData)
	r.expire(f"data_{currentTime}", time=3)   # Value will expire after 3 seconds    

	samples_read_per_channel = int(len(read_result.data) / num_channels)
	total_samples_read += samples_read_per_channel

	# Display the last sample for each channel.
	print('\r{:12}'.format(samples_read_per_channel), end='')

	if samples_read_per_channel > 0:
		index = samples_read_per_channel * num_channels - num_channels

		for i in range(num_channels):
			print('{:10.5f}'.format(read_result.data[index+i]), 'V ', end='')
		print(' {:10.5f}'.format(requestedTime-currentTime), end = '')
		#print(' {:10.5f}'.format(currentTime), end = '')
		stdout.flush()

if __name__ == '__main__':
    main()
