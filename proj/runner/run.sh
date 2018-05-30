docker run -d \
      --name runner \
      --restart always \
      --volume /srv/gitlab-runner/config:/etc/gitlab-runner \
      --volume /var/run/docker.sock:/var/run/docker.sock \
      --link gitlab:gitlab \
      runner:1.0
