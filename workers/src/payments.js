import { json, getUser } from './utils.js'

export async function handlePayments(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/payments', '')

  // Get available plans
  if (path === '/plans' && request.method === 'GET') {
    const plans = await env.DB.prepare('SELECT * FROM credit_plans WHERE active = 1').all()
    return json({ plans: plans.results })
  }

  // Get my credits
  if (path === '/credits' && request.method === 'GET') {
    const result = await env.DB.prepare('SELECT credits FROM users WHERE id = ?').bind(user.id).first()
    return json({ credits: result?.credits || 0 })
  }

  // Get my transaction history
  if (path === '/history' && request.method === 'GET') {
    const txs = await env.DB.prepare(
      'SELECT * FROM credit_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50'
    ).bind(user.id).all()
    return json({ transactions: txs.results })
  }

  // Confirm payment (토스페이먼츠 결제 승인)
  if (path === '/confirm' && request.method === 'POST') {
    const { paymentKey, orderId, amount, planId } = await request.json()

    // 토스페이먼츠 결제 승인 API 호출
    const tossResponse = await fetch('https://api.tosspayments.com/v1/payments/confirm', {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + btoa(env.TOSS_SECRET_KEY + ':'),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ paymentKey, orderId, amount }),
    })

    const tossResult = await tossResponse.json()

    if (!tossResponse.ok) {
      return json({ error: tossResult.message || '결제 승인 실패' }, 400)
    }

    // 플랜 조회
    const plan = await env.DB.prepare('SELECT * FROM credit_plans WHERE id = ?').bind(planId).first()
    if (!plan || plan.price !== amount) {
      return json({ error: '유효하지 않은 상품입니다.' }, 400)
    }

    // 크레딧 추가
    await env.DB.prepare('UPDATE users SET credits = credits + ? WHERE id = ?').bind(plan.credits, user.id).run()

    // 거래 기록
    const txId = crypto.randomUUID()
    await env.DB.prepare(
      'INSERT INTO credit_transactions (id, user_id, amount, type, description, payment_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
    ).bind(txId, user.id, plan.credits, 'purchase', plan.name, paymentKey, new Date().toISOString()).run()

    const updated = await env.DB.prepare('SELECT credits FROM users WHERE id = ?').bind(user.id).first()
    return json({ success: true, credits: updated.credits })
  }

  return json({ error: 'Not Found' }, 404)
}
