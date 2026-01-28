FROM nginx:alpine

# Copy static files
COPY index.html /usr/share/nginx/html/index.html

# Custom nginx config for SPA
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
