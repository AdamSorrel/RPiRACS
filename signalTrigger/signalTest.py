import redis, sched, time
import gpiod
from gpiod.line import Direction, Value

# Trigger pins are the two last pins, closest to the fan power source
# The inner is ground (pin 39) and the outer is trigger (pin 40 or GPIO21)
TRIGGER_PIN=21  


def triggerRead(r, triggerPin, triggerTime, triggerData):
    currentTime = retrieveTime()
    triggerPin.set_value(TRIGGER_PIN, Value.INACTIVE)
    time.sleep(0.05)    # Sleep for 50 ms
    triggerPin.set_value(TRIGGER_PIN, Value.ACTIVE)
    print(f"Triggered read with incoming data: {triggerData}, error: {triggerTime - currentTime}")



# Setting up the GPIO chip
if not gpiod.is_gpiochip_device("/dev/gpiochip4"):
    print("ERROR: Cannot connect to the GPIO chip. Quitting")
    quit()
    
triggerPin = gpiod.request_lines("/dev/gpiochip4", 
                                 consumer="raman-trigger", 
                                 config={
                                     TRIGGER_PIN:   gpiod.LineSettings(
                                                    direction=Direction.OUTPUT, 
                                                    output_value=Value.ACTIVE
                                                    )
                                 },
                                )

while True:
    try:
        triggerPin.set_value(TRIGGER_PIN, Value.ACTIVE)
        print("Trigger pin is UP, trigger value is DOWN")
        time.sleep(3)
        triggerPin.set_value(TRIGGER_PIN, Value.INACTIVE)
        print("Trigger pin is DOWN, trigger value is UP")
        time.sleep(3)

    except KeyboardInterrupt:
        print("Stopping")
        # Cancelling all upcoming events
        quit()
