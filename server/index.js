const express = require('express');
const cors = require('cors');
const path = require('path');
const { config, loadedEnvFile } = require('./config/env');
const requestLogger = require('./middleware/requestLogger');
const errorHandler = require('./middleware/errorHandler');
const createChatRouter = require('./routes/chatRoutes');

const app = express();
const PORT = config.port;
const staticDir = path.resolve(__dirname, '../client/dist');

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(requestLogger);
app.use(express.static(staticDir));

app.use('/api', createChatRouter(config));

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('*', (_req, res, next) => {
  // Fallback to SPA index if it exists
  if (staticDir) {
    return res.sendFile(path.join(staticDir, 'index.html'), (err) => {
      if (err) next();
    });
  }
  return next();
});

app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`🚀 服务器运行在 http://localhost:${PORT}`);
  console.log(`📁 前端访问地址: http://localhost:${PORT}/`);
  console.log(`✅ 环境变量来源: ${loadedEnvFile || '系统环境变量/默认值'}`);
  console.log('🔑 请在 .env.production 或 .env.dev 中设置 GEMINI_API_KEY (或 LOCAL_GEMINI_API_KEY)');
});
