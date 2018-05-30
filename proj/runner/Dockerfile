FROM gitlab/gitlab-runner:latest

RUN apt-get update
RUN apt-get install python3 -y
RUN apt-get install pylint -y
RUN curl -fsSL get.docker.com -o get-docker.sh && sh get-docker.sh
RUN service docker start 
RUN usermod -a -G docker gitlab-runner

# might be wrong? idk
#RUN chmod 777 /var/run/docker.sock
