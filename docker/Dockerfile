# Sandbox image for `greenwash --sandbox docker`.
# Python 3.12 and Node 22 match the versions installed in CI.
FROM node:22 AS node

FROM python:3.12-slim

# Bring in the Node 22 runtime and npm without pulling the full Node image.
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e ".[dev]"

# DockerSandbox mounts the task workspace here and passes it as the workdir.
WORKDIR /work
