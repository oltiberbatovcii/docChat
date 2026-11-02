# Stage 1: build the static site with Node
FROM node:24-alpine AS build
WORKDIR /app

# Dependencies first, for layer caching; `npm ci` installs exactly what package-lock.json says
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# Vite bakes this into the JavaScript at build time. The browser (on your machine) calls the
# API, so it's the address seen from the host, not the container name.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Stage 2: serve only the built files. Node and node_modules stay behind in stage 1.
# The unprivileged variant runs Nginx as a non-root user, listening on 8080 instead of 80.
FROM nginxinc/nginx-unprivileged:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
