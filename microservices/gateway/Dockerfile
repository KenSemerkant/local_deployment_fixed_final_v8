FROM nginx:alpine

# Create a default HTML page to serve the frontend
RUN rm -rf /usr/share/nginx/html/*

# We'll copy the frontend build in the docker-compose volume mount
# For now, just create a placeholder
RUN echo "<h1>AI Financial Analyst Microservices</h1>" > /usr/share/nginx/html/index.html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 8000

CMD ["nginx", "-g", "daemon off;"]