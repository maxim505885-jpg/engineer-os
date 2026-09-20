FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY . /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/nginx.conf.template

EXPOSE 8080

CMD ["sh", "-c", "PORT=${PORT:-8080}; sed \"s/__PORT__/${PORT}/g\" /etc/nginx/nginx.conf.template > /etc/nginx/conf.d/default.conf; nginx -g 'daemon off;'"]
