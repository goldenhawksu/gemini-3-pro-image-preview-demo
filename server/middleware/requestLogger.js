module.exports = function requestLogger(req, _res, next) {
  const timestamp = new Date().toISOString();
  console.log(`[Request] ${timestamp} ${req.method} ${req.url}`);
  next();
};
