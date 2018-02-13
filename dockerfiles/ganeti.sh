#!/bin/bash
set -ex
if [ "$(hostname)" == "localhost.localdomain" ] ; then
  hostname "$(cat /etc/hostname)"
fi

if [ "$(hostname)" == "node1" ] ; then
  ganeti_ver="$(gnt-cluster --version | awk '{print $NF}')"
  no_drbd=""
  no_lvm=""
  disk_templates=""
  ipolicy=""
  if [ "$ganeti_ver" != "$(echo -e "${ganeti_ver}\n2.7.99" | sort -V | head -n1)" ] ; then
    disk_templates="--enabled-disk-templates=diskless"
    ipolicy="--ipolicy-bounds-specs=min:disk-size=0,cpu-count=1,disk-count=0,memory-size=1,nic-count=0,spindle-use=0/max:disk-size=1048576,cpu-count=8,disk-count=16,memory-size=32768,nic-count=8,spindle-use=12"
  fi
  if [ "$ganeti_ver" = "$(echo -e "${ganeti_ver}\n2.8.2" | sort -V | head -n1)" ] ; then
    no_lvm="--no-lvm-storage"
  fi
  if [ "$ganeti_ver" = "$(echo -e "${ganeti_ver}\n2.9.4" | sort -V | head -n1)" ] ; then
    no_drbd="--no-drbd-storage"
  fi
  chmod 600 /root/.ssh/id_rsa
  gnt-cluster init --no-etc-hosts \
      --master-netdev=eth0 -N mode=routed,link=100 ${no_drbd} ${no_lvm} \
      --enabled-hypervisors=fake \
      ${disk_templates} ${ipolicy} \
      cluster
  gnt-node add --no-ssh-key-check node2
  gnt-node add --no-ssh-key-check node3

  for i in 1 2 3 4 ; do
   gnt-instance add -t diskless --no-ip-check --no-name-check -I hail \
    -o image+cirros --net 0:ip=192.168.1.10${i} instance${i}
  done
fi
touch /var/lock/subsys/local
