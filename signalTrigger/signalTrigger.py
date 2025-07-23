import redis, sched, time, sys
import gpiod
from gpiod.line import Direction, Value
from multiprocessing import Pool, TimeoutError

POOL_SIZE = 10

# Trigger pins are the two last pins, closest to the fan power source
# The inner is ground (pin 39) and the outer is trigger (pin 40 or GPIO21)
TRIGGER_PIN=21
TRIGGER_PIN1=20
TRIGGER_PIN2=26
TRIGGER_PIN3=16

def retrieveTime():
    now = float(time.clock_gettime_ns(time.CLOCK_REALTIME))
    return now/1e9

def triggerRead(triggerPin, triggerTime, triggerData):
    currentTime = retrieveTime()
    if abs(triggerTime - currentTime) > 0.01:
        print(print(f"[schedulerWorker/triggerRead] Trigger error too high: {triggerTime - currentTime}"))
    else:
        triggerPin.set_value(TRIGGER_PIN, Value.INACTIVE)
        time.sleep(0.01)    # Sleep for 10 ms aka. exposure time!
        triggerPin.set_value(TRIGGER_PIN, Value.ACTIVE)
        #print(f"Triggered read with incoming data: {triggerData}, error: {triggerTime - currentTime}")
        print(f"[schedulerWorker/triggerRead] Trigger error: {currentTime - triggerTime}")

def schedulerWorker(triggerTime, triggerData):
    # Setting up a scheduler class
    s = sched.scheduler(timefunc=retrieveTime, delayfunc=time.sleep)
    #currentTime = retrieveTime()
    #while (triggerTime - currentTime) > 0.01:
    try:
        with gpiod.request_lines("/dev/gpiochip4", 
                                consumer="raman-trigger", 
                                config={
                                TRIGGER_PIN:	gpiod.LineSettings(
                                                direction=Direction.OUTPUT, 
                                                output_value=Value.ACTIVE
                                                )
                                        },
                                 ) as triggerPin:
        
            s.enterabs(time=triggerTime, priority=10, action=triggerRead, argument=(triggerPin, triggerTime, triggerData))
            s.run()
    except OSError as e:
        print(f"[schedulerWorker] OSError: {e}")
    except Exception as e:
        print(f"[schedulerWorker] An exception of type {type(e).__name__} occurred: {str(e)}")
        #time.sleep(0.05)
        #currentTime = retrieveTime()
        #currentTime = 0
    

# Starting redis server
r = redis.Redis(host="192.168.222.233", password="redisRacs233", port=6379,decode_responses=True)
# Checking connection
if r.ping() == True:
    print("Connection with the REDIS database established.")
else:
    print("ERROR: Connection to the REDIS database was not established. Quitting.")
    quit()

# Deleting all previous old entries from database
r.flushdb()

# Setting up the GPIO chip
if not gpiod.is_gpiochip_device("/dev/gpiochip4"):
    print("ERROR: Cannot connect to the GPIO chip. Quitting")
    quit()


with Pool(processes=10) as pool:
    while True:
        try:
            for trigger in r.scan_iter(match="trigger_*"):
                triggerData = r.get(trigger)
                # Clearing up processed triggers
                triggerTime = float(trigger.split("_")[1])
                triggerTime = triggerTime*1e9
                currentTime = retrieveTime()
                timeUntilTrigger = triggerTime-currentTime
                #print(f"Time until trigger: {timeUntilTrigger}")
                if timeUntilTrigger < 0.001:
                    #print(f"Trigger is nigh for trigger {trigger}")
                    # If time until trigger is lower than 100 ms, triggering read threat, which is blocking.
                    #s.enterabs(time=triggerTime, priority=10, action=triggerRead, argument=(r, triggerPin, triggerTime, triggerData))
                    #s.run(blocking=False)
                    
                    pool.apply_async(schedulerWorker, (triggerTime, triggerData))
                    r.delete(trigger)
                #else:
                #    print(f"Skipping trigger because it came too late. Time until trigger: {timeUntilTrigger}")
                #print("*************************")
            time.sleep(0.001)
            
        except KeyboardInterrupt:
            print("Stopping")
            # Cancelling all upcoming events
            #for event in s.queue:
            #    s.cancel(event)
            # Terminating all processess running in pool
            pool.terminate()
            pool.join()
            print("All worker processess terminated. Exitting program.")
            sys.exit(0)
            #quit()
