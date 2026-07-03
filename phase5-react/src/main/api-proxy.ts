import { session } from 'electron';
import * as http from 'node:http';
import * as https from 'node:https';
import { URL } from 'node:url';

const TARGET_API_HOST = 'api.lexprime.cn';
const PROXY_PORT = 8081;

export function setupApiProxy(): void {
  const server = http.createServer((req, res) => {
    if (!req.url) {
      res.writeHead(400);
      res.end('Bad Request');
      return;
    }

    const url = new URL(req.url, `http://${TARGET_API_HOST}`);
    
    const options: https.RequestOptions = {
      hostname: TARGET_API_HOST,
      port: 443,
      path: `${url.pathname}${url.search}`,
      method: req.method,
      headers: {
        ...req.headers,
        host: TARGET_API_HOST,
        origin: `https://${TARGET_API_HOST}`,
        referer: `https://${TARGET_API_HOST}`,
      },
    };

    const proxyReq = https.request(options, (proxyRes) => {
      res.writeHead(proxyRes.statusCode || 500, {
        ...proxyRes.headers,
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      });
      proxyRes.pipe(res, { end: true });
    });

    proxyReq.on('error', (err) => {
      console.error('[api-proxy] error:', err);
      res.writeHead(500);
      res.end(`Proxy Error: ${err.message}`);
    });

    req.pipe(proxyReq, { end: true });
  });

  server.listen(PROXY_PORT, () => {
    console.log(`[api-proxy] running on http://localhost:${PROXY_PORT}`);
  });

  session.defaultSession.webRequest.onBeforeSendHeaders((details, callback) => {
    callback({
      requestHeaders: {
        ...details.requestHeaders,
        'Origin': `http://localhost:${PROXY_PORT}`,
      },
    });
  });

  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Access-Control-Allow-Origin': '*',
      },
    });
  });
}