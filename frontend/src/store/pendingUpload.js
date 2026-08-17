import { buildAuthFetchOptions } from './auth.js'

const DB_NAME = 'tiresias-pending-upload'
const DB_VERSION = 1
const STORE_NAME = 'pending_uploads'
const CURRENT_KEY = 'current'
const REMOTE_PENDING_KEY = 'tiresias_pending_upload_remote'
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
let memoryPendingUpload = null

const EMPTY_PENDING_UPLOAD = Object.freeze({
  isPending: false,
  files: [],
  simulationRequirement: '',
  savedAt: null,
  pendingToken: null,
})

function canUseIndexedDb() {
  return typeof window !== 'undefined' && 'indexedDB' in window
}

function readRemotePendingMeta() {
  if (typeof window === 'undefined') return null
  try {
    return JSON.parse(window.localStorage.getItem(REMOTE_PENDING_KEY) || 'null')
  } catch {
    return null
  }
}

function writeRemotePendingMeta(value) {
  if (typeof window === 'undefined') return
  if (!value) {
    window.localStorage.removeItem(REMOTE_PENDING_KEY)
    return
  }
  window.localStorage.setItem(REMOTE_PENDING_KEY, JSON.stringify(value))
}

function openDb() {
  return new Promise((resolve, reject) => {
    if (!canUseIndexedDb()) {
      reject(new Error('IndexedDB unavailable'))
      return
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => {
      reject(request.error || new Error('Failed to open IndexedDB'))
    }

    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME)
      }
    }

    request.onsuccess = () => {
      resolve(request.result)
    }
  })
}

function runStore(mode, executor) {
  return openDb().then((db) => new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, mode)
    const store = tx.objectStore(STORE_NAME)

    tx.oncomplete = () => {
      db.close()
    }

    tx.onerror = () => {
      reject(tx.error || new Error('IndexedDB transaction failed'))
    }

    tx.onabort = () => {
      reject(tx.error || new Error('IndexedDB transaction aborted'))
    }

    executor(store, resolve, reject)
  }))
}

export async function setPendingUpload(files, simulationRequirement) {
  const payload = {
    files: Array.isArray(files) ? files : [],
    simulationRequirement: simulationRequirement || '',
    savedAt: new Date().toISOString()
  }

  memoryPendingUpload = payload
  const remoteSaved = await savePendingUploadRemotely(payload)
  let localSaved = false

  if (canUseIndexedDb()) {
    try {
      await runStore('readwrite', (store, resolve, reject) => {
        const request = store.put(payload, CURRENT_KEY)
        request.onsuccess = () => resolve(true)
        request.onerror = () => reject(request.error || new Error('Failed to save pending upload'))
      })
      localSaved = true
    } catch (error) {
      console.warn('Pending upload local save failed:', error)
    }
  }

  const remoteMeta = readRemotePendingMeta()
  return {
    saved: remoteSaved || localSaved,
    remoteToken: remoteMeta?.token || null,
    remoteSaved,
    localSaved,
  }
}

export async function getPendingUpload() {
  const memoryPayload = memoryPendingUpload

  if (!canUseIndexedDb()) {
    if (!memoryPayload?.files?.length) {
      return await getRemotePendingUpload()
    }

    return {
      isPending: true,
      files: memoryPayload.files,
      simulationRequirement: memoryPayload.simulationRequirement || '',
      savedAt: memoryPayload.savedAt || null,
      pendingToken: readRemotePendingMeta()?.token || null,
    }
  }

  try {
    const payload = await runStore('readonly', (store, resolve, reject) => {
      const request = store.get(CURRENT_KEY)
      request.onsuccess = () => resolve(request.result || null)
      request.onerror = () => reject(request.error || new Error('Failed to load pending upload'))
    })

    if (!payload || !Array.isArray(payload.files) || payload.files.length === 0) {
      if (!memoryPayload?.files?.length) {
        return await getRemotePendingUpload()
      }

      return {
        isPending: true,
        files: memoryPayload.files,
        simulationRequirement: memoryPayload.simulationRequirement || '',
        savedAt: memoryPayload.savedAt || null,
        pendingToken: readRemotePendingMeta()?.token || null,
      }
    }

    memoryPendingUpload = payload

    return {
      isPending: true,
      files: payload.files,
      simulationRequirement: payload.simulationRequirement || '',
      savedAt: payload.savedAt || null,
      pendingToken: readRemotePendingMeta()?.token || null,
    }
  } catch (error) {
    console.warn('Pending upload restore failed:', error)
    if (!memoryPayload?.files?.length) {
      return await getRemotePendingUpload()
    }

    return {
      isPending: true,
      files: memoryPayload.files,
      simulationRequirement: memoryPayload.simulationRequirement || '',
      savedAt: memoryPayload.savedAt || null,
      pendingToken: readRemotePendingMeta()?.token || null,
    }
  }
}

export async function clearPendingUpload() {
  memoryPendingUpload = null

  if (!canUseIndexedDb()) {
    await clearRemotePendingUpload()
    return
  }

  try {
    await runStore('readwrite', (store, resolve, reject) => {
      const request = store.delete(CURRENT_KEY)
      request.onsuccess = () => resolve()
      request.onerror = () => reject(request.error || new Error('Failed to clear pending upload'))
    })
  } catch (error) {
    console.warn('Pending upload clear failed:', error)
  }

  await clearRemotePendingUpload()
}

async function savePendingUploadRemotely(payload) {
  if (!API_BASE || !payload?.files?.length) return false

  try {
    await clearRemotePendingUpload()

    const formData = new FormData()
    payload.files.forEach((file) => formData.append('files', file))
    formData.append('simulation_requirement', payload.simulationRequirement || '')

    const response = await fetch(`${API_BASE}/api/files/pending-upload`, {
      method: 'POST',
      ...buildAuthFetchOptions(),
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Remote pending upload failed (${response.status})`)
    }

    const result = await response.json()
    const remote = result?.pendingUpload
    if (!remote?.token) return false

    writeRemotePendingMeta({
      token: remote.token,
      savedAt: remote.createdAt || payload.savedAt || null,
      fileCount: remote.fileCount || payload.files.length,
    })
    return true
  } catch (error) {
    console.warn('Remote pending upload save failed:', error)
    return false
  }
}

async function getRemotePendingUpload() {
  const remote = readRemotePendingMeta()
  if (!remote?.token || !API_BASE) {
    return { ...EMPTY_PENDING_UPLOAD }
  }

  try {
    const manifestRes = await fetch(
      `${API_BASE}/api/files/pending/${encodeURIComponent(remote.token)}`,
      buildAuthFetchOptions()
    )

    if (!manifestRes.ok) {
      throw new Error(`Remote pending manifest failed (${manifestRes.status})`)
    }

    const manifestPayload = await manifestRes.json()
    const pendingUpload = manifestPayload?.pendingUpload
    if (!pendingUpload?.files?.length) {
      return { ...EMPTY_PENDING_UPLOAD }
    }

    const restoredFiles = []
    for (const fileMeta of pendingUpload.files) {
      const fileRes = await fetch(
        `${API_BASE}/api/files/pending/${encodeURIComponent(remote.token)}/${fileMeta.index}`,
        buildAuthFetchOptions()
      )

      if (!fileRes.ok) {
        throw new Error(`Remote pending file restore failed (${fileRes.status})`)
      }

      const blob = await fileRes.blob()
      restoredFiles.push(new File([blob], fileMeta.name, {
        type: fileMeta.type || blob.type || 'application/octet-stream',
        lastModified: Date.now(),
      }))
    }

    const payload = {
      files: restoredFiles,
      simulationRequirement: pendingUpload.simulationRequirement || '',
      savedAt: pendingUpload.createdAt || remote.savedAt || null,
    }

    memoryPendingUpload = payload

    return {
      isPending: true,
      files: payload.files,
      simulationRequirement: payload.simulationRequirement,
      savedAt: payload.savedAt,
      pendingToken: remote.token,
    }
  } catch (error) {
    console.warn('Remote pending upload restore failed:', error)
    return { ...EMPTY_PENDING_UPLOAD }
  }
}

async function clearRemotePendingUpload() {
  const remote = readRemotePendingMeta()
  writeRemotePendingMeta(null)

  if (!remote?.token || !API_BASE) return

  try {
    await fetch(`${API_BASE}/api/files/pending/${encodeURIComponent(remote.token)}`, buildAuthFetchOptions({
      method: 'DELETE',
    }))
  } catch (error) {
    console.warn('Remote pending upload clear failed:', error)
  }
}
