# RPiRACS
Raspberry Pi support files for the RACS system. The system is deployed on multiple Raspberry Pi platform, which are synchronized using PTP protocol. One of the RPi devices functions as a grandmaster clock with an arbitrary time. This means that it is not synchronized with any external time source. This time is distributed to all other RPi devices. 

Furthermore, the grandmaster clock is also running a REDIS database, which is a quick, non-SQL database system, gathering all the timestamps DAQ data and potentially other data streams. This system is periodically polled by all devices for new requested time stamps. Hosting REDIS database is not supported on Windows and thus cannot be deployed on the main Windows machine. 

DAQ device is pusing acquired data to the REDIS database, whereupon they are polled by the main (Windows) computer. They are visualized for the user, peaks are analyzed and particle speed is predicted. This data is used to predict a future position of the particle, which is an information used for other peripherals, such as Raman detector. 
