FROM node:20-alpine

WORKDIR /app

# Accept build arguments for environment variables
ARG VITE_API_URL=/api
ARG VITE_APP_NAME=SignalEdge\ AI
ARG VITE_STRIPE_PUBLISHABLE_KEY

# Set as environment variables for the build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_NAME=$VITE_APP_NAME
ENV VITE_STRIPE_PUBLISHABLE_KEY=$VITE_STRIPE_PUBLISHABLE_KEY

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies with improved error handling
# Use npm ci for locked dependencies and better reproducibility in Docker
RUN npm config set fetch-timeout 120000 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm config set registry https://registry.npmjs.org && \
    npm cache clean --force && \
    npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Copy source
COPY . .

# Build
RUN npm run build

# Serve with nginx
FROM nginx:alpine

COPY --from=0 /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
