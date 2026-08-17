import { renderMarkdown } from './markdown.js'

const OFFICIAL_ACCENT = '#2d4c88'
const OFFICIAL_ACCENT_LIGHT = '#e7eef9'
const OFFICIAL_ACCENT_MINT = '#dff1ec'
const OFFICIAL_BORDER = '#b9c3d6'
const OFFICIAL_TEXT = '#172033'
const OFFICIAL_MUTED = '#5a6477'

export function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function stripSectionPrefix(title) {
  return String(title || '')
    .replace(/^#+\s*/, '')
    .replace(/^\s*제?\s*\d+\s*(장|절|항)\s*/u, '')
    .replace(/^\s*[IVXLC]+\.\s*/iu, '')
    .replace(/^\s*\d+[\.\)]\s*/u, '')
    .trim()
}

export function normalizeSectionTitle(title, index) {
  const baseTitle = stripSectionPrefix(title) || `주요 분석 ${index + 1}`
  return `제${index + 1}장 ${baseTitle}`
}

export function buildExecutiveSummaryPoints(summary) {
  const cleaned = String(summary || '')
    .replace(/\s+/g, ' ')
    .trim()

  if (!cleaned) return []

  return cleaned
    .split(/(?<=[.!?]|다\.)\s+/u)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .slice(0, 4)
}

function toRoman(value) {
  const numerals = [
    ['M', 1000], ['CM', 900], ['D', 500], ['CD', 400], ['C', 100],
    ['XC', 90], ['L', 50], ['XL', 40], ['X', 10], ['IX', 9],
    ['V', 5], ['IV', 4], ['I', 1],
  ]

  let remaining = Math.max(1, Number(value) || 1)
  let result = ''

  for (const [symbol, amount] of numerals) {
    while (remaining >= amount) {
      result += symbol
      remaining -= amount
    }
  }

  return result
}

function stripMarkdownForEstimate(content) {
  return String(content || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]+`/g, ' ')
    .replace(/^#+\s+/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/>\s?/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_(.*?)_/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()
}

function estimateSectionPageSpan(content) {
  const plain = stripMarkdownForEstimate(content)
  if (!plain) return 1

  const headings = (String(content || '').match(/^#{1,5}\s+/gm) || []).length
  const bullets = (String(content || '').match(/^\s*(?:[-*+]|\d+\.)\s+/gm) || []).length
  const quotes = (String(content || '').match(/^>\s+/gm) || []).length
  const codeBlocks = (String(content || '').match(/```/g) || []).length / 2

  const weightedLength =
    plain.length +
    headings * 220 +
    bullets * 90 +
    quotes * 120 +
    codeBlocks * 480

  return Math.max(1, Math.ceil(weightedLength / 2300))
}

function formatIssueDate(iso) {
  const date = new Date(iso || Date.now())
  if (Number.isNaN(date.getTime())) return '발행일 미상'

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}. ${month}. ${day}.`
}

function formatIssueMonth(iso) {
  const date = new Date(iso || Date.now())
  if (Number.isNaN(date.getTime())) return '발행월 미상'

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  return `${year}. ${month}`
}

function buildDocumentCode(reportId) {
  if (!reportId) return 'TV-REPORT-DRAFT'
  return `TV-${String(reportId).replace(/[^a-zA-Z0-9]/g, '').slice(-10).toUpperCase()}`
}

function buildTocEntries(sections, includeSummaryPage) {
  let currentPage = includeSummaryPage ? 3 : 2
  const entries = []

  if (includeSummaryPage) {
    entries.push({
      indexLabel: '요약',
      title: '검토 요약 및 핵심 포인트',
      page: currentPage,
      depth: 'summary',
    })
    currentPage += 1
  }

  ;(sections || []).forEach((section, index) => {
    entries.push({
      indexLabel: `${toRoman(index + 1)}.`,
      title: stripSectionPrefix(section?.title) || `주요 분석 ${index + 1}`,
      page: currentPage,
      depth: 'section',
    })
    currentPage += estimateSectionPageSpan(section?.content || '')
  })

  return entries
}

export function buildRefinedReportDocument({
  title,
  summary,
  sections,
  generatedAt,
}) {
  const normalizedSections = (sections || []).map((section, index) => ({
    title: normalizeSectionTitle(section?.title, index),
    content: section?.content || '',
  }))

  return {
    title: String(title || '정책 시뮬레이션 분석보고서').trim(),
    summary: String(summary || '').trim(),
    sections: normalizedSections,
    generated_at: generatedAt || new Date().toISOString(),
    format: 'ko-government-report-v1',
  }
}

export function buildOfficialReportHtml(report, reportId = '') {
  const issuedDate = formatIssueDate(report.generated_at)
  const issuedMonth = formatIssueMonth(report.generated_at)
  const summaryPoints = buildExecutiveSummaryPoints(report.summary)
  const reportCode = buildDocumentCode(reportId)
  const includeSummaryPage = summaryPoints.length > 0
  const tocEntries = buildTocEntries(report.sections || [], includeSummaryPage)

  let html = ''

  html += `<section class="pdf-page pdf-cover">`
  html += `<div class="cover-classification">[정책검토용]</div>`
  html += `<div class="cover-title-stack">`
  html += `<div class="cover-rule cover-rule-top"></div>`
  html += `<div class="cover-title-frame">`
  html += `<div class="cover-type">정책 시뮬레이션 분석보고서</div>`
  html += `<h1 class="cover-title">${escapeHtml(report.title || '정책 시뮬레이션 분석보고서')}</h1>`
  html += `</div>`
  html += `<div class="cover-rule cover-rule-bottom"></div>`
  html += `</div>`
  html += `<div class="cover-middle-meta">${escapeHtml(issuedMonth)}</div>`
  html += `<div class="cover-summary-box">`
  html += `<div class="cover-summary-label">검토 주제</div>`
  html += `<p class="cover-summary-text">${escapeHtml(report.summary || '업로드 자료와 시뮬레이션 결과를 바탕으로 작성한 정책 검토용 분석보고서입니다.')}</p>`
  html += `</div>`
  html += `<div class="cover-footer">`
  html += `<div class="cover-footer-meta">`
  html += `<div>문서번호 ${escapeHtml(reportCode)}</div>`
  html += `<div>발 행 일 ${escapeHtml(issuedDate)}</div>`
  html += `</div>`
  html += `</div>`
  html += `</section>`

  html += `<section class="pdf-page pdf-toc page-break">`
  html += `<div class="page-kicker">목차</div>`
  html += `<h2 class="toc-title-main">목 차</h2>`
  html += `<div class="toc-divider"></div>`
  html += `<div class="toc-list">`
  tocEntries.forEach((entry) => {
    html += `<div class="toc-item toc-item--${entry.depth}">`
    html += `<span class="toc-index">${escapeHtml(entry.indexLabel)}</span>`
    html += `<span class="toc-entry-title">${escapeHtml(entry.title)}</span>`
    html += `<span class="toc-leader"></span>`
    html += `<span class="toc-page">${escapeHtml(entry.page)}</span>`
    html += `</div>`
  })
  html += `</div>`
  html += `<div class="toc-footnote">※ 본 문서는 시뮬레이션 결과를 제출용 형식으로 재구성한 분석용 편집본입니다.</div>`
  html += `</section>`

  if (includeSummaryPage) {
    html += `<section class="pdf-page pdf-summary page-break">`
    html += `<div class="section-topline"></div>`
    html += `<div class="section-band section-band--summary">`
    html += `<span class="section-band-index">요약</span>`
    html += `<span class="section-band-title">검토 요약 및 핵심 포인트</span>`
    html += `</div>`
    html += `<ol class="official-summary-list">`
    summaryPoints.forEach((point) => {
      html += `<li>${escapeHtml(point)}</li>`
    })
    html += `</ol>`
    html += `<div class="official-note-box">`
    html += `<div class="official-note-label">검토 메모</div>`
    html += `<p>본 요약은 업로드 자료, 그래프 구조, 시뮬레이션 결과를 종합해 의사결정자가 빠르게 검토할 수 있도록 정리한 핵심 문장입니다.</p>`
    html += `</div>`
    html += `</section>`
  }

  ;(report.sections || []).forEach((section, index) => {
    const cleanTitle = stripSectionPrefix(section?.title) || `주요 분석 ${index + 1}`
    html += `<section class="pdf-page pdf-section page-break">`
    html += `<div class="section-topline"></div>`
    html += `<div class="section-band">`
    html += `<span class="section-band-index">${toRoman(index + 1)}.</span>`
    html += `<span class="section-band-title">${escapeHtml(cleanTitle)}</span>`
    html += `</div>`
    html += `<div class="section-content-official">${renderMarkdown(section?.content || '')}</div>`
    html += `</section>`
  })

  return html
}

export function buildOfficialPdfDocumentHtml(report, reportId = '') {
  const bodyHtml = buildOfficialReportHtml(report, reportId)
  const pdfTitle = escapeHtml(report.title || '정책 시뮬레이션 분석보고서')

  return `<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>${pdfTitle}</title>
  <style>
    @page {
      size: A4;
      margin: 18mm 16mm 18mm 16mm;
    }
    @media print {
      body {
        margin: 0;
        print-color-adjust: exact;
        -webkit-print-color-adjust: exact;
      }
      .page-break {
        break-before: page;
        page-break-before: always;
      }
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      background: #fff;
      color: ${OFFICIAL_TEXT};
      font-family: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.82;
      letter-spacing: -0.01em;
    }
    .pdf-page {
      width: 100%;
      min-height: calc(297mm - 36mm);
    }
    .pdf-cover {
      position: relative;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 2mm 2mm 4mm;
      color: ${OFFICIAL_TEXT};
    }
    .cover-classification {
      text-align: right;
      color: ${OFFICIAL_ACCENT};
      font-weight: 700;
      font-size: 10pt;
      letter-spacing: 0.01em;
    }
    .cover-title-stack {
      margin-top: 22mm;
    }
    .cover-rule {
      height: 4.5mm;
      background: linear-gradient(90deg, #d8f2f1 0%, #88a8e6 45%, ${OFFICIAL_ACCENT} 100%);
    }
    .cover-rule-top {
      margin-bottom: 7mm;
    }
    .cover-rule-bottom {
      margin-top: 7mm;
    }
    .cover-title-frame {
      padding: 0 12mm;
      text-align: center;
    }
    .cover-type {
      margin-bottom: 5mm;
      font-size: 10pt;
      font-weight: 700;
      color: ${OFFICIAL_MUTED};
      letter-spacing: 0.08em;
    }
    .cover-title {
      margin: 0;
      font-size: 24pt;
      line-height: 1.35;
      font-weight: 800;
      color: ${OFFICIAL_ACCENT};
      word-break: keep-all;
    }
    .cover-middle-meta {
      margin-top: 16mm;
      text-align: center;
      font-size: 16pt;
      font-weight: 700;
      color: ${OFFICIAL_TEXT};
      letter-spacing: 0.04em;
    }
    .cover-summary-box {
      margin: 0 auto;
      width: 100%;
      border: 1px solid ${OFFICIAL_BORDER};
      padding: 6mm 7mm;
      background: #fbfcff;
    }
    .cover-summary-label {
      margin-bottom: 2.5mm;
      font-size: 9.5pt;
      font-weight: 700;
      color: ${OFFICIAL_ACCENT};
    }
    .cover-summary-text {
      margin: 0;
      font-size: 10.6pt;
      color: ${OFFICIAL_TEXT};
      white-space: pre-wrap;
    }
    .cover-footer {
      text-align: center;
    }
    .cover-footer-meta {
      display: inline-flex;
      flex-direction: column;
      gap: 1.2mm;
      font-size: 10pt;
      color: ${OFFICIAL_MUTED};
      text-align: center;
    }
    .page-kicker {
      color: ${OFFICIAL_MUTED};
      font-size: 9.6pt;
      font-weight: 700;
      margin-bottom: 7mm;
    }
    .toc-title-main {
      margin: 0;
      text-align: center;
      font-size: 22pt;
      font-weight: 800;
      letter-spacing: 0.28em;
      color: #111827;
    }
    .toc-divider {
      margin: 8mm 0 12mm;
      border-top: 1.4px solid #5f6675;
    }
    .toc-list {
      display: flex;
      flex-direction: column;
      gap: 4mm;
      min-height: 160mm;
    }
    .toc-item {
      display: flex;
      align-items: baseline;
      gap: 3mm;
      font-size: 11.4pt;
      color: ${OFFICIAL_TEXT};
    }
    .toc-item--summary {
      margin-bottom: 2mm;
    }
    .toc-index {
      width: 18mm;
      flex-shrink: 0;
      font-weight: 700;
    }
    .toc-entry-title {
      max-width: 122mm;
      word-break: keep-all;
    }
    .toc-leader {
      flex: 1;
      border-bottom: 1px dotted #7d8596;
      transform: translateY(-1.5mm);
      min-width: 10mm;
    }
    .toc-page {
      width: 12mm;
      text-align: right;
      font-weight: 700;
    }
    .toc-footnote {
      margin-top: 14mm;
      padding: 5mm 6mm;
      border: 1px solid #d5d9e2;
      color: ${OFFICIAL_MUTED};
      font-size: 9.6pt;
      background: #fcfcfd;
    }
    .section-topline {
      width: 100%;
      height: 2.2mm;
      margin-bottom: 4mm;
      background: linear-gradient(90deg, #d3f0ee 0%, #9ec0f2 50%, ${OFFICIAL_ACCENT} 100%);
    }
    .section-band {
      display: flex;
      align-items: center;
      gap: 4mm;
      padding: 3.8mm 5mm;
      border: 1px solid #bfd3e5;
      background: linear-gradient(90deg, ${OFFICIAL_ACCENT_LIGHT} 0%, #f5fbff 74%, ${OFFICIAL_ACCENT_MINT} 100%);
      margin-bottom: 8mm;
    }
    .section-band--summary {
      background: linear-gradient(90deg, #eef4ff 0%, #f8fcff 68%, #eef8f4 100%);
    }
    .section-band-index {
      font-size: 12pt;
      font-weight: 800;
      color: ${OFFICIAL_ACCENT};
      flex-shrink: 0;
    }
    .section-band-title {
      font-size: 17pt;
      font-weight: 800;
      color: ${OFFICIAL_TEXT};
      word-break: keep-all;
    }
    .official-summary-list {
      margin: 0 0 9mm;
      padding-left: 6mm;
    }
    .official-summary-list li {
      margin-bottom: 4mm;
      font-size: 11.1pt;
    }
    .official-note-box {
      padding: 5.5mm 6mm;
      border: 1px solid ${OFFICIAL_BORDER};
      background: #fbfcff;
    }
    .official-note-label {
      margin-bottom: 2mm;
      color: ${OFFICIAL_ACCENT};
      font-size: 9.4pt;
      font-weight: 700;
    }
    .official-note-box p {
      margin: 0;
      font-size: 10.3pt;
      color: ${OFFICIAL_MUTED};
    }
    .section-content-official {
      font-size: 10.6pt;
      color: ${OFFICIAL_TEXT};
    }
    .section-content-official .md-p {
      margin: 0 0 4.4mm;
    }
    .section-content-official .md-h2,
    .section-content-official .md-h3,
    .section-content-official .md-h4,
    .section-content-official .md-h5 {
      margin: 8mm 0 3mm;
      color: ${OFFICIAL_TEXT};
      font-weight: 800;
      word-break: keep-all;
    }
    .section-content-official .md-h2 {
      font-size: 14pt;
      padding: 2.2mm 3mm;
      background: #eff5fb;
      border-left: 4px solid ${OFFICIAL_ACCENT};
    }
    .section-content-official .md-h3 { font-size: 12.8pt; }
    .section-content-official .md-h4 { font-size: 11.8pt; }
    .section-content-official .md-h5 { font-size: 11pt; }
    .section-content-official .md-ul,
    .section-content-official .md-ol {
      margin: 0 0 4.4mm;
      padding-left: 6mm;
    }
    .section-content-official .md-li,
    .section-content-official .md-oli {
      margin-bottom: 2.1mm;
    }
    .section-content-official strong {
      color: ${OFFICIAL_ACCENT};
      font-weight: 800;
    }
    .section-content-official .md-quote {
      margin: 5mm 0;
      padding: 4mm 5mm;
      border: 1px solid #c5d4e6;
      border-left: 4px solid ${OFFICIAL_ACCENT};
      background: #f8fbff;
      color: #324158;
    }
    .section-content-official .code-block {
      white-space: pre-wrap;
      padding: 4mm;
      background: #f8fafc;
      border: 1px solid #d7dde7;
      font-size: 9.4pt;
      line-height: 1.6;
    }
    .section-content-official .inline-code {
      padding: 0.2mm 1.4mm;
      background: #eff4fb;
      border: 1px solid #d0dbec;
      border-radius: 2px;
      font-size: 9.5pt;
    }
    .section-content-official .md-hr {
      border: 0;
      border-top: 1px solid #cfd6e3;
      margin: 6mm 0;
    }
    .section-content-official .md-table {
      width: 100%;
      border-collapse: collapse;
      margin: 0 0 5mm;
      border: 1px solid #cfd6e3;
      table-layout: fixed;
    }
    .section-content-official .md-th,
    .section-content-official .md-td {
      padding: 2.6mm 3mm;
      border-bottom: 1px solid #dbe3ef;
      border-right: 1px solid #dbe3ef;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
    }
    .section-content-official .md-th {
      background: #eff5fb;
      color: ${OFFICIAL_TEXT};
      font-weight: 800;
    }
    .section-content-official .md-table tr:last-child .md-td {
      border-bottom: 0;
    }
    .section-content-official .md-table .md-th:last-child,
    .section-content-official .md-table .md-td:last-child {
      border-right: 0;
    }
  </style>
</head>
<body>${bodyHtml}</body>
</html>`
}
