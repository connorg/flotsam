# Start from Phusion because it's got OpenSSH configured to autostart.
FROM phusion/baseimage:latest
RUN apt-get update && apt-get install -y \
  iptables \
  pax \
  unzip \
  wget

# Get lite-raft
RUN wget https://lite-raft.googlecode.com/archive/7466d50c980d5d96d887e8666da3cc755a2af386.zip -O lite-raft-dist.zip
RUN mkdir /lr-tmp
RUN mkdir /lite-raft
RUN unzip lite-raft-dist.zip -d /lr-tmp
# Pull out the actual contents from the lite-raft-74.... directory
RUN mv /lr-tmp/*/* /lite-raft
RUN rm -rf /lr-tmp
# Otherwise it won't boot:
RUN mkdir /lite-raft/message-log

ADD ./run-lr.sh /usr/local/sbin/

ADD ssh-dir /root/.ssh/
EXPOSE 22
# This entry point is from Phusion base image; it starts services
CMD ["/sbin/my_init"]
