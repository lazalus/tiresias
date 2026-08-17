import crypto from 'node:crypto'

export const createNaverAdsSignature = ({ timestamp, method, uri, secretKey }) => {
  const message = `${timestamp}.${String(method || '').toUpperCase()}.${uri}`
  return crypto.createHmac('sha256', secretKey).update(message).digest('base64')
}

export const buildNaverAdsHeaders = ({ method, uri, config, timestamp = Date.now().toString() }) => {
  return {
    'Content-Type': 'application/json; charset=UTF-8',
    'X-Timestamp': timestamp,
    'X-API-KEY': config.accessLicense,
    'X-Customer': config.customerId,
    'X-Signature': createNaverAdsSignature({
      timestamp,
      method,
      uri,
      secretKey: config.secretKey,
    }),
  }
}
