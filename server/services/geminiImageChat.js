class GeminiImageChat {
  constructor(sessionId, apiUrl, apiKey) {
    this.sessionId = sessionId;
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
    this.conversationHistory = [];
    this.thoughtSignature = null;
  }

  buildUserMessage(prompt, images = []) {
    const parts = [{ text: prompt }];

    images.forEach(({ data, mimeType }) => {
      if (!data) return;
      parts.push({
        inline_data: {
          mime_type: mimeType || 'image/png',
          data,
        },
      });
    });

    return { role: 'user', parts };
  }

  extractImageData(response) {
    const candidate = response.candidates?.[0];
    if (!candidate) return null;

    const parts = candidate.content?.parts || [];
    for (const part of parts) {
      if (part.inlineData) {
        return part.inlineData.data;
      }
    }
    return null;
  }

  extractThinkingImages(response) {
    const thinkingImages = [];
    const candidate = response.candidates?.[0];
    if (!candidate) return thinkingImages;

    const parts = candidate.content?.parts || [];
    for (const part of parts) {
      if (part.thought && part.inlineData) {
        thinkingImages.push(part.inlineData.data);
      }
    }
    return thinkingImages;
  }

  buildAssistantMessageParts(response, includeThinking) {
    const parts = [];

    const thinkingImages = includeThinking ? this.extractThinkingImages(response) : [];
    if (thinkingImages.length > 0) {
      thinkingImages.forEach((img) => {
        parts.push({
          inlineData: { mime_type: 'image/png', data: img },
          thought: true,
        });
      });
    }

    const candidateParts = response.candidates?.[0]?.content?.parts || [];
    candidateParts.forEach((part) => {
      if (part.text) {
        parts.push({ text: part.text });
      } else if (part.inlineData) {
        parts.push({ inlineData: part.inlineData, thought: false });
      }
    });

    return { parts, thinkingImages };
  }

  extractText(response) {
    return response.candidates?.[0]?.content?.parts?.find((part) => part.text)?.text || '';
  }

  async sendMessage({
    prompt,
    images = [],
    aspectRatio = '1:1',
    imageSize = '2K',
    includeThinking = false,
    useSearch = false,
  }) {
    const userMessage = this.buildUserMessage(prompt, images);
    const contents = [...this.conversationHistory, userMessage];

    const payload = {
      contents,
      generationConfig: {
        responseModalities: ['TEXT', 'IMAGE'],
        imageConfig: {
          aspectRatio,
          imageSize,
        },
      },
    };

    if (useSearch) {
      payload.tools = [{ google_search: {} }];
    }

    const response = await fetch(this.apiUrl, {
      method: 'POST',
      headers: {
        'x-goog-api-key': this.apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API请求失败: ${response.status} - ${errorText}`);
    }

    const result = await response.json();

    this.conversationHistory.push(userMessage);

    const { parts, thinkingImages } = this.buildAssistantMessageParts(result, includeThinking);
    if (parts.length) {
      this.conversationHistory.push({
        role: 'assistant',
        parts,
      });
    }

    this.thoughtSignature = result.thought_signature || null;

    return {
      text: this.extractText(result),
      imageData: this.extractImageData(result),
      thinkingImages,
      thoughtSignature: this.thoughtSignature,
      groundingMetadata: result.groundingMetadata,
      rawResponse: result,
    };
  }

  reset() {
    this.conversationHistory = [];
    this.thoughtSignature = null;
  }

  getHistory() {
    return [...this.conversationHistory];
  }
}

module.exports = { GeminiImageChat };
