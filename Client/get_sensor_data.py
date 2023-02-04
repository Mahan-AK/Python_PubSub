import subprocess
import time
import sys


while True:
    try:
        p = subprocess.Popen(["sensors"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = p.communicate()[0].decode()

        for line in output.split('\n'):
            if line.startswith("Core 0:"):
                print(line[16:20])
                sys.stdout.flush()

        time.sleep(0.5)
    except KeyboardInterrupt:
        break