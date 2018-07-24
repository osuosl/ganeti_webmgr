ARG VERSION="latest"
FROM osuosl/ganeti:${VERSION}
COPY dockerfiles/ganeti.sh /etc/rc.d/rc.local
COPY dockerfiles/rapi.users /var/lib/ganeti/rapi/users
COPY dockerfiles/id_rsa-ganeti /root/.ssh/id_rsa
COPY dockerfiles/id_rsa-ganeti.pub /root/.ssh/authorized_keys
RUN chmod +x /etc/rc.d/rc.local && echo "password" | passwd root --stdin
CMD ["/sbin/init"]
