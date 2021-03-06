'''
Created on Sep 9, 2013

@author: eviek.
'''
#!/usr/bin/env python

import os, sys, time
import paramiko
from Instance import InstanceHandler

class Executioner:
    
    def __init__(self):
        self.instances = InstanceHandler()
        self.key = str(self.instances.key + '.pem')
        if not os.path.isfile(self.key):
            print "Key doesn't exist. Please make sure it is in the right directory."
            sys.exit(2)
    
    def printProgress(self, transferred, totalsize):
        progress = float(transferred *100 / totalsize)
        fill = int(progress / 2)
        text = "\rProgress: [{0}] {1}%".format( "-"*fill + " "*(50-fill), progress)
        sys.stdout.write(text)
        sys.stdout.flush()
    
    def load_data(self):
        # Transfer data : transfer to 1 host and scp from there to other hosts using private ip
        # TAR all files to transfer one! <-------------
        print "Transferring data to 1 server"
        pkey = paramiko.RSAKey.from_private_key_file(self.key)
        try:
            transport = paramiko.Transport((self.hosts[0], 22))
            transport.connect(username = 'ubuntu', pkey=pkey)
            transport.open_channel("session", self.hosts[0], "localhost")
            sftp = paramiko.SFTPClient.from_transport(transport)
            self.printProgress(0, 1)
            # Send file to host[0]
            sftp.put("testfile", "/home/ubuntu/testfile", callback=self.printProgress)
            sftp.put("run.sh", "/home/ubuntu/run.sh", callback=self.printProgress)
            # Send private key for access to other hosts
            sftp.put(self.key,self.key)
            sftp.close()
            sys.stdout.write("\n")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.hosts[0], username='ubuntu', key_filename=self.key)
            # Set permissions to be able to use the key
            stdin, stdout, stderr = ssh.exec_command('chmod 700 ' + self.key)
            stdin, stdout, stderr = ssh.exec_command('chmod a+x run.sh')
            print "Copy data to other servers"
            # Copy data to other hosts with scp
            # NOTE: only for first connection in other hosts no StrictHostKeyChecking!
            for ip in self.ips[1:]:
                stdin, stdout, stderr = ssh.exec_command('scp -o StrictHostKeyChecking=no -i '
                                                         +self.key+' testfile ubuntu@'+ip+':~/')
                stdin, stdout, stderr = ssh.exec_command('scp -i '+self.key+' run.sh ubuntu@'+ip+':~/')
        except:
            print "An error occurred while transferring data"
            self.instances.terminate()
            raise
        ssh.close()
        print "Transfer complete"
    
    def run(self):
        # Execute commands in all hosts
        print "Starting execution"
        for host in self.hosts:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(host, username='ubuntu', key_filename=self.key)
                # Execute command (asynchronous)
                stdin, stdout, stderr = ssh.exec_command('./run.sh')
                # Synchronous output with channel
                channel = stdout.channel
                while not channel.exit_status_ready():
                    if channel.recv_ready():
                        output = channel.recv(1024)
                        sys.stdout.write(output)
                sys.stdout.flush()
            except:
                print "An error occurred while executing commands"
                self.instances.terminate()
                raise
            ssh.close()
        print "Finished execution"
    
    def get_results(self):
        print "Copying results from remote servers"
        pkey = paramiko.RSAKey.from_private_key_file(self.key)
        self.printProgress(0, 1)
        for host in self.hosts:
            try:
                transport = paramiko.Transport((host, 22))
                transport.connect(username = 'ubuntu', pkey=pkey)
                transport.open_channel("session", host, "localhost")
                sftp = paramiko.SFTPClient.from_transport(transport)
                sftp.get("/home/ubuntu/testfile","resultfile_"+host, callback=self.printProgress)
                sftp.close()
            except:
                print "An error occurred while receiving results. Retrieve them manually and handle"
                print "remaining instances' termination."
                raise
        sys.stdout.write("\n")
        print "Transfer complete"
    
    def start(self):
#        self.instances.authenticate()
#        self.instances.get_billing()
        self.hosts, self.ips = self.instances.launch()
        # Wait for servers to start all services
        print "Wait 1 minute for servers to be ready"
        time.sleep(60)
        self.instances.set_alarm()
#        self.load_data()
#        self.run()
#        self.get_results()
        self.instances.terminate()
#        self.instances.get_billing()
    
    def stop(self):
        self.instances.terminate()
    
if __name__ == "__main__":
    execution = Executioner()
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            execution.start()
        elif 'stop' == sys.argv[1]:
            execution.stop()
        else:
            print "Unknown command"
            sys.exit(2)
    elif len(sys.argv) > 2:
        if 'load_data' == sys.argv[1]:
            execution.hosts, execution.ips = execution.instances.get_instances()
            if execution.hosts:
                execution.load_data()
        elif 'run' == sys.argv[1]:
            execution.hosts, execution.ips = execution.instances.get_instances()
            if execution.hosts:
                execution.run()
        elif 'get_results' == sys.argv[1]:
            execution.hosts, execution.ips = execution.instances.get_instances()
            if execution.hosts:
                execution.get_results()
        else:
            print "Unknown command"
            sys.exit(2)
    else:
        print "usage: %s start|stop|load_data instance1 instance2 ..|run instance1 instance2 ..|get_results instance1 instance2 .." % sys.argv[0]
        sys.exit(2)
    sys.exit(0)