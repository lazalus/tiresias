import axios from 'axios'
import { getToken, logout } from '../store/auth.js'
import { formatCapacityMessage, getCapacityState, isCapacityError } from './capacity.js'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 300000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 요청 인터셉터: 자동으로 인증 헤더 추가
service.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터 (에러 재시도)
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // 성공이 아니면 에러 발생
    if (!res.success && res.success !== undefined) {
      console.error('API Error:', res.error || res.message || 'Unknown error')
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }
    
    return res
  },
  error => {
    console.error('Response error:', error)

    const serverMessage = error.response?.data?.error || error.response?.data?.message
    const capacityState = getCapacityState(error)

    if (isCapacityError(error) && capacityState) {
      error.isCapacityError = true
      error.capacity = capacityState.capacity
      error.retryAfter = capacityState.retryAfter
      error.message = formatCapacityMessage(error)
    } else if (serverMessage) {
      error.message = serverMessage
    }

    if (error.response?.status === 401) {
      logout()
      if (typeof window !== 'undefined' && !['/login', '/signup'].includes(window.location.pathname)) {
        window.location.assign('/login')
      }
    }
    
    // 타임아웃 처리
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timeout')
    }
    
    if (error.message === 'Network Error') {
      console.error('네트워크 오류')
    }

    return Promise.reject(error)
  }
)

// 재시도 포함 요청 함수
export const requestWithRetry = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      const status = error?.response?.status
      if (isCapacityError(error) || (status && status >= 400 && status < 500 && status !== 408)) {
        throw error
      }
      if (i === maxRetries - 1) throw error
      
      console.warn(`Request failed, retrying (${i + 1}/${maxRetries})...`)
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
    }
  }
}

export default service
