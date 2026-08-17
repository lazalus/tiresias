<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/dashboard" class="header-home">
            <span class="app-name">TIRESIAS VIEW</span>
          </router-link>
          <span class="admin-badge">Admin</span>
        </div>
        <div class="header-right">
          <HeaderNav />
          <router-link to="/dashboard" class="header-link desktop-hide">홈</router-link>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <span class="kpi-label">오늘 매출</span>
          <span class="kpi-value">{{ formatKRW(stats.todayRevenue) }}</span>
          <span v-if="stats.todayPurchases != null" class="kpi-sub">{{ stats.todayPurchases }}건 결제</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">이번 달 매출</span>
          <span class="kpi-value">{{ formatKRW(stats.monthlyRevenue) }}</span>
          <span v-if="stats.monthlyPurchases != null" class="kpi-sub">{{ stats.monthlyPurchases }}건 결제</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">신규 가입</span>
          <span class="kpi-value">{{ stats.todaySignups ?? clientTodaySignups }}</span>
          <span class="kpi-sub">전체 {{ stats.totalUsers ?? '-' }}명</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">시뮬레이션</span>
          <span class="kpi-value">{{ formatNumber(stats.monthlySimulations) }}</span>
          <span class="kpi-sub">이번 달</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">OpenAI 비용 (30일)</span>
          <span class="kpi-value">${{ aiCosts.total_cost_usd ?? '-' }}</span>
          <span class="kpi-sub">{{ formatKRW(aiCosts.total_cost_krw) }}</span>
          <span v-if="aiCosts.fetched_at" class="kpi-meta">
            {{ aiCostsLoading ? '갱신 중' : (aiCosts.stale ? '캐시 표시 중' : '최근 갱신') }} {{ formatDateTime(aiCosts.fetched_at) }}
          </span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">검색 유입 (28일)</span>
          <span class="kpi-value">{{ formatNumber(searchConsole.summary?.clicks) }}</span>
          <span class="kpi-sub">
            CTR {{ formatPercent(searchConsole.summary?.ctr) }} · 노출 {{ formatNumber(searchConsole.summary?.impressions) }}
          </span>
          <span v-if="searchConsole.fetched_at" class="kpi-meta">
            {{ searchConsoleLoading ? '갱신 중' : (searchConsole.stale ? '캐시 표시 중' : '최근 갱신') }} {{ formatDateTime(searchConsole.fetched_at) }}
          </span>
          <span v-else-if="searchConsole.error_message" class="kpi-meta">
            {{ searchConsole.error_message }}
          </span>
        </div>
      </div>

      <!-- Pending Users -->
      <section v-if="pendingUsers.length > 0" class="section-block">
        <h2 class="section-title">
          <span class="dot dot--warning"></span>
          승인 대기 ({{ pendingUsers.length }})
        </h2>
        <div class="user-cards">
          <div v-for="u in pendingUsers" :key="u.id" class="user-card user-card--pending">
            <div class="user-card-top">
              <div class="user-card-info">
                <div class="user-card-name-row">
                  <span class="user-card-name">{{ u.name }}</span>
                  <span class="role-badge role-badge--pending">대기</span>
                </div>
                <span class="user-card-email">{{ u.email }}</span>
              </div>
              <span class="user-card-date">{{ formatShortDate(u.created_at) }}</span>
            </div>
            <div class="user-card-actions">
              <button class="btn btn--approve" @click="approveUser(u.id)" :disabled="actionLoading[u.id]">승인</button>
              <button class="btn btn--reject" @click="rejectUser(u.id)" :disabled="actionLoading[u.id]">거절</button>
            </div>
          </div>
        </div>
      </section>

      <!-- 통계 아코디언 -->
      <section class="section-block">
        <h2 class="section-title">
          <span class="dot dot--primary"></span>
          통계
        </h2>
        <div class="accordion-card">
          <!-- 방문 통계 -->
          <div class="accordion-item" :class="{ open: openAccordion === 'visits' }">
            <button class="accordion-header" @click="toggleAccordion('visits')">
              <span>방문 통계</span>
              <span class="accordion-arrow">{{ openAccordion === 'visits' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'visits'" class="accordion-body">
              <div class="stats-row">
                <div class="stat-item">
                  <span class="stat-label">오늘 방문</span>
                  <span class="stat-value">{{ visits.todayVisits ?? '-' }}</span>
                  <span class="stat-sub">순방문 {{ visits.todayUnique ?? '-' }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">이번 달</span>
                  <span class="stat-value">{{ visits.monthlyVisits ?? '-' }}</span>
                  <span class="stat-sub">순방문 {{ visits.monthlyUnique ?? '-' }}</span>
                </div>
              </div>
              <div v-if="visits.daily && visits.daily.length" class="daily-chart">
                <div class="chart-label">최근 7일</div>
                <div class="chart-bars">
                  <div v-for="d in visits.daily" :key="d.day" class="chart-bar-col">
                    <div class="chart-bar" :style="{ height: barHeight(d.views) + 'px' }"></div>
                    <span class="chart-day">{{ d.day.slice(5) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 시뮬레이션 통계 -->
          <div class="accordion-item" :class="{ open: openAccordion === 'sim' }">
            <button class="accordion-header" @click="toggleAccordion('sim')">
              <span>시뮬레이션</span>
              <span class="accordion-arrow">{{ openAccordion === 'sim' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'sim'" class="accordion-body">
              <div class="stats-row">
                <div class="stat-item">
                  <span class="stat-label">총 프로젝트</span>
                  <span class="stat-value">{{ stats.totalProjects ?? '-' }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">이번 달 결제</span>
                  <span class="stat-value">{{ stats.monthlyPurchases ?? '-' }}건</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 매출 로그 -->
          <div class="accordion-item" :class="{ open: openAccordion === 'revenue' }">
            <button class="accordion-header" @click="toggleAccordion('revenue'); if (!revenueDaily.length) fetchRevenueDaily()">
              <span>매출 로그</span>
              <span class="accordion-arrow">{{ openAccordion === 'revenue' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'revenue'" class="accordion-body">
              <div v-if="revenueDaily.length" class="log-table">
                <div class="log-table-header">
                  <span>날짜</span>
                  <span>건수</span>
                  <span>매출</span>
                </div>
                <div v-for="d in pagedRevenue" :key="d.date" class="log-table-row">
                  <span>{{ d.date }}</span>
                  <span>{{ d.count }}건</span>
                  <span class="log-amount">{{ formatKRW(d.total) }}</span>
                </div>
                <div v-if="revenueTotalPages > 1" class="pagination">
                  <button class="page-btn" :disabled="revenuePage <= 1" @click="revenuePage--">&lsaquo;</button>
                  <span class="page-info">{{ revenuePage }} / {{ revenueTotalPages }}</span>
                  <button class="page-btn" :disabled="revenuePage >= revenueTotalPages" @click="revenuePage++">&rsaquo;</button>
                </div>
              </div>
              <div v-else class="accordion-empty">매출 내역이 없습니다.</div>
            </div>
          </div>

          <!-- OpenAI 비용 -->
          <div class="accordion-item" :class="{ open: openAccordion === 'aicost' }">
            <button class="accordion-header" @click="toggleAccordion('aicost')">
              <span>OpenAI 비용</span>
              <span class="accordion-arrow">{{ openAccordion === 'aicost' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'aicost'" class="accordion-body">
              <div v-if="aiCosts.fetched_at" class="accordion-note">
                <span>{{ aiCostsLoading ? '저장된 비용 데이터를 표시한 뒤 새 데이터를 확인 중입니다.' : (aiCosts.stale ? '캐시 데이터를 먼저 표시하고 있습니다.' : '최신 저장 데이터를 표시하고 있습니다.') }}</span>
                <span>기준 {{ formatDateTime(aiCosts.fetched_at) }}</span>
              </div>
              <div v-if="aiCosts.daily && aiCosts.daily.length" class="log-table">
                <div class="log-table-header">
                  <span>날짜</span>
                  <span>비용 (USD)</span>
                  <span>비용 (KRW)</span>
                </div>
                <div v-for="d in pagedAiCosts" :key="d.date" class="log-table-row">
                  <span>{{ d.date }}</span>
                  <span>${{ d.cost_usd }}</span>
                  <span class="log-amount">{{ formatKRW(Math.round(d.cost_usd * 1400)) }}</span>
                </div>
                <div v-if="aiCostTotalPages > 1" class="pagination">
                  <button class="page-btn" :disabled="aiCostPage <= 1" @click="aiCostPage--">&lsaquo;</button>
                  <span class="page-info">{{ aiCostPage }} / {{ aiCostTotalPages }}</span>
                  <button class="page-btn" :disabled="aiCostPage >= aiCostTotalPages" @click="aiCostPage++">&rsaquo;</button>
                </div>
              </div>
              <div v-else class="accordion-empty">비용 데이터가 없습니다.</div>
            </div>
          </div>

          <!-- Search Console -->
          <div class="accordion-item" :class="{ open: openAccordion === 'searchConsole' }">
            <button class="accordion-header" @click="toggleAccordion('searchConsole'); if (!searchConsoleFetchedOnce) fetchSearchConsole()">
              <span>Search Console 진단</span>
              <span class="accordion-arrow">{{ openAccordion === 'searchConsole' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'searchConsole'" class="accordion-body">
              <div v-if="searchConsole.fetched_at" class="accordion-note">
                <span>
                  {{ searchConsoleLoading ? '저장된 검색 데이터를 표시한 뒤 새 데이터를 확인 중입니다.' : (searchConsole.stale ? '캐시 데이터를 먼저 표시하고 있습니다.' : '최신 저장 데이터를 표시하고 있습니다.') }}
                </span>
                <span>기준 {{ formatDateTime(searchConsole.fetched_at) }}</span>
              </div>
              <div v-if="searchConsole.data_through" class="accordion-note accordion-note--tight">
                <span>속성 {{ searchConsole.site_url || '-' }}</span>
                <span>데이터 기준일 {{ searchConsole.data_through }}</span>
              </div>

              <div v-if="searchConsole.connected || searchConsole.fetched_at" class="search-console-section">
                <div class="stats-row stats-row--search">
                  <div class="stat-item">
                    <span class="stat-label">클릭</span>
                    <span class="stat-value">{{ formatNumber(searchConsole.summary?.clicks) }}</span>
                    <span class="stat-sub">{{ formatSignedPercent(searchConsole.deltas?.clicks) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">노출</span>
                    <span class="stat-value">{{ formatNumber(searchConsole.summary?.impressions) }}</span>
                    <span class="stat-sub">{{ formatSignedPercent(searchConsole.deltas?.impressions) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">CTR</span>
                    <span class="stat-value">{{ formatPercent(searchConsole.summary?.ctr) }}</span>
                    <span class="stat-sub">{{ formatSignedPercent(searchConsole.deltas?.ctr) }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">평균 순위</span>
                    <span class="stat-value">{{ formatPosition(searchConsole.summary?.position) }}</span>
                    <span class="stat-sub">{{ formatPositionDelta(searchConsole.deltas?.position) }}</span>
                  </div>
                </div>

                <div v-if="searchConsole.diagnostics?.issues?.length" class="diagnostic-group">
                  <div class="diagnostic-title">주의할 점</div>
                  <div class="diagnostic-list">
                    <div v-for="item in searchConsole.diagnostics.issues" :key="`issue-${item.title}`" class="diagnostic-item diagnostic-item--issue">
                      <div class="diagnostic-item-title">{{ item.title }}</div>
                      <div class="diagnostic-item-detail">{{ item.detail }}</div>
                    </div>
                  </div>
                </div>

                <div v-if="searchConsole.diagnostics?.opportunities?.length" class="diagnostic-group">
                  <div class="diagnostic-title">개선 기회</div>
                  <div class="diagnostic-list">
                    <div v-for="item in searchConsole.diagnostics.opportunities" :key="`opportunity-${item.title}`" class="diagnostic-item diagnostic-item--opportunity">
                      <div class="diagnostic-item-title">{{ item.title }}</div>
                      <div class="diagnostic-item-detail">{{ item.detail }}</div>
                    </div>
                  </div>
                </div>

                <div v-if="searchConsole.diagnostics?.wins?.length" class="diagnostic-group">
                  <div class="diagnostic-title">현재 잡히는 신호</div>
                  <div class="diagnostic-list">
                    <div v-for="item in searchConsole.diagnostics.wins" :key="`win-${item.title}`" class="diagnostic-item diagnostic-item--win">
                      <div class="diagnostic-item-title">{{ item.title }}</div>
                      <div class="diagnostic-item-detail">{{ item.detail }}</div>
                    </div>
                  </div>
                </div>

                <div class="diagnostic-group">
                  <div class="diagnostic-title">상위 검색어</div>
                  <div v-if="searchConsole.top_queries?.length" class="log-table log-table--wide">
                    <div class="log-table-header log-table-header--wide">
                      <span>검색어</span>
                      <span>클릭</span>
                      <span>노출</span>
                      <span>CTR</span>
                    </div>
                    <div v-for="row in searchConsole.top_queries" :key="row.query" class="log-table-row log-table-row--wide">
                      <span class="log-cell-main">{{ row.query }}</span>
                      <span>{{ formatNumber(row.clicks) }}</span>
                      <span>{{ formatNumber(row.impressions) }}</span>
                      <span>{{ formatPercent(row.ctr) }}</span>
                    </div>
                  </div>
                  <div v-else class="accordion-empty">검색어 데이터가 없습니다.</div>
                </div>

                <div class="diagnostic-group">
                  <div class="diagnostic-title">상위 페이지</div>
                  <div v-if="searchConsole.top_pages?.length" class="log-table log-table--wide">
                    <div class="log-table-header log-table-header--wide">
                      <span>페이지</span>
                      <span>클릭</span>
                      <span>노출</span>
                      <span>CTR</span>
                    </div>
                    <div v-for="row in searchConsole.top_pages" :key="row.page" class="log-table-row log-table-row--wide">
                      <span class="log-cell-main">{{ compactUrl(row.page) }}</span>
                      <span>{{ formatNumber(row.clicks) }}</span>
                      <span>{{ formatNumber(row.impressions) }}</span>
                      <span>{{ formatPercent(row.ctr) }}</span>
                    </div>
                  </div>
                  <div v-else class="accordion-empty">페이지 데이터가 없습니다.</div>
                </div>

                <div class="diagnostic-group">
                  <div class="diagnostic-title">핵심 페이지 색인 상태</div>
                  <div v-if="searchConsole.inspections?.length" class="inspection-list">
                    <div v-for="item in searchConsole.inspections" :key="item.url" class="inspection-row">
                      <div class="inspection-main">
                        <div class="inspection-url">{{ compactUrl(item.url) }}</div>
                        <div class="inspection-sub">
                          {{ item.coverage_state || item.indexing_state || item.error_message || '상세 정보 없음' }}
                        </div>
                      </div>
                      <span class="inspection-badge" :class="inspectionBadgeClass(item.verdict)">{{ inspectionBadgeLabel(item.verdict) }}</span>
                    </div>
                  </div>
                  <div v-else class="accordion-empty">색인 검사 데이터가 없습니다.</div>
                </div>
              </div>

              <div v-else class="accordion-empty">
                {{ searchConsole.setup_hint || searchConsole.error_message || 'Search Console 설정이 아직 연결되지 않았습니다.' }}
              </div>
            </div>
          </div>

          <!-- 최근 활동 -->
          <div class="accordion-item" :class="{ open: openAccordion === 'activity' }">
            <button class="accordion-header" @click="toggleAccordion('activity')">
              <span>최근 활동</span>
              <span class="accordion-arrow">{{ openAccordion === 'activity' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'activity'" class="accordion-body">
              <div v-if="recentActivity.length" class="activity-list-inner">
                <div v-for="a in recentActivity" :key="a.id" class="activity-row">
                  <span class="activity-type" :class="'activity-type--' + a.type">{{ activityLabel(a.type) }}</span>
                  <span class="activity-desc">{{ a.description }}</span>
                  <span class="activity-date">{{ formatShortDate(a.created_at) }}</span>
                  <button class="activity-hide-btn" @click="hideActivity(a.id)" aria-label="최근 활동 숨기기">×</button>
                </div>
              </div>
              <div v-else class="accordion-empty">활동 내역이 없습니다.</div>
            </div>
          </div>
          <!-- 보고서 -->
          <div class="accordion-item" :class="{ open: openAccordion === 'reports' }">
            <button class="accordion-header" @click="toggleAccordion('reports')">
              <span>보고서 ({{ adminReports.length }})</span>
              <span class="accordion-arrow">{{ openAccordion === 'reports' ? '−' : '+' }}</span>
            </button>
            <div v-if="openAccordion === 'reports'" class="accordion-body">
              <div v-if="adminReports.length === 0" class="accordion-empty">보고서 없음</div>
              <template v-else>
                <div class="log-table">
                  <div class="log-table-header">
                    <span>제목</span>
                    <span>작성자</span>
                    <span>날짜</span>
                  </div>
                  <div v-for="r in pagedReports" :key="r.id" class="log-table-row">
                    <span class="report-row-title">{{ r.title || '제목 없음' }}</span>
                    <span>{{ r.user_name || '-' }}</span>
                    <span>{{ new Date(r.created_at).toLocaleDateString('ko-KR') }}</span>
                  </div>
                </div>
                <div v-if="reportTotalPages > 1" class="pagination">
                  <button class="page-btn" :disabled="reportPage <= 1" @click="reportPage--">&lsaquo;</button>
                  <span class="page-info">{{ reportPage }} / {{ reportTotalPages }}</span>
                  <button class="page-btn" :disabled="reportPage >= reportTotalPages" @click="reportPage++">&rsaquo;</button>
                </div>
              </template>
            </div>
          </div>
        </div>
      </section>

      <!-- All Users -->
      <section class="section-block">
        <h2 class="section-title">
          <span class="dot dot--primary"></span>
          유저 관리 ({{ activeUsers.length }})
        </h2>
        <div class="user-cards">
          <div v-for="u in activeUsers" :key="u.id" class="user-card" @click="toggleExpand(u.id)">
            <div class="user-card-top">
              <div class="user-card-info">
                <div class="user-card-name-row">
                  <span class="user-card-name">{{ u.name }}</span>
                  <span class="role-badge" :class="'role-badge--' + u.role">{{ u.role }}</span>
                  <span v-if="u.must_change_password || u.mustChangePassword" class="role-badge role-badge--warning">비밀번호 변경 필요</span>
                </div>
                <span class="user-card-email">{{ u.email }}</span>
              </div>
              <div class="user-card-right">
                <span class="user-card-date">{{ formatShortDate(u.created_at) }}</span>
              </div>
            </div>
            <transition name="expand">
              <div v-if="expandedUser === u.id" class="user-card-actions" @click.stop>
                <button
                  class="btn btn--role"
                  @click="toggleRole(u)"
                  :disabled="actionLoading[u.id]"
                >
                  {{ u.role === 'admin' ? '유저로 변경' : '관리자 설정' }}
                </button>
                <button
                  class="btn btn--neutral"
                  @click="resetUserPassword(u)"
                  :disabled="actionLoading[u.id]"
                >
                  비밀번호 초기화
                </button>
                <button
                  class="btn btn--reject"
                  @click="deleteUser(u)"
                  :disabled="actionLoading[u.id]"
                >
                  계정 삭제
                </button>
              </div>
            </transition>
          </div>
        </div>
      </section>
    </main>

    <BottomNav />

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, buildAuthAxiosConfig } from '../store/auth.js'
import axios from 'axios'
import BottomNav from '../components/BottomNav.vue'
import HeaderNav from '../components/HeaderNav.vue'

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

onMounted(() => {
  if (!currentUser.value || currentUser.value.role !== 'admin') {
    router.push('/dashboard')
    return
  }
  fetchStats()
  fetchUsers()
  fetchVisits()
  fetchRecentActivity()
  fetchAdminReports()
  fetchAiCosts()
  fetchSearchConsole()
})

function authHeaders() {
  return buildAuthAxiosConfig()
}

// Revenue Daily
const revenueDaily = ref([])
const revenuePage = ref(1)
const revenueTotalPages = computed(() => Math.ceil(revenueDaily.value.length / REPORTS_PER_PAGE))
const pagedRevenue = computed(() => {
  const start = (revenuePage.value - 1) * REPORTS_PER_PAGE
  return revenueDaily.value.slice(start, start + REPORTS_PER_PAGE)
})

async function fetchRevenueDaily() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/revenue-daily?days=30`, authHeaders())
    revenueDaily.value = res.data.daily || []
  } catch (e) {
    console.warn('Revenue daily fetch failed:', e)
  }
}

// AI Costs
const aiCosts = ref({})
const aiCostsLoading = ref(false)
const aiCostPage = ref(1)
const aiCostTotalPages = computed(() => Math.ceil((aiCosts.value.daily || []).length / REPORTS_PER_PAGE))
const pagedAiCosts = computed(() => {
  const daily = aiCosts.value.daily || []
  const start = (aiCostPage.value - 1) * REPORTS_PER_PAGE
  return daily.slice(start, start + REPORTS_PER_PAGE)
})

async function fetchAiCosts() {
  aiCostsLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/admin/openai-costs?days=30`, authHeaders())
    aiCosts.value = {
      ...(aiCosts.value || {}),
      ...(res.data || {}),
    }
  } catch (e) {
    console.warn('AI costs fetch failed:', e)
  } finally {
    aiCostsLoading.value = false
  }
}

// Search Console
const searchConsole = ref({
  summary: {},
  deltas: {},
  top_queries: [],
  top_pages: [],
  inspections: [],
  diagnostics: { issues: [], opportunities: [], wins: [] },
})
const searchConsoleLoading = ref(false)
const searchConsoleFetchedOnce = ref(false)

async function fetchSearchConsole() {
  searchConsoleLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/admin/search-console?days=28`, authHeaders())
    searchConsole.value = {
      ...(searchConsole.value || {}),
      ...(res.data || {}),
    }
    searchConsoleFetchedOnce.value = true
  } catch (e) {
    console.warn('Search Console fetch failed:', e)
    if (e.response?.data) {
      searchConsole.value = {
        ...(searchConsole.value || {}),
        ...(e.response.data || {}),
      }
    }
  } finally {
    searchConsoleLoading.value = false
  }
}

// Reports (admin)
const adminReports = ref([])
const reportPage = ref(1)
const REPORTS_PER_PAGE = 5

const reportTotalPages = computed(() => Math.ceil(adminReports.value.length / REPORTS_PER_PAGE))
const pagedReports = computed(() => {
  const start = (reportPage.value - 1) * REPORTS_PER_PAGE
  return adminReports.value.slice(start, start + REPORTS_PER_PAGE)
})

async function fetchAdminReports() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/reports`, authHeaders())
    adminReports.value = res.data.reports || []
  } catch (e) { console.error('보고서 목록 로드 실패:', e) }
}


// Stats
const stats = ref({})

async function fetchStats() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/stats`, authHeaders())
    stats.value = res.data
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  }
}

// Users
const allUsers = ref([])
const actionLoading = reactive({})
const expandedUser = ref(null)

const pendingUsers = computed(() => allUsers.value.filter(u => u.status === 'pending' || u.role === 'pending'))
const activeUsers = computed(() => allUsers.value.filter(u => u.status !== 'pending' && u.role !== 'pending'))

// Client-side fallback: count today's signups from user list
const clientTodaySignups = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return allUsers.value.filter(u => u.created_at && u.created_at.slice(0, 10) === today).length
})

function toggleExpand(id) {
  expandedUser.value = expandedUser.value === id ? null : id
}

async function fetchUsers() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/users`, authHeaders())
    allUsers.value = res.data.users || res.data
  } catch (e) {
    console.error('Failed to fetch users:', e)
  }
}

async function approveUser(id) {
  actionLoading[id] = true
  try {
    await axios.post(`${API_BASE}/api/admin/users/${id}/approve`, {}, authHeaders())
    await fetchUsers()
    await fetchStats()
  } catch (e) {
    alert('승인 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[id] = false
  }
}

async function rejectUser(id) {
  if (!confirm('정말 거절하시겠습니까?')) return
  actionLoading[id] = true
  try {
    await axios.post(`${API_BASE}/api/admin/users/${id}/reject`, {}, authHeaders())
    await fetchUsers()
    await fetchStats()
  } catch (e) {
    alert('거절 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[id] = false
  }
}

async function toggleRole(u) {
  const newRole = u.role === 'admin' ? 'user' : 'admin'
  const label = newRole === 'admin' ? '관리자로 설정' : '유저로 변경'
  if (!confirm(`${u.name}을(를) ${label}하시겠습니까?`)) return
  actionLoading[u.id] = true
  try {
    const endpoint = newRole === 'admin' ? 'set-admin' : 'set-user'
    await axios.post(`${API_BASE}/api/admin/users/${u.id}/${endpoint}`, {}, authHeaders())
    await fetchUsers()
  } catch (e) {
    alert('설정 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[u.id] = false
  }
}

async function resetUserPassword(u) {
  if (!confirm(`${u.name} (${u.email}) 계정 비밀번호를 초기화하고 임시 비밀번호를 메일로 보내시겠습니까?`)) return
  actionLoading[u.id] = true
  try {
    const res = await axios.post(`${API_BASE}/api/admin/users/${u.id}/reset-password`, {}, authHeaders())
    await fetchUsers()
    alert(`임시 비밀번호를 ${res.data?.email || u.email} 로 보냈습니다.`)
  } catch (e) {
    alert('비밀번호 초기화 실패: ' + (e.response?.data?.error || e.message))
  } finally {
    actionLoading[u.id] = false
  }
}

// Accordion
const openAccordion = ref(null)

function toggleAccordion(key) {
  openAccordion.value = openAccordion.value === key ? null : key
}

// Visits
const visits = ref({})

async function fetchVisits() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/visits`, authHeaders())
    visits.value = res.data
  } catch (e) {
    console.error('Failed to fetch visits:', e)
  }
}

function barHeight(views) {
  const max = Math.max(...(visits.value.daily || []).map(d => d.views), 1)
  return Math.max(4, (views / max) * 60)
}

// 계정 삭제
async function deleteUser(u) {
  if (!confirm(`${u.name} (${u.email}) 계정을 삭제하시겠습니까?`)) return
  actionLoading[u.id] = true
  try {
    await axios.post(`${API_BASE}/api/admin/users/${u.id}/reject`, {}, authHeaders())
    await fetchUsers()
    await fetchStats()
  } catch (e) {
    alert('삭제 실패: ' + (e.response?.data?.message || e.message))
  } finally {
    actionLoading[u.id] = false
  }
}

// Recent Activity
const recentActivity = ref([])
const hiddenActivityIds = ref(loadHiddenActivityIds())

function loadHiddenActivityIds() {
  try {
    const raw = localStorage.getItem('tiresias_admin_hidden_activity_ids')
    const parsed = JSON.parse(raw || '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function persistHiddenActivityIds() {
  localStorage.setItem('tiresias_admin_hidden_activity_ids', JSON.stringify(hiddenActivityIds.value))
}

async function fetchRecentActivity() {
  try {
    const res = await axios.get(`${API_BASE}/api/admin/users`, authHeaders())
    const users = res.data.users || res.data
    // Build recent activity from user signups + credit transactions
    const activities = users.slice(0, 10).map(u => ({
      id: u.id,
      type: 'signup',
      description: `${u.name} (${u.email})`,
      created_at: u.created_at
    }))
    recentActivity.value = activities
      .filter((activity) => !hiddenActivityIds.value.includes(activity.id))
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
      .slice(0, 10)
  } catch (e) {
    console.error('Failed to fetch activity:', e)
  }
}

function hideActivity(id) {
  if (hiddenActivityIds.value.includes(id)) return
  hiddenActivityIds.value = [...hiddenActivityIds.value, id]
  persistHiddenActivityIds()
  recentActivity.value = recentActivity.value.filter((activity) => activity.id !== id)
}

function activityLabel(type) {
  const labels = { signup: '가입', purchase: '결제', usage: '사용', admin_grant: '지급' }
  return labels[type] || type
}

function formatKRW(val) {
  if (val == null) return '-'
  return `₩${Number(val).toLocaleString('ko-KR')}`
}

function formatNumber(val) {
  if (val == null) return '-'
  return Number(val).toLocaleString('ko-KR')
}

function formatShortDate(d) {
  if (!d) return '-'
  const dt = new Date(d)
  const m = String(dt.getMonth() + 1).padStart(2, '0')
  const day = String(dt.getDate()).padStart(2, '0')
  return `${m}.${day}`
}

function formatDateTime(d) {
  if (!d) return '-'
  const dt = new Date(d)
  if (Number.isNaN(dt.getTime())) return d
  return dt.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatPercent(value) {
  const numeric = Number(value || 0)
  return `${(numeric * 100).toFixed(2)}%`
}

function formatSignedPercent(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric === 0) return '변화 없음'
  const prefix = numeric > 0 ? '+' : ''
  return `${prefix}${numeric.toFixed(1)}%`
}

function formatPosition(value) {
  const numeric = Number(value || 0)
  if (!numeric) return '-'
  return `${numeric.toFixed(1)}위`
}

function formatPositionDelta(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric === 0) return '변화 없음'
  if (numeric < 0) return `${Math.abs(numeric).toFixed(1)}위 개선`
  return `${numeric.toFixed(1)}위 하락`
}

function compactUrl(value) {
  if (!value) return '-'
  try {
    const url = new URL(value)
    const path = url.pathname === '/' ? '' : url.pathname
    return `${url.hostname}${path}`
  } catch {
    return value
  }
}

function inspectionBadgeClass(verdict) {
  if (verdict === 'PASS') return 'inspection-badge--pass'
  if (verdict === 'ERROR') return 'inspection-badge--error'
  return 'inspection-badge--warning'
}

function inspectionBadgeLabel(verdict) {
  if (verdict === 'PASS') return '정상'
  if (verdict === 'ERROR') return '오류'
  if (verdict === 'FAIL') return '미색인'
  if (verdict === 'NEUTRAL') return '확인 필요'
  return verdict || '확인 필요'
}
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* Header */
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--header-bg);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--border-color);
}

.header-inner {
  max-width: 640px;
  margin: 0 auto;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-home {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}

.app-logo {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  object-fit: cover;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.85rem;
}

.admin-badge {
  font-size: 0.65rem;
  font-weight: 600;
  color: #818cf8;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.2);
  padding: 2px 8px;
  border-radius: 20px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}

.header-link:hover {
  color: var(--text-primary);
  background: var(--border-color);
}

/* Main */
.admin-main {
  max-width: 640px;
  margin: 0 auto;
  padding: 20px 16px 100px;
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 32px;
}

.kpi-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
}

.kpi-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.01em;
}

.kpi-value {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kpi-sub {
  font-size: 0.68rem;
  color: var(--text-muted);
}

.kpi-meta {
  font-size: 0.62rem;
  color: var(--text-muted);
}

/* Section */
.section-block {
  margin-bottom: 28px;
}

.section-title {
  font-size: 0.88rem;
  font-weight: 600;
  margin: 0 0 14px;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Dots */
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot--primary {
  background: #6366f1;
}

.dot--warning {
  background: #f59e0b;
}

/* User Cards */
.user-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 16px;
  transition: border-color 0.2s, background 0.2s;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.user-card:active {
  background: var(--bg-surface);
}

.user-card--pending {
  border-color: rgba(245, 158, 11, 0.15);
  cursor: default;
}

.user-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.user-card-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.user-card-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-card-name {
  font-size: 0.88rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card-email {
  font-size: 0.75rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-card-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.user-card-credits {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.credits-value {
  font-size: 1rem;
  font-weight: 700;
  color: #818cf8;
  letter-spacing: -0.01em;
}

.credits-label {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-weight: 500;
}

.user-card-date {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

/* Role Badges */
.role-badge {
  font-size: 0.62rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}

.role-badge--admin {
  background: rgba(99, 102, 241, 0.12);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.role-badge--user {
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.role-badge--pending {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.role-badge--warning {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

/* Card Actions */
.user-card-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-color);
  overflow: hidden;
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  max-height: 80px;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding-top: 0;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  white-space: nowrap;
  flex: 1;
  font-family: inherit;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--approve {
  background: rgba(34, 197, 94, 0.12);
  border-color: rgba(34, 197, 94, 0.25);
  color: #4ade80;
}

.btn--approve:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.2);
}

.btn--reject {
  background: rgba(239, 68, 68, 0.08);
  border-color: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.btn--reject:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.15);
}

.btn--credit {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.2);
  color: #818cf8;
}

.btn--credit:hover:not(:disabled) {
  background: rgba(99, 102, 241, 0.18);
}

.btn--role {
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.btn--role:hover:not(:disabled) {
  background: rgba(245, 158, 11, 0.15);
}

.btn--neutral {
  background: var(--bg-surface);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.btn--neutral:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.12);
}

.btn--ghost {
  background: var(--bg-surface);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.btn--ghost:hover {
  background: var(--bg-surface);
  opacity: 0.8;
}

.btn--primary {
  background: #6366f1;
  border: none;
  color: #fff;
  font-weight: 600;
}

.btn--primary:hover:not(:disabled) {
  background: #5558e6;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 500;
  padding: 0;
}

.modal-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 20px 20px 0 0;
  padding: 28px 20px 32px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 -8px 48px rgba(0, 0, 0, 0.5);
}

.modal-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 4px;
}

.modal-sub {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0 0 22px;
}

.modal-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.modal-field label {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.modal-field input {
  width: 100%;
  padding: 12px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.modal-field input:focus {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 24px;
}

.modal-actions .btn {
  flex: 1;
  padding: 12px 20px;
  font-size: 0.88rem;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition: transform 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-card {
  transform: translateY(100%);
}

.modal-leave-to .modal-card {
  transform: translateY(100%);
}

/* Desktop adjustments */
@media (min-width: 480px) {
  .modal-overlay {
    align-items: center;
    padding: 24px;
  }

  .modal-card {
    border-radius: 20px;
  }
}

/* Accordion */
.accordion-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
}

.accordion-item {
  border-bottom: 1px solid var(--border-color);
}

.accordion-item:last-child {
  border-bottom: none;
}

.accordion-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 14px 16px;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 0.82rem;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s;
}

.accordion-header:hover {
  background: var(--surface-hover);
}

.accordion-arrow {
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 300;
}

.accordion-body {
  padding: 12px 16px 16px;
}

.accordion-note {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 0.68rem;
  color: var(--text-muted);
}

.accordion-empty {
  font-size: 0.75rem;
  color: var(--text-secondary);
  padding: 8px 0;
}

.search-console-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.accordion-note--tight {
  margin-top: -4px;
}

/* Log Table */
.log-table {
  display: flex;
  flex-direction: column;
}

.log-table-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  padding: 8px 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
}

.log-table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  padding: 10px 0;
  font-size: 0.78rem;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
}

.log-table-row:last-child {
  border-bottom: none;
}

.log-amount {
  font-weight: 600;
  color: var(--text-primary);
}

.log-table--wide {
  gap: 0;
}

.log-table-header--wide,
.log-table-row--wide {
  grid-template-columns: minmax(0, 2fr) repeat(3, minmax(0, 0.9fr));
}

.log-cell-main {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Report Admin List */
.report-list-admin {
  display: flex;
  flex-direction: column;
}

.report-row-admin {
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.report-row-admin:last-child {
  border-bottom: none;
}

.report-row-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-row-title {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-primary);
}

.report-row-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.action-btn-sm {
  font-size: 0.68rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: none;
  cursor: pointer;
  font-family: inherit;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.action-btn-sm.action-btn--approve {
  color: #6366f1;
  border-color: rgba(99, 102, 241, 0.3);
}

.action-btn-sm.action-btn--approve:hover {
  background: rgba(99, 102, 241, 0.08);
}

.action-btn-sm.action-btn--reject {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.3);
}

.action-btn-sm.action-btn--reject:hover {
  background: rgba(239, 68, 68, 0.08);
}

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding-top: 12px;
}

.page-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background: none;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: inherit;
  transition: all 0.15s;
}

.page-btn:hover:not(:disabled) {
  background: var(--surface-hover);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.72rem;
  color: var(--text-muted);
}

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  padding: 12px;
}

.stat-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.stat-sub {
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.stats-row--search {
  margin-bottom: 0;
}

.diagnostic-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.diagnostic-title {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.diagnostic-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.diagnostic-item {
  border-radius: 10px;
  padding: 12px;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
}

.diagnostic-item--issue {
  border-color: rgba(239, 68, 68, 0.18);
}

.diagnostic-item--opportunity {
  border-color: rgba(99, 102, 241, 0.18);
}

.diagnostic-item--win {
  border-color: rgba(34, 197, 94, 0.18);
}

.diagnostic-item-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.diagnostic-item-detail {
  font-size: 0.72rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.inspection-list {
  display: flex;
  flex-direction: column;
  border-top: 1px solid var(--border-color);
}

.inspection-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.inspection-row:last-child {
  border-bottom: none;
}

.inspection-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.inspection-url {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inspection-sub {
  font-size: 0.68rem;
  color: var(--text-secondary);
}

.inspection-badge {
  flex-shrink: 0;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid var(--border-color);
}

.inspection-badge--pass {
  color: #4ade80;
  border-color: rgba(34, 197, 94, 0.25);
  background: rgba(34, 197, 94, 0.08);
}

.inspection-badge--warning {
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.25);
  background: rgba(245, 158, 11, 0.08);
}

.inspection-badge--error {
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.25);
  background: rgba(239, 68, 68, 0.08);
}

/* Daily Chart */
.daily-chart {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
}

.chart-label {
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 10px;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 70px;
}

.chart-bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.chart-bar {
  width: 100%;
  background: #6366f1;
  border-radius: 3px 3px 0 0;
  min-height: 4px;
}

.chart-day {
  font-size: 0.6rem;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
}

/* Activity */
.activity-list-inner {
}

.activity-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.75rem;
}

.activity-row:last-child {
  border-bottom: none;
}

.activity-type {
  font-size: 0.62rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  flex-shrink: 0;
}

.activity-type--signup {
  background: rgba(168, 85, 247, 0.1);
  color: #c084fc;
}

.activity-type--purchase {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
}

.activity-type--usage {
  background: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
}

.activity-desc {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--text-primary);
}

.activity-date {
  color: var(--text-secondary);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.activity-hide-btn {
  border: none;
  background: transparent;
  color: var(--text-muted);
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.95rem;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
}

.activity-hide-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

@media (min-width: 768px) {
  .admin-main {
    padding: 28px 24px 100px;
  }

  .header-inner {
    max-width: 720px;
    padding: 0 24px;
  }

  .admin-main {
    max-width: 720px;
  }

  .kpi-card {
    padding: 20px;
  }

  .kpi-value {
    font-size: 1.3rem;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .app-header {
    background: var(--header-bg);
    backdrop-filter: saturate(180%) blur(20px);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
  }

  .header-inner {
    max-width: 1200px;
    height: 60px;
    padding: 0 40px;
  }

  .app-name {
    font-size: 0.9rem;
  }

  .admin-main {
    max-width: 1080px;
    padding: 28px 40px 60px;
  }

  .desktop-hide {
    display: none;
  }

  .kpi-grid {
    grid-template-columns: repeat(6, 1fr);
  }

  .kpi-card {
    padding: 24px;
  }
}
</style>
