FROM golang
# Modified from https://github.com/docker-library/golang/tree/master/1.4/onbuild

RUN mkdir -p /go/src/app
WORKDIR /go/src/app

# this will be built below. go-wrapper is from golang.
CMD ["go-wrapper", "run"]

RUN apt-get update && apt-get install -y \
  iptables \
  unzip \
  wget

RUN wget https://github.com/connorg/raftd-forgetful/archive/df36d5f792f7717a06711995368e64ebb229f424.zip -O /tmp/raftd.zip
RUN mkdir -p /tmp/raftd-unzip
RUN unzip /tmp/raftd -d /tmp/raftd-unzip/
RUN mv /tmp/raftd-unzip/*/* /go/src/app/
RUN go-wrapper download
RUN go-wrapper install
