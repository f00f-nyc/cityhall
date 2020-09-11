FROM nginx:1.17.6-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
COPY include.websocket /etc/nginx/app/include.websocket
COPY include.forwarded /etc/nginx/app/include.forwarded

