# The Caddyfile is baked into the image rather than bind-mounted from the host so
# the TLS config is versioned with the commit that needs it — docker-compose.prod.yml
# and Caddyfile can't drift apart between the revision that was built and whatever
# happens to be checked out on the EC2 host.
#
# Runtime config that varies per deployment (APP_DOMAIN, ACME_EMAIL) is still
# supplied as environment variables by docker-compose.prod.yml; Caddy's Caddyfile
# reads those with {$VAR} at startup.
FROM caddy:2-alpine

COPY Caddyfile /etc/caddy/Caddyfile