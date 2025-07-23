import redis, sched, time
from multiprocessing import Pool, TimeoutError
import random

def retrieveTime():
    now = float(time.clock_gettime_ns(time.CLOCK_REALTIME))
    return now/1e9

def triggerRead(triggerTime):
    #print(f"[triggerRead] Trigger time: {triggerTime}")
    currentTime = retrieveTime()
    print(f"Read triggered with error: {triggerTime - currentTime}")

def schedulerSetup(triggerTime):
    
    #print(f"[schedulerSetup] Trigger time: {triggerTime}")
    # Setting up a scheduler class
    s = sched.scheduler(timefunc=retrieveTime, delayfunc=time.sleep)
    
    s.enterabs(time=triggerTime, priority=10, action=triggerRead, argument=(triggerTime,))
    s.run()
                
                

def f(x):
    return x*x

with Pool(processes=10) as pool:
    # Trigger time 1 sec from now
    triggerTime = float(time.clock_gettime_ns(time.CLOCK_REALTIME))/1e9 + 0.3 + random.random()
    
    res = pool.apply_async(schedulerSetup, (triggerTime,))

    
    for i in range(0,30):
        triggerTime = float(time.clock_gettime_ns(time.CLOCK_REALTIME))/1e9 + random.random()
    
        res = pool.apply_async(schedulerSetup, (triggerTime,))
    
    time.sleep(2)
    
    
    #res.get(timeout = 2)
    #while True:
    #    try:
    #        res.ready()
    #        print(f"Process successful: {res.successful()}")
            
    #    except:
    #        continue
    #   time.sleep(0.5)
    
