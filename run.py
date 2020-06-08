import sys,os,time,re,shutil
import subprocess as sp


nor_of_config=2
nor_of_shard=2
default_port=27017

if len(sys.argv)>=2:
  default_port=int(sys.argv[1])
if len(sys.argv)>=3:
  nor_of_shard=int(sys.argv[2])
if len(sys.argv)==4:
  nor_of_config=int(sys.argv[3])

config_db_count=0
shard_db_count=0
path="/data"

from os import listdir
if os.path.exists(path):
  config_db_count=[f for f in listdir(path) if re.search("^meta", f)]
  shard_db_count=[f for f in listdir(path) if re.search("^shard", f)]
  if nor_of_config!=len(config_db_count):
    for dir  in config_db_count:
      shutil.rmtree(path+"/"+dir)  
  if nor_of_config!=len(shard_db_count):
    for dir  in shard_db_count:
      shutil.rmtree(path+"/"+dir)
  



for i in range(0,100):
  print("Killing ",str(28000+i))
  sp.Popen('bash -c "fuser -k '+str(28000+i)+'/tcp"', shell=True)
for i in range(0,100):
  print("Killing ",str(29000+i))
  sp.Popen('bash -c "fuser -k '+str(29000+i)+'/tcp"', shell=True)
time.sleep(2)
config_hosts=[]
#sp.Popen('gnome-terminal -x bash -c "sleep 5 && ls -la && sleep 5"', shell=True)  
for i in range(0,nor_of_config):
  while True:
    sp.Popen('mkdir -p /data/meta{0}_db && chown -R :mongodb /data && chmod -R 771 /data && (mongod --configsvr --replSet cfgrs --dbpath /data/meta{0}_db --bind_ip_all --port {1})&'.format(str(i),str(28000+i)),shell=True,stdin=None, close_fds=True,stdout=sp.DEVNULL, stderr=None)
    if sp.Popen('lsof -i :{}'.format(str(28000+i)), stdout=sp.PIPE, stderr=None,shell=True).communicate()[0].decode()!="":
      print("---Configsvr ",28000+i)
      break
    time.sleep(5)
  config_hosts.append('{ _id : '+str(i)+', host : \\"127.0.0.1:'+str(28000+i)+'\\" }')
shard_hosts=[]
for i in range(0,nor_of_shard):  
  while True:
    sp.Popen('mkdir -p /data/shard{0}_db && chown -R :mongodb /data && chmod -R 771 /data && (mongod --shardsvr --replSet shard1rs --dbpath /data/shard{0}_db --port {1} --bind_ip_all)'.format(str(i),str(29000+i)), shell=True,stdin=None, close_fds=True,stdout=sp.DEVNULL, stderr=None)
    if sp.Popen('lsof -i :{}'.format(str(29000+i)), stdout=sp.PIPE, stderr=None,shell=True).communicate()[0].decode()!="":
      print("---Shardsvr ",29000+i)
      break
    time.sleep(5)
  shard_hosts.append('{ _id : '+str(i)+', host : \\"127.0.0.1:'+str(29000+i)+'\\" }')

cmd='''echo -e "rs.initiate(
  {
    _id: \\"cfgrs\\",
    configsvr: true,
    members: [
     '''+",\n".join(config_hosts)+'''
    ]
  }
)\\n\\cc" | mongo --port 28000 & read'''
print(cmd)
# , stderr=sp.STDOUT
sp.Popen('bash -c  \''+cmd+'\'',shell=True)

cmd='''echo -e "rs.initiate(
  {
    _id: \\"shard1rs\\",
    members: [
     '''+",\n".join(shard_hosts)+'''
    ]
  }
)\\n\\cc" | mongo --port 29000 & read'''
print(cmd)
sp.Popen('bash -c  \''+cmd+'\'',shell=True)
if default_port==27017:
  sp.Popen('bash -c "systemctl stop mongod && fuser -k {}/tcp"'.format(str(default_port)), shell=True)
else:
  sp.Popen('bash -c "fuser -k {}/tcp"'.format(str(default_port)), shell=True)
for i in range(5,0,-1):
    time.sleep(1)
    print(i,"/",5,"Seconds")
#sp.Popen('bash -c "(mongos --configdb cfgrs/127.0.0.1:27020,127.0.0.1:27021 --bind_ip_all --port {})"'.format(str(default_port)), shell=True, close_fds=True)
# sp.Popen('gnome-terminal -x bash -c "lsof -i :27020 && lsof -i :27021 && read"', shell=True)
config_hosts=["127.0.0.1:{}".format(str(28000+i)) for i in range(nor_of_config)]
print(",".join(config_hosts))
while sp.Popen('lsof -i :{}'.format(str(default_port)), stdout=sp.PIPE, stderr=None,shell=True).communicate()[0].decode()=="":
  sp.Popen('mongos --configdb cfgrs/{} --bind_ip_all --port {} &'.format(",".join(config_hosts),str(default_port)), shell=True, close_fds=True,stdout=None, stderr=None)
  print("\n\nMongo({}) Retrying.......\n\n".format(str(default_port)))
  if sp.Popen('lsof -i :{}'.format(str(default_port)), stdout=sp.PIPE, stderr=None,shell=True).communicate()[0].decode()!="":
    break
  time.sleep(5)

shard_hosts=["127.0.0.1:{}".format(str(29000+i)) for i in range(nor_of_shard)]
print(",".join(shard_hosts))
cmd='''echo -e "sh.addShard(\\"shard1rs/'''+",".join(shard_hosts)+'''\\")\\nsh.status()\\n" | mongo --port '''+str(default_port)
print(cmd)
sp.Popen('bash -c  \''+cmd+'\'',shell=True)

while True:
  time.sleep(3600*24)
