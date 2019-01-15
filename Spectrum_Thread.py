import commands
import csdr
import os
import socket
import subprocess
import thread
import threading
import time

class Spectrum_Thread (threading.Thread):

    def __init__(self, cfg, clients, cma, cmr):

        self.clients = clients
        self.cfg = cfg
        self.cma = cma
        self.cmr = cmr
        self.pid = ""
    	if os.system("csdr 2> /dev/null") == 32512: #check for csdr
             print "[Spectrum_Thread constructor] You need to install \"csdr\" to run OpenWebRX!\n"
             return
    	if os.system("nmux --help 2> /dev/null") == 32512: #check for nmux
             print "[Spectrum_Thread constructor] You need to install an up-to-date version of \"csdr\" that contains the \"nmux\" tool to run OpenWebRX! Please upgrade \"csdr\"!\n"
             return
    	if cfg.start_rtl_thread:
	    #Start spectrum thread
            print "Creating a  Spectrum_Thread object"
            self.spectrum_thread=threading.Thread(target = self.spectrum_thread_function, args = ())
            self.spectrum_thread.start()
        print commands.getoutput('ps -ef | grep "nc -v" | grep /bin/sh | grep -v grep | grep logaver')
        self.pid = commands.getoutput('ps -ef | grep "nc -v" | grep /bin/sh | grep -v grep | grep logaver').split()[1]
        print "[Spectrum_Thread constructor] csdr chain started: " + self.pid


    def spectrum_thread_function(self):
        global clients, spectrum_dsp, spectrum_thread_watchdog_last_tick
        spectrum_dsp=dsp=csdr.dsp()
        dsp.nc_port=self.cfg.iq_server_port
        dsp.set_demodulator("fft")
        dsp.set_samp_rate(self.cfg.samp_rate)
        dsp.set_fft_size(self.cfg.fft_size)
        dsp.set_fft_fps(self.cfg.fft_fps)
        dsp.set_fft_averages(int(round(1.0 * self.cfg.samp_rate / self.cfg.fft_size / self.cfg.fft_fps / (1.0 - self.cfg.fft_voverlap_factor))) if self.cfg.fft_voverlap_factor>0 else 0)
        dsp.set_fft_compression(self.cfg.fft_compression)
        dsp.set_format_conversion(self.cfg.format_conversion)
        self.apply_csdr_cfg_to_dsp(dsp)
        sleep_sec=0.87/self.cfg.fft_fps
        print "[Spectrum_Thread constructor] Spectrum thread initialized successfully."
        dsp.start()
        if self.cfg.csdr_dynamic_bufsize:
            dsp.read(8) #dummy read to skip bufsize & preamble
            print "[Spectrum_Thread constructor] Note: CSDR_DYNAMIC_BUFSIZE_ON = 1"
        print "[Spectrum_Thread constructor] Spectrum thread started."
        bytes_to_read=int(dsp.get_fft_bytes_to_read())
        spectrum_thread_counter=0
        while True:
            data=dsp.read(bytes_to_read)
            #print "gotcha",len(data),"bytes of spectrum data via spectrum_thread_function()"
            if spectrum_thread_counter >= self.cfg.fft_fps:
                spectrum_thread_counter=0
                spectrum_thread_watchdog_last_tick = time.time() #once every second
            else: spectrum_thread_counter+=1
            self.cma("spectrum_thread")
            correction=0
            for i in range(0,len(self.clients)):
                i-=correction
                if (self.clients[i].ws_started):
                    #print "got data and have clients"
                    if self.clients[i].spectrum_queue.full():
                        print "[Spectrum_Thread function] client spectrum queue full, closing it."
                        close_client(i, False)
                        correction+=1
                    else:
                        #print "[Spectrum_Thread function] putting data into queue."
                        self.clients[i].spectrum_queue.put([data]) # add new string by "reference" to all clients
                else:
                    print "[Spectrum_Thread function] Not queueing spectrum data - no clients"

            self.cmr()
            
    def apply_csdr_cfg_to_dsp(self, dsp):
        dsp.csdr_dynamic_bufsize = self.cfg.csdr_dynamic_bufsize
        dsp.csdr_print_bufsizes = self.cfg.csdr_print_bufsizes
        dsp.csdr_through = self.cfg.csdr_through

    def stop(self):
        print "[Spectrum_Thread] Terminating Spectrum_Thread: " + self.pid
        os.kill(int(self.pid), 15)
        os.system("pkill csdr")

