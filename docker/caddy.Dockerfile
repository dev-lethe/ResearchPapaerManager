FROM caddy:2.8

# The upstream binary carries CAP_NET_BIND_SERVICE for privileged ports.
# This service listens on 8080, so remove the file capability to keep
# no-new-privileges and a fully dropped runtime capability set compatible.
RUN setcap -r /usr/bin/caddy

RUN addgroup -S caddy-runtime \
    && adduser -S -D -H -G caddy-runtime caddy-runtime

USER caddy-runtime
