# Frontend Dockerfile with improved build context handling
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy public directory explicitly first to ensure it exists
COPY public ./public/

# Then copy the rest of the source code
COPY src ./src/
COPY tsconfig.json ./
COPY .env* ./

# Set environment variables
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy build files from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
