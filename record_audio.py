import pyaudio
import wave
import datetime
import time
import os
from subprocess import Popen, PIPE
import rtmidi_python as rtmidi

CHUNK = 132300
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 1
WAVE_NAME = "output"
WAVE_ENDING = ".wav"

p = pyaudio.PyAudio()


print("* recording")

streams = []
count = 1

next_downbeat_millis = [10000000000000000000000]
bpm = 120
midi_out = rtmidi.MidiOut(b'out')
midi_out.open_port(0)


def callback(in_data, frame_count, time_info, status):

	#print("saving to disk. frame_count is " +str(frame_count))
	frames = []
	frames.append(in_data)

	timestamp = datetime.datetime.now().time()
	timestring = str(timestamp)
	cur_millis = int(round(time.time() * 1000))
	print ('cur_millis is '+str(cur_millis))
	cur_filename = WAVE_NAME + timestring[-12:-10] + '.' + timestring[-9:-5] + WAVE_ENDING
	wf = wave.open(cur_filename, 'wb')#+ str(count)

	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()
	#print("saved to disk")
	cmd = "python3 /Users/Ryan/src/MTFBerlinHack/GMMPatternTracker.py single " + cur_filename
	p_extract = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	stdout, stderr = p_extract.communicate()
	#print("got an std: " +str(stdout))
	stdout_string = stdout.decode()
	lines = stdout_string.split('\n')
	prev_time = -1
	bpms = []
	global next_downbeat_millis
	next_downbeat_millis =[]
	for line in lines:
		print(line)
		if len(line.split('\t')) > 1:
			if prev_time != -1:
				cur_time = float(line.split('\t')[0])
				bpms.append( 60.0 / (cur_time - prev_time))
			prev_time = float(line.split('\t')[0])
		if len(line.split('\t')) > 1 and line.split('\t')[1] == '1':
			#print ('this is the line mothafucka!')
			downbeat_interval_millis =  float(line.split('\t')[0]) * 1000
			#print ('downbeat_interval_millis is '+str(downbeat_interval_millis))
			next_db =cur_millis + downbeat_interval_millis + (CHUNK / RATE * 1000)
			next_downbeat_millis.append(next_db)
			print ('next_downbeat_millis is '+str(next_downbeat_millis))
			print ('difference is '+str(next_db - cur_millis))

	global bpm
	if len(bpms) > 0:
		bpm = sum(bpms) / len(bpms)
	print(bpms)
	print(bpm)
	return (in_data, pyaudio.paContinue)

stream = p.open(format=FORMAT,
				channels=CHANNELS,
				rate=RATE,
				input=True,
				frames_per_buffer=CHUNK,
				stream_callback=callback)

# start the stream (4)
stream.start_stream()

while True:
	cur_millis = int(round(time.time() * 1000))
	for db in next_downbeat_millis:
		if cur_millis > db:
			next_downbeat_millis.remove(db)
			print("DOWNBEAT MOTHERFUCKER!!!!!")
			midi_out.send_message([0x90, 61, bpm])
			midi_out.send_message([0x90, 60, bpm])


stream.stop_stream()
stream.close()


# close PyAudio (7)
p.terminate()
"""count = 10
while count > 0:
	frames = []
	print(datetime.datetime.now().time())
	stream = p.open(format=FORMAT,
					channels=CHANNELS,
					rate=RATE,
					input=True,
					frames_per_buffer=CHUNK)

	for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
		data = stream.read(CHUNK)
		frames.append(data)

	print("* done recording")

	stream.stop_stream()
	stream.close()
	wf = wave.open(WAVE_NAME + str(count) + WAVE_ENDING, 'wb')
	wf.setnchannels(CHANNELS)
	wf.setsampwidth(p.get_sample_size(FORMAT))
	wf.setframerate(RATE)
	wf.writeframes(b''.join(frames))
	wf.close()
	count -= 1
p.terminate()
"""


