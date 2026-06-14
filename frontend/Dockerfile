# Nginx-based Dockerfile for frontend production serving
FROM node:20-alpine AS build

WORKDIR /app

# Add a build argument to invalidate cache if necessary
ARG CACHEBUST=1

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy the rest of the application
COPY . .

# Build the React app using Vite
# We pass standard environment variables that Vite expects
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Serve the app with Nginx
FROM nginx:alpine

# Copy the custom Nginx config (we will create this or use default with a tweak)
# For SPA routing to work, we need to fallback to index.html
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Copy the build output from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
