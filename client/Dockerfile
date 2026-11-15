FROM node:22-alpine AS build

WORKDIR /workspace

COPY package.json package-lock.json turbo.json ./
COPY client/package.json client/package.json
COPY server/package.json server/package.json
RUN npm ci

COPY client client
RUN npm run build --workspace @mind-clash/client

FROM nginx:1.27-alpine

COPY client/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/client/dist /usr/share/nginx/html

EXPOSE 80
