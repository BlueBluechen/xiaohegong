const http = require('http');
const fs = require('fs');
const path = require('path');
const https = require('https');

const PORT = process.env.PORT || 8080;
const ROOT = __dirname;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.ico':  'image/x-icon',
  '.txt':  'text/plain; charset=utf-8'
};

/* ============================================================
   /api/stamp —— 照片转拓印卡的代理
   ------------------------------------------------------------
   为什么要有这个端点：
     前端 HTML 是公开的，绝不能放 ARK key。key 只在这里读环境变量。
   约束：
     请求体限制 8MB（base64 后约 6MB 原图），超了直接拒。
     每次调用都花真钱，所以只接受 POST + 合法 JSON。
   ============================================================ */
const ARK_KEY = process.env.ARK_API_KEY || '';
const ARK_MODEL = process.env.ARK_MODEL || 'doubao-seedream-5-0-flash-260915';
const ARK_URL = 'https://ark.cn-beijing.volces.com/api/v3/images/generations';
const MAX_BODY = 8 * 1024 * 1024;

const INK = {
  swan:   '深色羽毛禁用死黑，用炭灰、墨蓝灰、深褐灰层层半透明叠印',
  bridge: '墙体用赭红、陶土赤褐半透明叠印，屋顶用灰蓝',
  sluice: '墙体用灰蓝、鼠尾草青，孔洞保留纸底留白',
  reed:   '浅色花穗以暖白米白为主，茎叶用橄榄绿、浅抹茶绿干刷',
};

function buildPrompt(subject) {
  const ink = INK[subject] || INK.swan;
  return '请基于参考图制作一张纯拓印插画，1:1 方形构图。\n' +
    '画面整张都是干净的拓印插画风格，不出现任何文字、字母、数字、水印。\n\n' +
    '1. 主体与构图：参考图中最有记忆点的单一主体位于画面正中央，水平垂直均居中；' +
    '主体约占画面 55%~65%，四周保留舒展的暖白或浅米白艺术纸底留白，呼吸感充足。\n' +
    '2. 主体提取：只保留核心主体与少量必要陪体，省略背景杂物；' +
    '外轮廓呈手工剪纸或版画刀刻般干净利落的弧线与几何切面，完全不使用黑色勾线描边，' +
    '边界与纸底清晰分明。\n' +
    '3. 拓印质感：内部采用孔版丝网半透明叠印与海绵拓包干压结合的弥散颗粒质感；' +
    ink + '；受光处保留干擦飞白，色块内部由浓到淡弥散渐变，明快干净、透气，' +
    '避免厚重浑浊与 neon 艳色。\n' +
    '4. 整体去繁就简、主体居中、外轮廓利落现代、配色低饱和通透清新、留白舒展、简约高级。';
}

function postJSON(url, payload, headers, timeout = 120000) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = Buffer.from(JSON.stringify(payload));
    const req = https.request({
      hostname: u.hostname, path: u.pathname + u.search, method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json',
                               'Content-Length': body.length }, headers),
      timeout,
    }, (r) => {
      const chunks = [];
      r.on('data', c => chunks.push(c));
      r.on('end', () => resolve({ status: r.statusCode, text: Buffer.concat(chunks).toString() }));
    });
    req.on('timeout', () => { req.destroy(new Error('upstream timeout')); });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function fetchBinary(url) {
  return new Promise((resolve) => {
    const u = new URL(url);
    https.get({ hostname: u.hostname, path: u.pathname + u.search, timeout: 60000 }, (r) => {
      if (r.statusCode !== 200) { r.resume(); return resolve(null); }
      const cs = [];
      r.on('data', c => cs.push(c));
      r.on('end', () => resolve(Buffer.concat(cs)));
    }).on('error', () => resolve(null))
      .on('timeout', function () { this.destroy(); resolve(null); });
  });
}

function handleStamp(req, res) {
  if (!ARK_KEY) {
    res.writeHead(503, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ ok: false, error: '服务端未配置 ARK_API_KEY' }));
  }

  let size = 0;
  const chunks = [];
  let aborted = false;

  req.on('data', c => {
    size += c.length;
    if (size > MAX_BODY && !aborted) {
      aborted = true;
      res.writeHead(413, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: false, error: '照片太大，请压缩到 6MB 以内' }));
      req.destroy();
      return;
    }
    if (!aborted) chunks.push(c);
  });

  req.on('end', async () => {
    if (aborted) return;
    let payload;
    try {
      payload = JSON.parse(Buffer.concat(chunks).toString());
    } catch (e) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ ok: false, error: '请求不是合法 JSON' }));
    }

    // 图片入参：优先收「裸 base64 + mime」，兼容旧的 data URL
    //
    // 为什么要改：火山 API 网关会拦截含小写 "data:image" 的请求体，
    // 直接 504（0.1 秒，函数根本没收到）。实测 DATA:IMAGE 大写、
    // data:foo/bar、image/jpeg;base64 都能过，只有 data:image 不行。
    // 所以前端改发裸 base64，服务端自己拼成 data URL 再送方舟。
    let image = null;
    const raw = payload.image;
    if (typeof raw === 'string' && raw) {
      if (raw.startsWith('data:image/')) {
        image = raw;                                  // 旧格式，照旧
      } else if (/^[A-Za-z0-9+/=\s]+$/.test(raw)) {
        const mime = typeof payload.mime === 'string' && payload.mime
          ? payload.mime : 'image/jpeg';
        image = 'data:' + mime + ';base64,' + raw.replace(/\s/g, '');
      }
    } else if (typeof payload.imageBase64 === 'string' && payload.imageBase64) {
      const mime = typeof payload.mime === 'string' && payload.mime
        ? payload.mime : 'image/jpeg';
      image = 'data:' + mime + ';base64,' + payload.imageBase64.replace(/\s/g, '');
    }

    if (!image) {
      res.writeHead(400, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({
        ok: false,
        error: '缺图片：请传 image（裸 base64）或 imageBase64，可附 mime'
      }));
    }

    try {
      const up = await postJSON(ARK_URL, {
        model: ARK_MODEL,
        prompt: buildPrompt(payload.subject),
        image: [image],
        size: payload.size || '2K',
        response_format: 'url',
        watermark: false,            // 不要「AI生成」水印
      }, { Authorization: 'Bearer ' + ARK_KEY });

      if (up.status !== 200) {
        res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ ok: false, error: 'upstream ' + up.status,
                                        detail: up.text.slice(0, 300) }));
      }

      const d = JSON.parse(up.text);
      const url = d && d.data && d.data[0] && d.data[0].url;
      if (!url) {
        res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ ok: false, error: '上游没返回图片地址' }));
      }

      /* 关键：把图取回来转 base64 一起返回。
         为什么不直接给前端 URL：TOS 直链没有 CORS 头，浏览器 fetch 不到，
         前端就没法裁切成卡片要的 2:1，只能降级。服务端取图没有这个限制。 */
      const img = await fetchBinary(url);
      if (!img) {
        res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
        return res.end(JSON.stringify({ ok: false, error: '取图失败' }));
      }

      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: true,
                               image: 'data:image/png;base64,' + img.toString('base64') }));
    } catch (e) {
      res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: false, error: String(e.message || e).slice(0, 200) }));
    }
  });
}

const server = http.createServer((req, res) => {
  const urlPath0 = decodeURIComponent((req.url || '/').split('?')[0]);

  // 拓印代理：唯一允许 POST 的路径
  if (urlPath0 === '/api/stamp') {
    if (req.method !== 'POST') {
      res.writeHead(405, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end(JSON.stringify({ ok: false, error: '只接 POST' }));
    }
    return handleStamp(req, res);
  }

  // 其余只处理 GET / HEAD
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('Method Not Allowed');
  }

  let urlPath = urlPath0;

  // 健康检查
  if (urlPath === '/health' || urlPath === '/healthz') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ ok: true, service: 'xiaohegong' }));
  }

  // 根路径 → index.html
  if (urlPath === '/' || urlPath === '') urlPath = '/index.html';

  // 防目录穿越
  const filePath = path.join(ROOT, path.normalize(urlPath).replace(/^(\.\.[\/\\])+/, ''));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('Forbidden');
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      // 未找到 → 回落到 index.html（单页应用习惯）
      fs.readFile(path.join(ROOT, 'index.html'), (e2, d2) => {
        if (e2) {
          res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
          return res.end('Not Found');
        }
        res.writeHead(200, {
          'Content-Type': 'text/html; charset=utf-8',
          'Content-Disposition': 'inline',
          'Cache-Control': 'no-cache'
        });
        res.end(d2);
      });
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Content-Disposition': 'inline',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=3600',
      'X-Content-Type-Options': 'nosniff'
    });
    res.end(data);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`xiaohegong listening on ${PORT}`);
});
