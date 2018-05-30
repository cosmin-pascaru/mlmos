docker run -d \
      --name runner \
      --restart always \
      -v /srv/gitlab-runner/config:/etc/gitlab-runner \
      -v /var/run/docker.sock:/var/run/docker.sock \
      --link gitlab:gitlab \
      runner:1.0
