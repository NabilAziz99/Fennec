# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Bake the API base URL into the bundle at build time
ARG VITE_API_BASE_URL=https://fennec-api-429281326783.us-west1.run.app
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config template (uses $PORT substituted at startup)
COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port (Cloud Run sets PORT=8080)
EXPOSE 8080

ENV PORT=8080

# Substitute $PORT at startup, then start nginx
CMD ["/bin/sh", "-c", "envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
