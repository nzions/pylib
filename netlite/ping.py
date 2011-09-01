
# lighweight PING libraries

import threading
import os
import struct
import socket
import select
import time
import datetime

# from os import getpid


class Ping():
    def __init__(self):
        
        self.lock = threading.Lock()
        self.sequences = {}
        self.last_sequence = 0

    # this code is spread all over the internet
    # Original Version from Matthew Dixon Cowles:
    # -> ftp://ftp.visi.com/users/mdc/ping.py
    def _checksum(self, source_string):
        """
        I'm not too confident that this is right but testing seems
        to suggest that it gives the same answers as in_cksum in ping.c
        """

        sum = 0
        countTo = len(source_string) / 2 * 2
        count = 0
        while count < countTo:
            thisVal = ord(source_string[count + 1]) * 256 + ord(source_string[count])
            sum = sum + thisVal
            sum = sum & 0xffffffff  # Necessary?
            count = count + 2

        if countTo < len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff  # Necessary?

        sum = (sum >> 16) + (sum & 65535)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 65535

        # Swap bytes. Bugger me if I know why.
        answer = answer >> 8 | answer << 8 & 0xff00

        return answer
        
    def ping(self, host, timeout=2000):
        """Pings the <host> with a timeout of <timeout> in ms
            returns a 2 value tuple
            (True/False, RTT (in ms))
            raises on a system error
            returns false if ping did not respond within timeout
            """

        try:
            ip = socket.gethostbyname(host)
        except:
            raise(Exception, "Could not resolve host " + host)
        

        payload = 'Python netlite/ping F0F0F'
        pack_string = '!BBHHH' + str(len(payload)) + 's'
        checksum = 0

        # get the PID, make sure it stays 16 bit
        process_id = os.getpid() & 0xFFFF

        # create the unique sequence
        # lock is used here for thread safety
        sequence = None
        self.lock.acquire()
        sequence = self.last_sequence & 0xFFFF

        if (sequence in self.sequences):
            self.lock.release()
            raise(Exception, "Ran out of Sequences, wow are we really pinging 65k hosts?")

        self.sequences[sequence] = host
        self.last_sequence += 1
        self.lock.release()

        # crete the socket
        # should eventually wrap this, but the caller should be handling exceptions
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp'))
        sock.bind(('0.0.0.0',0))

        # ICMP Header is type (8), code Echo reply (0), checksum (16), id (16), sequence (16) 
        message = struct.pack(pack_string, 8, 0, checksum, process_id, sequence, payload)

        # generate Checksum
        checksum = self._checksum(message)

        # regenerate message with checksum
        message = struct.pack(pack_string, 8, 0, checksum, process_id, sequence, payload)

        # now send the packet
        start_time = time.clock()
        sock.sendto(message, (ip, 1))

        # now recieve the response
        sel = select.select([sock], [], [], (timeout / 1000))
        if sel[0] == []:
            return(False,timeout)

        loop_time = time.clock()
        current_rttms = (loop_time - start_time) * 1000

        data, addr = sock.recvfrom(1500)
        if (addr[0] != ip):
            raise(Exception, "Recieved a packet that wasn't mine from " + addr[0])
        
        header = data[20:28]
        r_type, r_code, r_checksum, r_id, r_sequence = struct.unpack('!BBHHH', header)

        if (r_type != 0 and r_code != 0):
            return(False, 0)

        if (r_id == process_id and r_sequence == sequence):
            return(True, current_rttms)

    def _oldloop():
        """The old loop method of processing PING reply's"""
    
        # and now loop untill we recieve a response or time out
        while True:

            # this was ported across from ruby where a raw socket recieves all icmp reply's
            # probably something to do wit setting promisc mode or something
            # this pythong config seems to only return packets sourced from the app
            # needs more testing

            # this section not needed
            loop_time = time.clock()
            current_rttms = (loop_time - start_time) * 1000
            
            # break out on timeout
            if (current_rttms > timeout):
                return(False,timeout)
            
            sel = select.select([sock], [], [], (timeout / 1000))
            if sel[0] == []: continue
            
            # we got a packet
            loop_time = time.clock()
            current_rttms = (loop_time - start_time) * 1000

            data, addr = sock.recvfrom(1500)
            if (addr[0] != ip):
                print "not my packet"
                continue
            
            header = data[20:28]
            x, y, z, r_id, r_sequence = struct.unpack('!BBHHH', header)

            if (r_id == process_id and r_sequence == sequence):
                return(True, current_rttms)


if __name__ == "__main__":
    """ Sample of lightweight ping"""

    p = Ping()
    print p.ping('192.168.0.1')
    

        
        

        
