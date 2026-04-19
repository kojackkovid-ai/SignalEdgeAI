const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3001;
const HOST = '0.0.0.0';
const DIST_DIR = path.join(__dirname, 'dist');
const BACKEND_URL = 'http://localhost:8000';

console.log('DIST_DIR:', DIST_DIR);
console.log('DIST_DIR exists:', fs.existsSync(DIST_DIR));
console.log('Backend URL:', BACKEND_URL);

// Function to proxy API requests to the backend
function proxyToBackend(req, res, path) {
  const backendReq = http.request(
    `${BACKEND_URL}${path}`,
    {
      method: req.method,
      headers: {
        ...req.headers,
        host: 'localhost:8000'
      }
    },
    (backendRes) => {
      // Copy response status and headers
      res.writeHead(backendRes.statusCode, backendRes.headers);
      // Pipe backend response to client
      backendRes.pipe(res);
    }
  );

  backendReq.on('error', (err) => {
    console.error('Backend proxy error:', err);
    res.writeHead(502, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Backend unavailable', message: err.message }));
  });

  // If it's a POST/PUT/PATCH request, pipe the request body to backend
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    req.pipe(backendReq);
  } else {
    backendReq.end();
  }
}

const server = http.createServer((req, res) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
  
  // Check if this is an API request - if so, proxy to backend
  if (req.url.startsWith('/api')) {
    console.log(`  -> Proxying to backend: ${BACKEND_URL}${req.url}`);
    return proxyToBackend(req, res, req.url);
  }

  let filePath = path.join(DIST_DIR, req.url === '/' ? 'index.html' : req.url);

  // Try to serve the file
  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // If file not found and it's not index.html, serve index.html instead (SPA routing)
        if (req.url !== '/index.html' && !req.url.includes('.')) {
          console.log(`  -> Serving index.html for SPA routing`);
          fs.readFile(path.join(DIST_DIR, 'index.html'), (err, content) => {
            if (err) {
              res.writeHead(500);
              res.end('Server error');
              return;
            }
            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.end(content);
          });
          return;
        }
        res.writeHead(404);
        res.end('Not found');
      } else {
        console.error('Error reading file:', err);
        res.writeHead(500);
        res.end('Server error');
      }
    } else {
      // Determine content type
      let contentType = 'text/html';
      if (filePath.endsWith('.js')) contentType = 'application/javascript';
      else if (filePath.endsWith('.css')) contentType = 'text/css';
      else if (filePath.endsWith('.json')) contentType = 'application/json';
      else if (filePath.endsWith('.svg')) contentType = 'image/svg+xml';
      else if (filePath.endsWith('.png')) contentType = 'image/png';
      else if (filePath.endsWith('.jpg') || filePath.endsWith('.jpeg')) contentType = 'image/jpeg';
      else if (filePath.endsWith('.gif')) contentType = 'image/gif';

      console.log(`  -> Serving ${filePath} as ${contentType}`);
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

server.on('error', (err) => {
  console.error('Server error:', err);
  if (err.code === 'EADDRINUSE') {
    console.error(`Port ${PORT} is already in use`);
  }
});

server.listen(PORT, HOST, () => {
  console.log(`\n🚀 Server running at http://localhost:${PORT}/`);
  console.log(`   DIST_DIR: ${DIST_DIR}\n`);
});
