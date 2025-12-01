# Gemini Image Chat

基于 Gemini 3 Pro Image Preview API 的图片生成聊天客户端。

## 功能

- 文本生成图片
- 多图上传与合成
- 图片编辑
- 调整宽高比 (1:1, 3:4, 4:3, 9:16, 16:9)
- 调整尺寸 (512px, 1K, 2K, 4K, 8K)
- Google Search 集成
- 图片下载

## 技术栈

- React 18 + Vite
- Tailwind CSS + Radix UI
- Gemini 3 Pro Image Preview API

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 配置

首次运行需要配置：
- API URL (默认代理到 `http://localhost:10006`)
- Gemini API Key

配置保存在 localStorage 中。

## API 端点

```
POST /v1beta/models/gemini-3-pro-image-preview:generateContent
```

需要在请求头中包含 `x-goog-api-key`。

## 许可

MIT
