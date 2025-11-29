# Gemini 3 Pro Image Chat

多轮对话式图片生成与编辑工具，基于 **Gemini 3 Pro Image Preview**，支持文本生图、多图合成、图片迭代编辑、搜索接地以及可选的 Thinking 可视化。

## 功能特性
- 文本生图 + 多轮上下文对话
- 多图合成（最多 14 张参考图）
- 基于上一张结果的迭代编辑
- 搜索接地模式（Google Search）
- Thinking 过程可视化开关
- 1:1 / 16:9 / 4:3 / 3:4 / 5:4 / 9:16 比例，2K/4K 尺寸
- 前端上传/预览/删除/下载完整链路

## 目录结构
```
├── server/                 # Node/Express 后端
│   ├── index.js            # 应用入口
│   ├── config/env.js       # 环境变量加载
│   ├── routes/chatRoutes.js# API 路由
│   ├── services/geminiImageChat.js
│   ├── store/conversationStore.js
│   └── middleware/...
├── client/                 # Vite + React 前端
│   ├── src/features/chat   # Chat 功能域（组件、hooks、api）
│   ├── src/components/ui   # 基础 UI 组件
│   └── vite.config.js      # 代理等配置
├── scripts/gemini_image_request.py # Python 示例脚本
├── package.json            # 根启动/构建脚本
└── pnpm-lock.yaml
```

## 快速开始
1) 安装依赖（根目录）
```bash
npm install
```

2) 配置密钥（任选其一环境文件）
```
.env.production  # 优先加载
.env.dev         # 开发默认回退
```
示例：
```
GEMINI_API_KEY=your_api_key_here
PORT=10006
# 可选：API_URL 自定义后端转发地址
```

3) 运行
```bash
# 启动服务（使用 client/dist 静态文件）
npm start

# 开发前端（会代理到本地 10006）
cd client && npm install && npm run dev
```
前端开发时可通过 `VITE_API_PROXY_TARGET` 覆盖代理目标。

4) 构建前端（生成 client/dist 供后端静态托管）
```bash
npm run build
```

## API 摘要
- `POST /api/generate-image` 文本/对话生图
- `POST /api/edit-image` 迭代编辑（基于上一张）
- `POST /api/composite-images` 多图合成（<=14）
- `POST /api/generate-with-search` 搜索接地生图
- `POST /api/reset-chat` 清除会话
- `GET  /api/chat-history/:sessionId` 查询历史
- `GET  /api/health` 健康检查

## 前端要点
- Chat 逻辑集中在 `src/features/chat`：
  - `hooks/useChatSession.js`：会话状态、上传、API 协调
  - `api/chatApi.js`：统一的 fetch 封装
  - `components/*`：头部、消息列表、输入面板解耦
- 14 张上传上限，超限时在消息流内提示
- Enter 发送，Shift+Enter 换行
- “Edit Last” 仅当存在上一张生成结果时可用

## 开发提示
- 依赖 Node 18+（使用原生 fetch）
- 后端静态目录：`client/dist`
- 想重置会话：点击右上角刷新图标或调用 `/api/reset-chat`

## Python 快速调用示例
`scripts/gemini_image_request.py` 提供了多轮对话、迭代编辑、多图合成的完整示例，可直接设置 `LOCAL_GEMINI_API_KEY` 运行。

## 许可证
MIT
