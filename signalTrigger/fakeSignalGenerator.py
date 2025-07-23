import redis, sched, time

# Connecting to the redis database 
r = redis.Redis(host="192.168.222.233", password="redisRacs233", port=6379,decode_responses=True)

# Checking connection
if r.ping() == True:
    print("Connection with the REDIS database established.")
else:
    print("ERROR: Connection to the REDIS database was not established. Quitting.")
    quit()
    
n=0
offsetTime = 2/1e9
while n < 2:
    
    triggerTime = float(time.clock_gettime_ns(time.CLOCK_REALTIME))/1e18
    triggerTime = triggerTime + offsetTime
    print(triggerTime)

    r.set(f"trigger_{triggerTime}", triggerTime)
    r.expire(f"trigger_{triggerTime}", 3)	# Trigger signal expires after 10 seconds 
    n = n + 1
    time.sleep(0.3)

r.close()
