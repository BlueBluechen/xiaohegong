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
  // 诊断：?diag=1 时直接返回环境状态，不走方舟
  if ((req.url || '').includes('diag=1')) {
    const probe = {};
    for (const m of ['https', 'dns', 'net', 'tls', 'fs']) {
      try { probe[m] = !!require(m); } catch (e) { probe[m] = 'ERR:' + e.code; }
    }
    const body = JSON.stringify({
      ok: true,
      hasKey: !!ARK_KEY,
      keyLen: ARK_KEY ? ARK_KEY.length : 0,
      model: ARK_MODEL,
      url: ARK_URL,
      maxBody: MAX_BODY,
      modules: probe,
      node: process.version,
      pid: process.pid,
    });
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(body);
  }
  if (!ARK_KEY) {
    res.writeHead(503, { 'Content-Type': 'application/json; charset=utf-8' });
    return res.end(JSON.stringify({ ok: false, error: '服务端未配置 ARK_API_KEY' }));
  }

  // 诊断：?net=1 时测外网连通性（DNS + TCP + 一次真实请求）
  if ((req.url || '').includes('net=1')) {
    const t0 = Date.now();
    const out = { ok: true, steps: [] };
    const finish = () => {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify(out));
    };
    require('dns').lookup('ark.cn-beijing.volces.com', (e, addr) => {
      out.steps.push({ step: 'dns', ok: !e, addr: addr || null, err: e ? e.code : null, ms: Date.now() - t0 });
      if (e) return finish();
      const r = https.request({
        hostname: 'ark.cn-beijing.volces.com', path: '/api/v3/images/generations',
        method: 'POST', timeout: 8000,
        headers: { 'Content-Type': 'application/json', 'Content-Length': 2,
                   Authorization: 'Bearer ' + ARK_KEY },
      }, (resp) => {
        resp.resume();
        out.steps.push({ step: 'http', status: resp.statusCode, ms: Date.now() - t0 });
        finish();
      });
      r.on('timeout', () => { out.steps.push({ step: 'http', err: 'timeout', ms: Date.now() - t0 }); r.destroy(); finish(); });
      r.on('error', (err) => { out.steps.push({ step: 'http', err: err.code || err.message, ms: Date.now() - t0 }); finish(); });
      r.end('{}');
    });
    return;
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

  // 诊断：延迟 N 毫秒后返回，测网关/代理的首字节超时阈值
  if (urlPath0 === '/api/slow') {
    const q = new URL(req.url, 'http://x').searchParams;
    const t = Math.min(Math.max(Number(q.get('t')) || 1000, 1), 30000);
    const t0 = Date.now();
    setTimeout(() => {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: true, slept: t, ms: Date.now() - t0 }));
    }, t);
    return;
  }

  // 诊断：async handler 立即返回，对比回调式
  if (urlPath0 === '/api/asyncpost') {
    (async () => {
      let n = 0;
      const chunks = [];
      await new Promise(ok => {
        req.on('data', c => { n += c.length; chunks.push(c); });
        req.on('end', ok);
      });
      await new Promise(r => setTimeout(r, 5));
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: true, async: true, bytes: n }));
    })();
    return;
  }

  // 诊断：立即返回的 POST，用来判断 POST 本身是否被网关拦
  if (urlPath0 === '/api/posttest') {
    if (req.method !== 'POST') {
      res.writeHead(405, { 'Content-Type': 'application/json; charset=utf-8' });
      return res.end('{"ok":false,"error":"POST only"}');
    }
    let n = 0;
    req.on('data', c => { n += c.length; });
    req.on('end', () => {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ ok: true, bytes: n }));
    });
    return;
  }

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

  // 诊断接口：分别测「同步」「微任务」「宏任务」三种响应方式
  if (urlPath === '/api/ping') {
    const mode = (req.url.split('mode=')[1] || 'sync').split('&')[0];
    const body = JSON.stringify({ ok: true, mode });
    const send = () => {
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(body);
    };
    if (mode === 'sync')   return send();
    if (mode === 'tick')   return process.nextTick(send);
    if (mode === 'promise') return Promise.resolve().then(send);
    if (mode === 'timeout') return setTimeout(send, 0);
    return send();
  }

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
