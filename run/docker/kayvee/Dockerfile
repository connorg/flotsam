FROM java:7
RUN apt-get update && apt-get install -y \
  iptables

RUN wget http://search.maven.org/remotecontent?filepath=io/libraft/kayvee/0.1.1/kayvee-0.1.1-dist.zip -O kayvee-dist.zip
RUN mkdir /kayvee
RUN unzip kayvee-dist.zip -d /kayvee
RUN mv /kayvee/*/* /kayvee/
# COPY ./docker-entrypoint.sh /
# ENTRYPOINT ["/docker-entrypoint.sh"]
ENTRYPOINT ["/bin/bash"]
