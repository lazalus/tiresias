import { buildAuthFetchOptions } from '../store/auth.js'

function normalizeFileName(value) {
  return String(value || '보고서')
    .replace(/[\\/:*?"<>|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim() || '보고서'
}

export function readPendingOrder() {
  try {
    return JSON.parse(localStorage.getItem('pending_order') || 'null')
  } catch {
    return null
  }
}

export function savePendingOrder(value) {
  localStorage.setItem('pending_order', JSON.stringify(value))
}

export function clearPendingOrder() {
  localStorage.removeItem('pending_order')
}

export async function tryDownloadReportPdf({ apiBase, reportId, fileName }) {
  const res = await fetch(
    `${apiBase}/api/report/pdf/${encodeURIComponent(reportId)}`,
    buildAuthFetchOptions()
  )

  if (res.ok) {
    const blob = await res.blob()
    downloadPdfBlob(blob, fileName)
    return { success: true, downloaded: true }
  }

  let errorData = null
  try {
    errorData = await res.json()
  } catch {
    errorData = null
  }

  throw new Error(errorData?.error || 'PDF 다운로드에 실패했습니다.')
}

export async function downloadConfirmedPdf({ apiBase, reportId, title }) {
  const result = await tryDownloadReportPdf({
    apiBase,
    reportId,
    fileName: title,
  })

  if (!result.downloaded) {
    throw new Error('결제는 완료되었지만 PDF 다운로드를 시작하지 못했습니다.')
  }

  return result
}

export function downloadPdfBlob(blob, fileName) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${normalizeFileName(fileName)}.pdf`
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
