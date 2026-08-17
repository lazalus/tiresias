/**
 * 보고서용 마크다운 -> HTML 변환
 * 사용자 텍스트는 모두 escape한 뒤 허용된 블록만 HTML로 조립한다.
 */

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function applyInlineMarkdown(text) {
  const escaped = escapeHtml(text)

  return escaped
    .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
}

function isTableSeparator(line) {
  const trimmed = String(line || '').trim()
  return /^\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?$/.test(trimmed)
}

function splitTableRow(line) {
  const trimmed = String(line || '').trim().replace(/^\||\|$/g, '')
  return trimmed.split('|').map((cell) => applyInlineMarkdown(cell.trim()))
}

function buildTable(lines) {
  if (lines.length < 2) return ''

  const header = splitTableRow(lines[0])
  const body = lines.slice(2).map(splitTableRow)

  let html = '<table class="md-table"><thead><tr>'
  header.forEach((cell) => {
    html += `<th class="md-th">${cell}</th>`
  })
  html += '</tr></thead>'

  if (body.length > 0) {
    html += '<tbody>'
    body.forEach((row) => {
      html += '<tr>'
      row.forEach((cell) => {
        html += `<td class="md-td">${cell}</td>`
      })
      html += '</tr>'
    })
    html += '</tbody>'
  }

  html += '</table>'
  return html
}

function buildList(items, ordered) {
  const tag = ordered ? 'ol' : 'ul'
  const itemClass = ordered ? 'md-oli' : 'md-li'
  const listClass = ordered ? 'md-ol' : 'md-ul'

  let html = `<${tag} class="${listClass}">`
  items.forEach(({ text, level, start }) => {
    const startAttr = ordered && Number.isFinite(start) && start > 1 ? ` data-start="${start}"` : ''
    html += `<li class="${itemClass}" data-level="${level}"${startAttr}>${applyInlineMarkdown(text)}</li>`
  })
  html += `</${tag}>`
  return html
}

function buildBlockquote(lines) {
  return `<blockquote class="md-quote">${lines.map((line) => applyInlineMarkdown(line)).join('<br>')}</blockquote>`
}

function buildParagraph(lines) {
  return `<p class="md-p">${lines.map((line) => applyInlineMarkdown(line)).join('<br>')}</p>`
}

function extractCodeBlocks(content) {
  const blocks = []

  const text = String(content || '').replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    const token = `@@CODEBLOCK_${blocks.length}@@`
    const langClass = lang ? ` language-${escapeHtml(lang)}` : ''
    blocks.push(`<pre class="code-block"><code class="${langClass}">${escapeHtml(code)}</code></pre>`)
    return token
  })

  return { text, blocks }
}

function restoreCodeBlocks(html, blocks) {
  return blocks.reduce(
    (acc, block, index) => acc.replaceAll(`@@CODEBLOCK_${index}@@`, block),
    html,
  )
}

export function renderMarkdown(content) {
  if (!content) return ''

  const { text, blocks } = extractCodeBlocks(content)
  const lines = text.replace(/^##\s+.+\n+/, '').split(/\r?\n/)
  const htmlParts = []

  let paragraphLines = []
  let quoteLines = []
  let listItems = []
  let listOrdered = false

  const flushParagraph = () => {
    if (paragraphLines.length) {
      htmlParts.push(buildParagraph(paragraphLines))
      paragraphLines = []
    }
  }

  const flushQuote = () => {
    if (quoteLines.length) {
      htmlParts.push(buildBlockquote(quoteLines))
      quoteLines = []
    }
  }

  const flushList = () => {
    if (listItems.length) {
      htmlParts.push(buildList(listItems, listOrdered))
      listItems = []
    }
  }

  const flushAll = () => {
    flushParagraph()
    flushQuote()
    flushList()
  }

  for (let index = 0; index < lines.length; index += 1) {
    const rawLine = lines[index]
    const line = rawLine.trimEnd()
    const trimmed = line.trim()

    if (!trimmed) {
      flushAll()
      continue
    }

    if (/^@@CODEBLOCK_\d+@@$/.test(trimmed)) {
      flushAll()
      htmlParts.push(trimmed)
      continue
    }

    const tableHeader = trimmed.includes('|') ? trimmed : null
    const nextTrimmed = index + 1 < lines.length ? lines[index + 1].trim() : ''
    if (tableHeader && isTableSeparator(nextTrimmed)) {
      flushAll()
      const tableLines = [trimmed, nextTrimmed]
      index += 2
      while (index < lines.length) {
        const row = lines[index].trim()
        if (!row || !row.includes('|')) break
        tableLines.push(row)
        index += 1
      }
      index -= 1
      htmlParts.push(buildTable(tableLines))
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/)
    if (headingMatch) {
      flushAll()
      const level = Math.min(5, headingMatch[1].length + 1)
      htmlParts.push(`<h${level} class="md-h${level}">${applyInlineMarkdown(headingMatch[2])}</h${level}>`)
      continue
    }

    if (/^---+$/.test(trimmed)) {
      flushAll()
      htmlParts.push('<hr class="md-hr">')
      continue
    }

    const quoteMatch = trimmed.match(/^>\s?(.*)$/)
    if (quoteMatch) {
      flushParagraph()
      flushList()
      quoteLines.push(quoteMatch[1])
      continue
    }

    const unorderedMatch = line.match(/^(\s*)[-*+]\s+(.+)$/)
    if (unorderedMatch) {
      flushParagraph()
      flushQuote()
      if (listItems.length && listOrdered) flushList()
      listOrdered = false
      listItems.push({
        text: unorderedMatch[2],
        level: Math.floor(unorderedMatch[1].length / 2),
      })
      continue
    }

    const orderedMatch = line.match(/^(\s*)(\d+)\.\s+(.+)$/)
    if (orderedMatch) {
      flushParagraph()
      flushQuote()
      if (listItems.length && !listOrdered) flushList()
      listOrdered = true
      listItems.push({
        text: orderedMatch[3],
        level: Math.floor(orderedMatch[1].length / 2),
        start: Number(orderedMatch[2]),
      })
      continue
    }

    flushQuote()
    flushList()
    paragraphLines.push(trimmed)
  }

  flushAll()

  return restoreCodeBlocks(htmlParts.join(''), blocks)
}

