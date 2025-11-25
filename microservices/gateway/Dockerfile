FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Create directory for frontend build
RUN mkdir -p /usr/share/nginx/html

# Copy frontend build files to nginx directory
COPY build/ /usr/share/nginx/html/

EXPOSE 80 8000

CMD ["nginx", "-g", "daemon off;"]