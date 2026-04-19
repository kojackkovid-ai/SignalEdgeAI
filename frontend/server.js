const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const PORT = 3001;
const HOST = '0.0.0.0';
const DIST_DIR = path.join(__dirname, 'dist');

console.log('DIST_DIR:', DIST_DIR);
console.log('DIST_DIR exists:', fs.existsSync(DIST_DIR));

const server = http.createServer((req, res) => {
  console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
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
