import api from './index.js'
import { buildAuthAxiosConfig } from '../store/auth.js'

export const sendSupportFeedback = async (payload, token = null) => {
  const res = await api.post('/api/support/feedback', payload, buildAuthAxiosConfig())
  return res.data
}
