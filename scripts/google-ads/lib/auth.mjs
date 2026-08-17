export const getGoogleAdsAccessToken = async (config) => {
  const body = new URLSearchParams({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    refresh_token: config.refreshToken,
    grant_type: 'refresh_token',
  })

  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Failed to refresh Google OAuth token (${response.status}): ${text}`)
  }

  const payload = await response.json()
  if (!payload.access_token) {
    throw new Error('Google OAuth response did not contain access_token')
  }

  return payload.access_token
}
