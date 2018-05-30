FROM alpine:latest

COPY http_server.py /home/http_server.py

RUN apk --no-cache add python3

ENTRYPOINT python3 /home/http_server.py
