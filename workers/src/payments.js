import { json, getUser, verifyJWT } from './utils.js'

const MIN_SIMULATION_PAYMENT_AMOUNT = 12900
const PDF_DOWNLOAD_PAYMENT_AMOUNT = 1000
const ORDER_TYPE = {
  SIMULATION: 'simulation',
  PDF_DOWNLOAD: 'pdf_download',
}

export async function handlePayments(request, env, url) {
  const user = await getUser(request, env)
  if (!user) return json({ error: 'Unauthorized' }, 401)

  const path = url.pathname.replace('/api/payments', '')

  if (path === '/status' && request.method === 'GET') {
    const pendingToken = String(url.searchParams.get('pending_token') || '').trim() || null
    const reusableSimulationOrder = await findReusableSimulationOrder(env, user.id, pendingToken)
    return json({
      reusableSimulationOrder: reusableSimulationOrder
        ? {
            orderId: reusableSimulationOrder.order_id,
            amount: Number(reusableSimulationOrder.amount),
            planId: reusableSimulationOrder.plan_id || null,
            plannedAgents: reusableSimulationOrder.planned_agents ?? null,
            plannedRounds: reusableSimulationOrder.planned_rounds ?? null,
            pendingToken: reusableSimulationOrder.resource_id || null,
            confirmedAt: reusableSimulationOrder.confirmed_at,
          }
        : null,
    })
  }

  // Get my transaction history
  if (path === '/history' && request.method === 'GET') {
    const txs = await env.DB.prepare(
      'SELECT * FROM credit_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50'
    ).bind(user.id).all()
    return json({ transactions: txs.results })
  }

  // Create payment order bound to the current user
  if (path === '/create-order' && request.method === 'POST') {
    const { amount, quoteToken, orderType, reportId } = await request.json()

    if (orderType === ORDER_TYPE.PDF_DOWNLOAD) {
      return createPdfDownloadOrder(env, user, {
        amount,
        reportId,
      })
    }

    if (!quoteToken) {
      return json({ error: '견적 정보가 없습니다. 다시 계산해주세요.' }, 400)
    }

    let quote
    try {
      quote = await verifyJWT(quoteToken, env.JWT_SECRET)
    } catch {
      return json({ error: '유효하지 않은 견적 정보입니다.' }, 400)
    }

    if (quote?.scope !== 'payment_quote' || quote?.user_id !== user.id) {
      return json({ error: '주문 소유자와 견적 정보가 일치하지 않습니다.' }, 403)
    }

    if (!quote.quote_expires_at || quote.quote_expires_at < Date.now()) {
      return json({ error: '견적이 만료되었습니다. 다시 계산해주세요.' }, 400)
    }

    const quotedAmount = Number(quote.amount)
    const planId = String(quote.plan_id || '').trim() || null
    const plannedAgents = Number.isFinite(Number(quote.agents)) ? Number(quote.agents) : null
    const plannedRounds = Number.isFinite(Number(quote.rounds)) ? Number(quote.rounds) : null
    const pendingToken = String(quote.pending_token || '').trim() || null

    if (!Number.isInteger(quotedAmount) || quotedAmount < MIN_SIMULATION_PAYMENT_AMOUNT || quotedAmount % 100 !== 0) {
      return json({ error: '유효한 amount가 필요합니다.' }, 400)
    }

    if (amount !== undefined && Number(amount) !== quotedAmount) {
      return json({ error: '견적 금액과 주문 금액이 일치하지 않습니다.' }, 400)
    }

    const reusableOrder = await findReusableSimulationOrder(env, user.id, pendingToken)
    if (reusableOrder) {
      return json({
        success: true,
        already_confirmed: true,
        reusable: true,
        order: {
          orderId: reusableOrder.order_id,
          amount: Number(reusableOrder.amount),
          planId: reusableOrder.plan_id || null,
          plannedAgents: reusableOrder.planned_agents ?? null,
          plannedRounds: reusableOrder.planned_rounds ?? null,
          pendingToken: reusableOrder.resource_id || null,
        }
      })
    }

    const orderId = `SIM_${Date.now()}_${crypto.randomUUID().slice(0, 8)}`
    await env.DB.prepare(
      `INSERT INTO payment_orders
         (order_id, user_id, amount, order_type, resource_id, plan_id, planned_agents, planned_rounds, status, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      orderId,
      user.id,
      quotedAmount,
      ORDER_TYPE.SIMULATION,
      pendingToken,
      planId,
      plannedAgents,
      plannedRounds,
      'pending',
      new Date().toISOString()
    ).run()

    return json({
      success: true,
      order: {
        orderId,
        amount: quotedAmount
      }
    }, 201)
  }

  // Confirm payment (토스페이먼츠 결제 승인)
  if (path === '/confirm' && request.method === 'POST') {
    const { paymentKey, orderId, amount } = await request.json()

    if (!paymentKey || !orderId || !amount) {
      return json({ error: 'paymentKey, orderId, amount가 필요합니다.' }, 400)
    }

    const paymentOrder = await env.DB.prepare(
      'SELECT order_id, user_id, amount, order_type, resource_id, status, payment_key, confirmed_at FROM payment_orders WHERE order_id = ? LIMIT 1'
    ).bind(orderId).first()

    if (!paymentOrder) {
      return json({ error: '유효하지 않은 주문입니다.' }, 404)
    }

    if (paymentOrder.user_id !== user.id) {
      return json({ error: '주문 소유자가 일치하지 않습니다.' }, 403)
    }

    if (Number(paymentOrder.amount) !== Number(amount)) {
      return json({ error: '주문 금액이 일치하지 않습니다.' }, 400)
    }

    if ((paymentOrder.status === 'confirmed' || paymentOrder.status === 'consumed') && paymentOrder.payment_key) {
      if (paymentOrder.payment_key !== paymentKey) {
        return json({ error: '이미 다른 결제 정보로 승인된 주문입니다.' }, 409)
      }

      return json({
        success: true,
        already_confirmed: true,
        transaction: {
          order_id: paymentOrder.order_id,
          payment_key: paymentOrder.payment_key,
          confirmed_at: paymentOrder.confirmed_at
        }
      })
    }

    const existing = await env.DB.prepare(
      'SELECT id, amount, created_at FROM credit_transactions WHERE payment_key = ? LIMIT 1'
    ).bind(paymentKey).first()

    if (existing) {
      if (paymentOrder.payment_key && paymentOrder.payment_key === paymentKey) {
        return json({ success: true, already_confirmed: true, transaction: existing })
      }

      return json({ error: '이미 사용된 결제 정보입니다.' }, 409)
    }

    if (paymentOrder.payment_key && paymentOrder.payment_key !== paymentKey) {
      return json({ error: '주문에 연결된 결제 정보가 일치하지 않습니다.' }, 409)
    }

    // 토스페이먼츠 결제 승인 API 호출
    const tossResponse = await fetch('https://api.tosspayments.com/v1/payments/confirm', {
      method: 'POST',
      headers: {
        'Authorization': 'Basic ' + btoa(env.TOSS_SECRET_KEY + ':'),
        'Content-Type': 'application/json',
        'Idempotency-Key': `confirm:${orderId}`,
      },
      body: JSON.stringify({ paymentKey, orderId, amount }),
    })

    const tossPayload = await tossResponse.text()
    let tossResult = {}
    try {
      tossResult = tossPayload ? JSON.parse(tossPayload) : {}
    } catch {
      tossResult = {}
    }

    if (!tossResponse.ok) {
      return json({ error: tossResult.message || '결제 승인 실패' }, 400)
    }

    const transactionType = paymentOrder.order_type === ORDER_TYPE.PDF_DOWNLOAD
      ? 'pdf_payment'
      : 'simulation_payment'
    const transactionDescription = paymentOrder.order_type === ORDER_TYPE.PDF_DOWNLOAD
      ? `PDF 다운로드 결제 (${Number(amount).toLocaleString()}원)`
      : `시뮬레이션 결제 (${Number(amount).toLocaleString()}원)`

    const txId = crypto.randomUUID()
    try {
      await env.DB.prepare(
        'INSERT INTO credit_transactions (id, user_id, amount, type, description, payment_key, reference_key, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
      ).bind(
        txId,
        user.id,
        amount,
        transactionType,
        transactionDescription,
        paymentKey,
        orderId,
        new Date().toISOString()
      ).run()
      await env.DB.prepare(
        'UPDATE payment_orders SET status = ?, payment_key = ?, confirmed_at = ?, reserved_at = NULL WHERE order_id = ? AND user_id = ?'
      ).bind('confirmed', paymentKey, new Date().toISOString(), orderId, user.id).run()
    } catch (error) {
      if (String(error.message || '').includes('UNIQUE')) {
        await env.DB.prepare(
          'UPDATE payment_orders SET status = ?, payment_key = ?, confirmed_at = COALESCE(confirmed_at, ?), reserved_at = NULL WHERE order_id = ? AND user_id = ?'
        ).bind('confirmed', paymentKey, new Date().toISOString(), orderId, user.id).run()
        return json({ success: true, already_confirmed: true })
      }
      throw error
    }

    return json({ success: true })
  }

  return json({ error: 'Not Found' }, 404)
}

async function createPdfDownloadOrder(env, user, { amount, reportId }) {
  const normalizedReportId = String(reportId || '').trim()
  if (!normalizedReportId) {
    return json({ error: 'reportId가 필요합니다.' }, 400)
  }

  const report = await env.DB.prepare(
    'SELECT id, title, pdf_key FROM reports WHERE id = ? AND user_id = ?'
  ).bind(normalizedReportId, user.id).first()

  if (!report) {
    return json({ error: '다운로드할 보고서를 찾을 수 없습니다.' }, 404)
  }

  if (amount !== undefined && Number(amount) !== PDF_DOWNLOAD_PAYMENT_AMOUNT) {
    return json({ error: 'PDF 다운로드 금액이 올바르지 않습니다.' }, 400)
  }

  const existingOrder = await env.DB.prepare(
    `SELECT order_id, amount, status
     FROM payment_orders
     WHERE user_id = ?
       AND order_type = ?
       AND resource_id = ?
       AND status IN ('pending', 'confirmed')
     ORDER BY created_at DESC
     LIMIT 1`
  ).bind(user.id, ORDER_TYPE.PDF_DOWNLOAD, normalizedReportId).first()

  if (existingOrder) {
    return json({
      success: true,
      order: {
        orderId: existingOrder.order_id,
        amount: Number(existingOrder.amount),
        reportId: normalizedReportId,
      },
      already_exists: true,
      status: existingOrder.status,
    })
  }

  const orderId = `PDF_${Date.now()}_${crypto.randomUUID().slice(0, 8)}`
  await env.DB.prepare(
    'INSERT INTO payment_orders (order_id, user_id, amount, order_type, resource_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)'
  ).bind(
    orderId,
    user.id,
    PDF_DOWNLOAD_PAYMENT_AMOUNT,
    ORDER_TYPE.PDF_DOWNLOAD,
    normalizedReportId,
    'pending',
    new Date().toISOString()
  ).run()

  return json({
    success: true,
    order: {
      orderId,
      amount: PDF_DOWNLOAD_PAYMENT_AMOUNT,
      reportId: normalizedReportId,
      reportTitle: report.title || '보고서',
    }
  }, 201)
}

async function findReusableSimulationOrder(env, userId, pendingToken = null) {
  return env.DB.prepare(
    `SELECT order_id, amount, confirmed_at, resource_id, plan_id, planned_agents, planned_rounds
     FROM payment_orders
     WHERE user_id = ?
       AND COALESCE(order_type, 'simulation') = ?
       AND (? IS NULL OR resource_id = ?)
       AND status = 'confirmed'
       AND project_id IS NULL
     ORDER BY COALESCE(confirmed_at, created_at) DESC
     LIMIT 1`
  ).bind(userId, ORDER_TYPE.SIMULATION, pendingToken, pendingToken).first()
}
