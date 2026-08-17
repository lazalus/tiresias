import { getUser, json } from './utils.js'

function normalizeEmail(value) {
  return String(value || '').trim().toLowerCase()
}

function buildBaseUrl(env) {
  return String(env.AUTH_BASE_URL || 'https://tiresiasview.com')
    .trim()
    .replace(/\/+$/, '')
}

function sanitizeText(value, maxLength = 2000) {
  return String(value || '').trim().slice(0, maxLength)
}

function isValidEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || '').trim())
}

function getCategoryLabel(category) {
  const map = {
    inquiry: '문의하기',
    issue: '불편사항 접수',
    improvement: '서비스 개선 제안',
  }
  return map[category] || '고객 의견'
}

function buildSupportFeedbackEmail(env, payload) {
  const fromName = String(env.RESEND_FROM_NAME || 'Tiresias View').trim() || 'Tiresias View'
  const supportEmail = String(env.SUPPORT_EMAIL || 'support@tiresiasview.com').trim() || 'support@tiresiasview.com'
  const baseUrl = buildBaseUrl(env)
  const categoryLabel = getCategoryLabel(payload.category)
  const submittedAt = new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })

  return {
    from: `${fromName} <${env.RESEND_FROM_EMAIL}>`,
    to: [supportEmail],
    subject: `[${fromName}] 고객 의견 - ${categoryLabel}`,
    reply_to: payload.email,
    html: `
      <div style="margin:0;padding:32px 20px;background:#f5f7fb;font-family:'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif;color:#172033;">
        <div style="max-width:640px;margin:0 auto;background:#ffffff;border:1px solid #d8e0ee;border-radius:18px;overflow:hidden;">
          <div style="padding:28px 28px 18px;border-bottom:1px solid #e5ebf5;background:linear-gradient(180deg,#fbfdff 0%,#f3f7ff 100%);">
            <div style="font-size:12px;font-weight:700;letter-spacing:0.12em;color:#51607a;">TIRESIAS VIEW</div>
            <h1 style="margin:14px 0 8px;font-size:26px;line-height:1.3;color:#203963;">고객 의견이 접수되었습니다</h1>
            <p style="margin:0;font-size:14px;line-height:1.7;color:#4e5b72;">고객센터에서 접수된 의견입니다. 아래 내용을 확인하고 후속 대응을 진행하세요.</p>
          </div>
          <div style="padding:24px 28px;">
            <table style="width:100%;border-collapse:collapse;margin-bottom:18px;">
              <tbody>
                <tr>
                  <td style="width:120px;padding:10px 0;font-size:13px;font-weight:700;color:#344054;border-bottom:1px solid #e5ebf5;">구분</td>
                  <td style="padding:10px 0;font-size:13px;color:#475467;border-bottom:1px solid #e5ebf5;">${categoryLabel}</td>
                </tr>
                <tr>
                  <td style="width:120px;padding:10px 0;font-size:13px;font-weight:700;color:#344054;border-bottom:1px solid #e5ebf5;">이름</td>
                  <td style="padding:10px 0;font-size:13px;color:#475467;border-bottom:1px solid #e5ebf5;">${payload.name}</td>
                </tr>
                <tr>
                  <td style="width:120px;padding:10px 0;font-size:13px;font-weight:700;color:#344054;border-bottom:1px solid #e5ebf5;">이메일</td>
                  <td style="padding:10px 0;font-size:13px;color:#475467;border-bottom:1px solid #e5ebf5;">${payload.email}</td>
                </tr>
                <tr>
                  <td style="width:120px;padding:10px 0;font-size:13px;font-weight:700;color:#344054;border-bottom:1px solid #e5ebf5;">접수 시각</td>
                  <td style="padding:10px 0;font-size:13px;color:#475467;border-bottom:1px solid #e5ebf5;">${submittedAt}</td>
                </tr>
                <tr>
                  <td style="width:120px;padding:10px 0;font-size:13px;font-weight:700;color:#344054;">계정</td>
                  <td style="padding:10px 0;font-size:13px;color:#475467;">${payload.userId || '비로그인 또는 계정 미확인'}</td>
                </tr>
              </tbody>
            </table>
            <div style="padding:16px 18px;border:1px solid #d8e0ee;border-radius:12px;background:#fbfcff;">
              <div style="font-size:13px;font-weight:700;color:#344054;margin-bottom:10px;">내용</div>
              <div style="font-size:14px;line-height:1.8;color:#334155;white-space:pre-wrap;">${payload.message}</div>
            </div>
            <div style="font-size:12px;line-height:1.8;color:#667085;border-top:1px solid #e5ebf5;padding-top:16px;margin-top:18px;">
              서비스 이용약관: <a href="${baseUrl}/terms" style="color:#2d4c88;text-decoration:none;">${baseUrl}/terms</a><br/>
              개인정보처리방침: <a href="${baseUrl}/privacy" style="color:#2d4c88;text-decoration:none;">${baseUrl}/privacy</a>
            </div>
          </div>
        </div>
      </div>
    `.trim(),
    text: [
      `[고객 의견] ${categoryLabel}`,
      `이름: ${payload.name}`,
      `이메일: ${payload.email}`,
      `계정: ${payload.userId || '비로그인 또는 계정 미확인'}`,
      '',
      payload.message,
      '',
      `약관: ${baseUrl}/terms`,
      `개인정보처리방침: ${baseUrl}/privacy`,
    ].join('\n'),
  }
}

async function sendSupportFeedbackEmail(env, payload) {
  if (!env.RESEND_API_KEY || !env.RESEND_FROM_EMAIL) {
    throw new Error('RESEND_API_KEY 또는 RESEND_FROM_EMAIL이 설정되지 않았습니다.')
  }

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(buildSupportFeedbackEmail(env, payload)),
  })

  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`Resend support email failed (${response.status}): ${body.slice(0, 300)}`)
  }
}

export async function handleSupport(request, env, url) {
  const path = url.pathname.replace('/api/support', '')

  if (path === '/feedback' && request.method === 'POST') {
    const user = await getUser(request, env)
    const body = await request.json().catch(() => ({}))

    const category = sanitizeText(body.category, 32)
    const name = sanitizeText(body.name || user?.nickname || user?.name, 100)
    const email = normalizeEmail(body.email || user?.email)
    const message = sanitizeText(body.message, 5000)

    if (!['inquiry', 'issue', 'improvement'].includes(category)) {
      return json({ error: '의견 유형을 선택해주세요.' }, 400)
    }

    if (!name || !email || !message) {
      return json({ error: '이름, 이메일, 내용을 모두 입력해주세요.' }, 400)
    }

    if (!isValidEmail(email)) {
      return json({ error: '올바른 이메일을 입력해주세요.' }, 400)
    }

    if (message.length < 8) {
      return json({ error: '내용은 8자 이상 입력해주세요.' }, 400)
    }

    await sendSupportFeedbackEmail(env, {
      category,
      name,
      email,
      message,
      userId: user?.id || null,
    })

    return json({ success: true, message: '고객 의견이 접수되었습니다.' })
  }

  return json({ error: 'Not Found' }, 404)
}
