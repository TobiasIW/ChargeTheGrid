import os
import sys

def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        print("PID does not exist, ProcessLookupError")
        return False
    except PermissionError:
        print("PID exists, PermissionError")
        return True
    else:
        print("PID exists, noError")
        return True
def checkRunning():
    pid = str(os.getpid())
    pidfile = "/home/pi/Entwicklung/chargePid.pid"
    print(pid)
    if os.path.isfile(pidfile):
        with open(pidfile, 'r') as pidFileStream:
            pidFromFile = int(pidFileStream.read())
            print ("found pid: "+str(pidFromFile))
            if (check_pid(pidFromFile)):
                print("pid exists, exiting")
                sys.exit()
            else:
                print("pid does not exist")
    else:
        print("does not exist")
        
    pidFileWriter= open(pidfile, 'w')
    pidFileWriter.write(pid)
    pidFileWriter.close()
