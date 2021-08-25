import FSM_Interface as FSMI

"""
### IMPORTANT ###
This is a template for multithreading and controlling the app from custom code
Example: Using external signal sources like from real sensors or just simulating things quickly
Example: Scripted playback from saved files and records
If you don't want to do that just run the main Interface file
If you do want to do that, still better to set up your saves using the GUI normally
"""

# Creates the thread object and opens app
# external=True launches in multi-thread mode
# directory='' means wherever the app .py file is, else supply your own location
# file=f preloads a saved file on launch. Don't use it otherwise for a blank screen
t = FSMI.Main(external=True, directory='', file='FSM_save Binary div_by_five.txt')
# Use .main on the thread object to reach app functions

# Creates a thread object for blocking tasks like start()
### IMPORTANT ### Only one blocking function at a time!
FSMI.Fun(t.main, "start('Zero')") # start(str) starts run mode where str is starting node. Case sensitive & limit 1!
#t.main.stop() # Returns to edit mode and kills the thread object above

t.main.display('Running preset...') # Sets the run display
bins = '01010111001001101110031111000010110' # Notice there's a bad signal in here! It's ignored but recorded
for i in bins:
    #t.main.send(i) # Sends a signal. Returns 0 on success, -1 on failure, -2 if not running
    print(i, t.main.send(i))
print(t.main.get_active()) # Gets active state's name (make sure they're unique if you want this meaningful)
#t.main.record() # Saves a runtime record file in rdf-style
t.main.display('DONE!')
t.main.quit() # Closes the app and kills threads


# Checking that all app threads terminated, optional
import threading
import time
while len(threading.enumerate()) > 1: # Note that this will loop forever if the window is still open
    print(threading.enumerate())
    time.sleep(.1)
