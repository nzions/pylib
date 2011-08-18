import telnetlib
import sys
import re

class RemoteCiscoConsole:
    def __init__(self):
        self.con = None

    def connect(self,device,username,password,enpassword=None,prot='telnet'):
        """
        Connects to a device and logges in, will raise an error if it fails
        """

        # reset con
        self.con = None

        # prompt timeout
        pto = 2

        # connect
        if (enpassword == None): enpassword = password
        
        try:
            self.con = telnetlib.Telnet(device,23,5)
        except:
            raise Exception(sys.exc_info()[1])

        # login, first stage
        a,b,c = self.con.expect(["sername: ", "assword: "], pto)
        if a == -1:
            print repr(c)
            raise Exception('Unrecognised prompt: %s' % c)
        elif a == 0:
            self.con.write(username + "\n")
            a,b,c = self.con.expect(["assword: "], pto)
            if a == -1:
                raise Exception('Sent username, no password prompt: %s' % c)
        self.con.write(password + "\n")

        # logon enter enable
        a,b,c = self.con.expect([">", "#"], pto)
        if a == -1:
            raise Exception('No command prompt: %s' % c)
        elif a == 0:
            self.con.write("en\n")
            a,b,c = self.con.expect(["assword: "], pto)
            if a == -1:
                raise Exception('No enable password prompt: %s' % c)
            self.con.write(enpassword + "\n")
            a,b,c = self.con.expect(["#"], pto)
            if a == -1:
                raise Exception('Could not enter enable prompt: %s' % c)

        try:
            self.safe_exec('term length 0')
        except:
            raise Exception('Could not set term lenght to 0: %s' % sys.exc_info()[1])

        return(True)
        
    def safe_exec(self,command,expect="#"):
        """
        Executes the command on conn and expects the expect
        raises an error if the result is not returned
        raises an error if % Invalid input detected is returned as well

        returns the returned data if succesful
        """

        self.con.write(command + "\n")
        a,b,c = self.con.expect([expect], 2)
        if a == -1:
            raise Exception('Error Command "%s" did not return "%s": %s' % (command,expect,c))
        if re.search('% Invalid input detected', c):
            raise Exception('Error Command "%s" is invalid' % command)

        return(c)
