const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

const DEFAULT_API_URL = 'https://www.packyapi.com/v1beta/models/gemini-3-pro-image-preview:generateContent';

function loadEnvFile() {
  const candidates = [
    process.env.ENV_FILE,
    process.env.NODE_ENV === 'production' ? '.env.production' : '.env.dev',
    '.env.production',
    '.env.dev',
    '.env',
  ].filter(Boolean);

  for (const filename of candidates) {
    const fullPath = path.resolve(process.cwd(), filename);
    if (fs.existsSync(fullPath)) {
      dotenv.config({ path: fullPath });
      return filename;
    }
  }

  return null;
}

const loadedEnvFile = loadEnvFile();

const config = {
  port: process.env.PORT || 10006,
  apiKey: process.env.GEMINI_API_KEY || process.env.LOCAL_GEMINI_API_KEY || 'YOUR_API_KEY_HERE',
  apiUrl: process.env.API_URL || DEFAULT_API_URL,
};

module.exports = {
  config,
  loadedEnvFile,
};
