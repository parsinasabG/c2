# Stage 1: Build the React application
FROM node:18-alpine AS build

# Set the working directory in the container for the app source
WORKDIR /app/app

# Copy package.json and package-lock.json from the 'app' subdirectory of the build context
COPY app/package.json ./
COPY app/package-lock.json ./
# If you use yarn:
# COPY app/yarn.lock ./
# RUN yarn install

# Install dependencies
RUN npm install

# Copy the rest of the application code from the 'app' subdirectory
COPY app/ /app/app/

# Build the application (npm run build should be defined in app/package.json)
RUN npm run build

# Stage 2: Serve the static files with Nginx
FROM nginx:1.21-alpine

# Copy the build output from the build stage (/app/app/build) to Nginx html directory
COPY --from=build /app/app/build /usr/share/nginx/html

# Copy a custom Nginx configuration if needed (optional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for Nginx
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
