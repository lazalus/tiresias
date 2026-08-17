import fs from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { chromium } from 'playwright'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const repoRoot = path.resolve(__dirname, '..', '..')

const templateModuleUrl = pathToFileURL(
  path.join(repoRoot, 'frontend', 'src', 'utils', 'reportPdfTemplate.js')
).href

const { buildOfficialPdfDocumentHtml } = await import(templateModuleUrl)

async function main() {
  const [, , inputPath, outputPath] = process.argv

  if (!inputPath || !outputPath) {
    throw new Error('사용법: node render_report_pdf.mjs <input.json> <output.pdf>')
  }

  const payload = JSON.parse(await fs.readFile(inputPath, 'utf-8'))
  const reportId = payload.report_id || ''
  const html = buildOfficialPdfDocumentHtml(payload, reportId)

  const browser = await chromium.launch({ headless: true })

  try {
    const page = await browser.newPage()
    await page.setContent(html, { waitUntil: 'load' })
    await page.emulateMedia({ media: 'print' })
    await page.pdf({
      path: outputPath,
      format: 'A4',
      printBackground: true,
      margin: {
        top: '18mm',
        right: '16mm',
        bottom: '18mm',
        left: '16mm',
      },
      preferCSSPageSize: true,
    })
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  console.error(error?.stack || String(error))
  process.exit(1)
})
