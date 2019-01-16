import commands
import os
import socket
import subprocess
import thread
import threading
import time

class RTL_Thread (threading.Thread):

    def __init__(self, cfg):
    	
	#Start rtl thread
        print "Creating a  RTL_Thread object"
    	if os.system("csdr 2> /dev/null") == 32512: #check for csdr
             print "[RTL thread object] You need to install \"csdr\" to run OpenWebRX!\n"
             return
    	if os.system("nmux --help 2> /dev/null") == 32512: #check for nmux
             print "[RTL thread object] You need to install an up-to-date version of \"csdr\" that contains the \"nmux\" tool to run OpenWebRX! Please upgrade \"csdr\"!\n"
             return
    	if cfg.start_rtl_thread:
            nmux_bufcnt = nmux_bufsize = 0
            while nmux_bufsize < cfg.samp_rate/4: nmux_bufsize += 4096
            while nmux_bufsize * nmux_bufcnt < cfg.nmux_memory * 1e6: nmux_bufcnt += 1
            if nmux_bufcnt == 0 or nmux_bufsize == 0: 
                print "[RTL thread object] Error: nmux_bufsize or nmux_bufcnt is zero. These depend on nmux_memory and samp_rate options in config_webrx.py"
                return
            print "[RTL thread object] nmux_bufsize = %d, nmux_bufcnt = %d" % (nmux_bufsize, nmux_bufcnt)
            local_rtl_command = cfg.start_rtl_command
            local_rtl_command += "| nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (nmux_bufsize, nmux_bufcnt, cfg.iq_server_port)
            self.rtl_thread=threading.Thread(target = lambda:subprocess.Popen(local_rtl_command, shell=True),  args=())
            self.rtl_thread.start()
            print "[RTL thread object] Started rtl_thread: "+local_rtl_command
            print "[RTL thread object] Waiting for I/Q server to start..."
            while True:
                testsock=socket.socket()
                try: testsock.connect(("127.0.0.1", cfg.iq_server_port))
                except:
                    time.sleep(0.1)
                    continue
                testsock.close()
                break
            self.pid = commands.getoutput("ps -ef | grep rtl_sdr | grep -v /bin/sh").split()[1]
            print "[RTL thread object] I/Q server started: " + self.pid

    def stop(self):
        print "[RTL thread object] Terminating " + self.pid
        os.kill(int(self.pid), 15)

    def restart(self, cfg, center_freq):
        print "[RTL thread object] Terminating " + self.pid
        try:
            os.kill(int(self.pid), 15)
        except:
            pass
        time.sleep(5.0)
        nmux_bufcnt = nmux_bufsize = 0
        while nmux_bufsize < cfg.samp_rate/4: nmux_bufsize += 4096
        while nmux_bufsize * nmux_bufcnt < cfg.nmux_memory * 1e6: nmux_bufcnt += 1
        if nmux_bufcnt == 0 or nmux_bufsize == 0: 
            print "[RTL thread object] Error: nmux_bufsize or nmux_bufcnt is zero. These depend on nmux_memory and samp_rate options in config_webrx.py"
            return
        print "[RTL thread object] nmux_bufsize = %d, nmux_bufcnt = %d" % (nmux_bufsize, nmux_bufcnt)
        local_rtl_command = cfg.start_rtl_command[0:cfg.start_rtl_command.find("-f")+2] + " " + center_freq + " " + cfg.start_rtl_command[cfg.start_rtl_command.find("-p"):]
        local_rtl_command += "| nmux --bufsize %d --bufcnt %d --port %d --address 127.0.0.1" % (nmux_bufsize, nmux_bufcnt, cfg.iq_server_port)
        self.rtl_thread=threading.Thread(target = lambda:subprocess.Popen(local_rtl_command, shell=True),  args=())
        self.rtl_thread.start()
        print "[RTL thread object] Started rtl_thread: "+local_rtl_command
        print "[RTL thread object] Waiting for I/Q server to start..."
        while True:
            testsock=socket.socket()
            try: testsock.connect(("127.0.0.1", cfg.iq_server_port))
            except:
                time.sleep(0.1)
                continue
            testsock.close()
            break
        print commands.getoutput("ps -ef | grep rtl_sdr")
        self.pid = commands.getoutput("ps -ef | grep rtl_sdr | grep -v /bin/sh").split()[1]
        print "[RTL thread object] I/Q server restarted: " + self.pid
