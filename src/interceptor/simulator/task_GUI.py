# Emulated Interceptor GUI Receiver
# Connects PULL socket to tcp://localhost:PORT
# Collects and prints data from a data processing pipeline 
# over the socket determined by PORT..
#
# Useful for debugging to check that a data processing
# pipeline is actually sending over the channel.
#

import sys
import time
import zmq

#Connection port to feeding process
PORT=5557

#Sleep time between collection attempts
SLEEP_S = 0

#Print all frames?
#PRINT_ALL = False
PRINT_ALL = True
PRINT_DELIM = "***************************************************"

#Print Interval in frames
PRINT_INT_FRAMES = 500

#Choose PUSH-PULL or PUB_SUB
USE_PUSH_PULL = False
GUI_TOPIC = "gui"


context = zmq.Context()

# Socket to receive messages on
if USE_PUSH_PULL:
    receiver = context.socket(zmq.PULL)
    receiver.connect("tcp://localhost:{}".format(PORT))
    receiver.bind("tcp://*:{}".format(PORT))
else:
    receiver = context.socket(zmq.SUB)
    #receiver.connect("tcp://localhost:{}".format(PORT))
    receiver.connect("tcp://127.0.1.1:{}".format(PORT)) #DEBUG
    topic_token = GUI_TOPIC
    receiver.setsockopt(zmq.SUBSCRIBE,topic_token.encode('utf-8'))

if USE_PUSH_PULL:
    print("ZMQ Pattern PUSH-PULL\n")
else:
    print("ZMQ Pattern PUB-SUB\n")


fps_counter = 0
fps_time_start = time.time()
# Process tasks forever
while True:
    s = receiver.recv_string()
    if not USE_PUSH_PULL:
        s = s[(len(GUI_TOPIC)+1):]


    if PRINT_ALL:
        #For high frame rates it's a bad idea
        sys.stdout.write("Rx: " + s + "\n")
        sys.stdout.flush()
        pass

    fps_counter += 1
    if fps_counter % PRINT_INT_FRAMES == 0:
        deltaT = time.time() - fps_time_start
        sys.stdout.write("FPS:{:.2f}\n".format(fps_counter/deltaT))
        if not PRINT_ALL:
            sys.stdout.write("Rx: \"" + s + "\"\n" + PRINT_DELIM + "\n")
        sys.stdout.flush()
        fps_time_start = time.time()
        fps_counter = 0

    # Do the work
    time.sleep(SLEEP_S)

