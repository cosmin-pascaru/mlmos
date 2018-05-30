FROM gitlab/gitlab-runner:latest

RUN apt-get update
RUN apt-get install python3 -y
RUN apt-get install pylint -y
RUN curl -fsSL get.docker.com -o get-docker.sh && sh get-docker.sh
RUN service docker start

RUN groupadd --gid 995 host_docker  
RUN usermod -a -G host_docker gitlab-runner

# TODO:
# Pass docker group id from host to container, 
# and add gitlab-runner user to host's docker group,
# so it can access docker.sock

