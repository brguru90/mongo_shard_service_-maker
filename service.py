import sys
import subprocess as sp

service_name="myservice"
path="~/Desktop/run.py"
paams=""
user=sp.Popen('echo $USER', stdout=sp.PIPE, stderr=None,shell=True).communicate()[0].decode()
if user=="":
    user="root"
print(str(sys.argv))
if len(sys.argv)>=2:
    path=sys.argv[1]
if len(sys.argv)>=3:
    service_name=sys.argv[2]
if len(sys.argv)>=4:
    user=sys.argv[3]
if len(sys.argv)>=5 and sys.argv[4]!="":
    paams=sys.argv[4]

file_name=path.split("/")[-1]
sp.Popen('cp -f {} /usr/bin/{}'.format(path,file_name), shell=True,stdout=sp.PIPE, stderr=sp.PIPE) 

service='''[Unit]
Description={0}
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
Type=simple
Restart=always
RestartSec=10
User={2}
ExecStart=/usr/bin/bash -c "/usr/bin/python3 /usr/bin/{1} {3}"
StandardInput=tty-force

[Install]
WantedBy=multi-user.target
'''.format(service_name,file_name,user,paams)

f = open("/lib/systemd/system/{}".format(service_name+".service"), "w")
f.write(service)
f.close()

print(service)

sp.Popen('bash -c "chmod 775 /usr/bin/{}"'.format(file_name), shell=True,stdout=sp.PIPE, stderr=sp.PIPE)   
sp.Popen('bash -c "systemctl daemon-reload && systemctl stop {0} && systemctl enable {0} && systemctl start {0}"'.format(service_name), shell=True, stdout=sp.PIPE, stderr=sp.PIPE)   