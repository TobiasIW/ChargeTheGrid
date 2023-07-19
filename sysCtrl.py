import datetime
import os
import sys

class sysCtrlClass:
    def __init__(self):
        self.tasks = {}
    def check_pid(self, pid):
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


    def checkRunning(self, config):
        pid = str(os.getpid())
        pidfile = config.baseFolder + "chargePid.pid"
        print("pid of process" + pid)

        if os.path.isfile(pidfile):
            try:
                with open(pidfile, 'r') as pidFileStream:
                    pidFromFile = int(pidFileStream.read())
                    print("pid in file: " + str(pidFromFile))
                    if (self.check_pid(pidFromFile)):
                        print("pid exists, exiting")
                        sys.exit()
                    else:
                        print("pid does not exist")
            except Exception as e:
                print("Exception: pid file invalid: ", e)
        else:
            print("does not exist")
        pidFileWriter = open(pidfile, 'w')
        pidFileWriter.write(pid)
        pidFileWriter.close()

    def executeTask(self, arg_taskTime, arg_startTime):
        if str(arg_taskTime) in self.tasks.keys():
            __timeDiff = datetime.datetime.now() - self.tasks[str(arg_taskTime)]
            dT = __timeDiff.total_seconds()
            if __timeDiff.total_seconds() >= arg_taskTime:
                self.tasks[str(arg_taskTime)] = datetime.datetime.now()
                return True, dT
            else:
                return False, dT
        else:
            if arg_startTime == 0:
                self.tasks[str(arg_taskTime)] = datetime.datetime.now()
                return True, arg_taskTime
            else:
                self.tasks[str(arg_taskTime)] = datetime.datetime.now() - datetime.timedelta(
                    seconds=arg_taskTime - arg_startTime)
                return False, arg_taskTime



