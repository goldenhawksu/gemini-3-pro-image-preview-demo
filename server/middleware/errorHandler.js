module.exports = function errorHandler(err, _req, res, _next) {
  console.error('服务器错误:', err);
  const status = err.status || 500;
  res.status(status).json({
    error: err.message || '服务器内部错误',
  });
};
