FROM alpine:latest

# Install dependencies and CoreDNS
RUN apk add --no-cache ca-certificates wget && \
    wget https://github.com/coredns/coredns/releases/download/v1.12.0/coredns_1.12.0_linux_amd64.tgz && \
    tar -xzf coredns_1.12.0_linux_amd64.tgz && \
    mv coredns /usr/local/bin/ && \
    rm coredns_1.12.0_linux_amd64.tgz

# Run CoreDNS and redirect standard output to a log file
CMD ["sh", "-c", "coredns -conf /etc/coredns/Corefile > /etc/coredns/dns-queries.log 2>&1"]
