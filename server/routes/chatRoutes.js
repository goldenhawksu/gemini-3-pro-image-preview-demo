const express = require('express');
const { ensureChat, getChat, resetChat } = require('../store/conversationStore');
const { GeminiImageChat } = require('../services/geminiImageChat');

function normalizeImages(imageDataList = []) {
  return imageDataList.map((item) => {
    if (typeof item === 'string') {
      return { data: item, mimeType: 'image/png' };
    }
    return {
      data: item.data,
      mimeType: item.mimeType || 'image/png',
    };
  });
}

function createChatRouter(config) {
  const router = express.Router();

  const getOrCreateChat = (sessionId) =>
    ensureChat(sessionId, () => new GeminiImageChat(sessionId, config.apiUrl, config.apiKey));

  router.post('/generate-image', async (req, res, next) => {
    try {
      const { prompt, aspectRatio = '1:1', imageSize = '2K', sessionId, includeThinking = false } = req.body;

      if (!sessionId) return res.status(400).json({ error: '缺少 sessionId' });

      const chat = getOrCreateChat(sessionId);
      const response = await chat.sendMessage({ prompt, aspectRatio, imageSize, includeThinking });

      res.json(response);
    } catch (error) {
      next(error);
    }
  });

  router.post('/edit-image', async (req, res, next) => {
    try {
      const {
        imageData,
        editPrompt,
        aspectRatio = '1:1',
        imageSize = '2K',
        sessionId,
        includeThinking = false,
      } = req.body;

      if (!sessionId || !imageData || !editPrompt) {
        return res.status(400).json({ error: '缺少必要参数：sessionId, imageData, editPrompt' });
      }

      const chat = getOrCreateChat(sessionId);
      const response = await chat.sendMessage({
        prompt: editPrompt,
        images: [{ data: imageData, mimeType: 'image/png' }],
        aspectRatio,
        imageSize,
        includeThinking,
      });

      res.json(response);
    } catch (error) {
      next(error);
    }
  });

  router.post('/composite-images', async (req, res, next) => {
    try {
      const { prompt, imageDataList, aspectRatio = '5:4', imageSize = '2K', sessionId, includeThinking = false } = req.body;

      if (!sessionId || !prompt || !imageDataList || imageDataList.length === 0) {
        return res.status(400).json({ error: '缺少必要参数' });
      }

      if (imageDataList.length > 14) {
        return res.status(400).json({ error: '最多支持14张参考图片' });
      }

      const chat = getOrCreateChat(sessionId);
      const response = await chat.sendMessage({
        prompt,
        images: normalizeImages(imageDataList),
        aspectRatio,
        imageSize,
        includeThinking,
      });

      res.json(response);
    } catch (error) {
      next(error);
    }
  });

  router.post('/generate-with-search', async (req, res, next) => {
    try {
      const { prompt, aspectRatio = '16:9', imageSize = '2K', sessionId } = req.body;

      if (!sessionId || !prompt) {
        return res.status(400).json({ error: '缺少必要参数' });
      }

      const chat = getOrCreateChat(sessionId);
      const response = await chat.sendMessage({ prompt, aspectRatio, imageSize, useSearch: true });

      res.json(response);
    } catch (error) {
      next(error);
    }
  });

  router.post('/continue-chat', async (req, res, next) => {
    try {
      const { prompt, sessionId, aspectRatio = '1:1', imageSize = '2K' } = req.body;

      if (!sessionId || !prompt) {
        return res.status(400).json({ error: '缺少必要参数' });
      }

      const chat = getOrCreateChat(sessionId);
      const response = await chat.sendMessage({ prompt, aspectRatio, imageSize });

      res.json(response);
    } catch (error) {
      next(error);
    }
  });

  router.post('/reset-chat', (req, res) => {
    const { sessionId } = req.body;
    if (!sessionId) return res.status(400).json({ error: '缺少 sessionId' });

    resetChat(sessionId);
    res.json({ success: true, message: '对话已重置' });
  });

  router.get('/chat-history/:sessionId', (req, res) => {
    const { sessionId } = req.params;
    const chat = getChat(sessionId);
    if (!chat) return res.json({ history: [] });

    res.json({ history: chat.getHistory() });
  });

  return router;
}

module.exports = createChatRouter;
