<template>
  <div class="simulation-panel">
    <!-- Top Control Bar -->
    <div class="control-bar">
      <div class="status-group">
        <!-- 정보광장 -->
        <div class="platform-status twitter" :class="{ active: runStatus.twitter_running, completed: runStatus.twitter_completed }">
          <div class="platform-header">
            <span class="platform-name">정보광장</span>
            <span v-if="runStatus.twitter_completed" class="status-badge completed-badge">완료</span>
            <span v-else-if="runStatus.twitter_running" class="status-badge running-badge">진행중</span>
          </div>
          <div class="platform-stats">
            <span class="stat"><span class="stat-label">라운드</span><span class="stat-value mono">{{ runStatus.twitter_current_round || 0 }}<span class="stat-total">/{{ displayedTotalRounds }}</span></span></span>
            <span class="stat"><span class="stat-label">경과</span><span class="stat-value mono">{{ twitterElapsedTime }}</span></span>
            <span class="stat"><span class="stat-label">행동</span><span class="stat-value mono">{{ runStatus.twitter_actions_count || 0 }}</span></span>
          </div>
        </div>

        <!-- 주제토론 -->
        <div class="platform-status reddit" :class="{ active: runStatus.reddit_running, completed: runStatus.reddit_completed }">
          <div class="platform-header">
            <span class="platform-name">주제토론</span>
            <span v-if="runStatus.reddit_completed" class="status-badge completed-badge">완료</span>
            <span v-else-if="runStatus.reddit_running" class="status-badge running-badge">진행중</span>
          </div>
          <div class="platform-stats">
            <span class="stat"><span class="stat-label">라운드</span><span class="stat-value mono">{{ runStatus.reddit_current_round || 0 }}<span class="stat-total">/{{ displayedTotalRounds }}</span></span></span>
            <span class="stat"><span class="stat-label">경과</span><span class="stat-value mono">{{ redditElapsedTime }}</span></span>
            <span class="stat"><span class="stat-label">행동</span><span class="stat-value mono">{{ runStatus.reddit_actions_count || 0 }}</span></span>
          </div>
        </div>
      </div>

      <div class="action-controls">
        <button 
          class="action-btn primary"
          :disabled="phase !== 2 || isGeneratingReport"
          @click="handleNextStep"
        >
          <span v-if="isGeneratingReport" class="loading-spinner-small"></span>
          {{ isGeneratingReport ? '시작 중...' : '결과 보고서 생성 시작' }}
          <span v-if="!isGeneratingReport" class="arrow-icon">→</span>
        </button>
      </div>
    </div>

    <div v-if="startError" class="start-alert" :class="{ waiting: startWaiting }">
      <div class="start-alert-title">{{ startWaiting ? '현재 다른 사용자의 시뮬레이션이 진행 중입니다' : '시뮬레이션 시작 실패' }}</div>
      <p class="start-alert-message">{{ startError }}</p>
      <div class="start-alert-actions">
        <span v-if="startWaiting && startQueueState?.position" class="start-alert-meta">현재 대기열 {{ startQueueState.position }}번입니다.</span>
        <span v-if="startWaiting && startRetryCountdown > 0" class="start-alert-meta">약 {{ startRetryCountdown }}초 후 자동으로 다시 시도합니다.</span>
        <button v-if="startWaiting" class="start-alert-btn" @click="doStartSimulation">지금 다시 시도</button>
      </div>
    </div>

    <div v-if="reportQueueState" class="start-alert waiting">
      <div class="start-alert-title">보고서 생성 대기열에 등록되었습니다</div>
      <p class="start-alert-message">{{ reportQueueMessage }}</p>
      <div class="start-alert-actions">
        <span v-if="reportQueueState?.position" class="start-alert-meta">현재 대기열 {{ reportQueueState.position }}번입니다.</span>
        <span v-if="reportRetryCountdown > 0" class="start-alert-meta">약 {{ reportRetryCountdown }}초 후 자동으로 다시 시도합니다.</span>
      </div>
    </div>

    <!-- Main Content: Dual Timeline -->
    <div class="main-content-area" ref="scrollContainer">
      <!-- Timeline Header -->
      <div class="timeline-header" v-if="allActions.length > 0">
        <div class="timeline-stats">
          <span class="total-count">전체 이벤트: <span class="mono">{{ allActions.length }}</span></span>
          <span class="platform-breakdown">
            <span class="breakdown-item twitter">
              <svg class="mini-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
              <span class="mono">{{ twitterActionsCount }}</span>
            </span>
            <span class="breakdown-divider">/</span>
            <span class="breakdown-item reddit">
              <svg class="mini-icon" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
              <span class="mono">{{ redditActionsCount }}</span>
            </span>
          </span>
        </div>
      </div>
      
      <!-- Timeline Feed -->
      <div class="timeline-feed">
        <div class="timeline-axis"></div>
        
        <TransitionGroup name="timeline-item">
          <div 
            v-for="action in chronologicalActions" 
            :key="action._uniqueId || action.id || `${action.timestamp}-${action.agent_id}`" 
            class="timeline-item"
            :class="action.platform"
          >
            <div class="timeline-marker">
              <div class="marker-dot"></div>
            </div>
            
            <div class="timeline-card">
              <div class="card-header">
                <div class="agent-info">
                  <div class="avatar-placeholder">{{ (action.agent_name || 'A')[0] }}</div>
                  <span class="agent-name">{{ action.agent_name }}</span>
                </div>
                
                <div class="header-meta">
                  <div class="platform-indicator">
                    <svg v-if="action.platform === 'twitter'" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
                    <svg v-else viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                  </div>
                  <div class="action-badge" :class="getActionTypeClass(action.action_type)">
                    {{ getActionTypeLabel(action.action_type) }}
                  </div>
                </div>
              </div>
              
              <div class="card-body">
                <!-- CREATE_POST: 게시물 작성 -->
                <div v-if="action.action_type === 'CREATE_POST' && action.action_args?.content" class="content-text main-text">
                  {{ action.action_args.content }}
                </div>

                <!-- QUOTE_POST: 게시물 인용 -->
                <template v-if="action.action_type === 'QUOTE_POST'">
                  <div v-if="action.action_args?.quote_content" class="content-text">
                    {{ action.action_args.quote_content }}
                  </div>
                  <div v-if="action.action_args?.original_content" class="quoted-block">
                    <div class="quote-header">
                      <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path></svg>
                      <span class="quote-label">@{{ action.action_args.original_author_name || 'User' }}</span>
                    </div>
                    <div class="quote-text">
                      {{ truncateContent(action.action_args.original_content, 150) }}
                    </div>
                  </div>
                </template>

                <!-- REPOST: 게시물 공유 -->
                <template v-if="action.action_type === 'REPOST'">
                  <div class="repost-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"></polyline><path d="M3 11V9a4 4 0 0 1 4-4h14"></path><polyline points="7 23 3 19 7 15"></polyline><path d="M21 13v2a4 4 0 0 1-4 4H3"></path></svg>
                    <span class="repost-label">Reposted from @{{ action.action_args?.original_author_name || 'User' }}</span>
                  </div>
                  <div v-if="action.action_args?.original_content" class="repost-content">
                    {{ truncateContent(action.action_args.original_content, 200) }}
                  </div>
                </template>

                <!-- LIKE_POST: 게시물 좋아요 -->
                <template v-if="action.action_type === 'LIKE_POST'">
                  <div class="like-info">
                    <svg class="icon-small filled" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>
                    <span class="like-label">Liked @{{ action.action_args?.post_author_name || 'User' }}'s post</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="liked-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- CREATE_COMMENT: 댓글 작성 -->
                <template v-if="action.action_type === 'CREATE_COMMENT'">
                  <div v-if="action.action_args?.content" class="content-text">
                    {{ action.action_args.content }}
                  </div>
                  <div v-if="action.action_args?.post_id" class="comment-context">
                    <svg class="icon-small" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                    <span>Reply to post #{{ action.action_args.post_id }}</span>
                  </div>
                </template>

                <!-- SEARCH_POSTS: 게시물 검색 -->
                <template v-if="action.action_type === 'SEARCH_POSTS'">
                  <div class="search-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                    <span class="search-label">Search Query:</span>
                    <span class="search-query">"{{ action.action_args?.query || '' }}"</span>
                  </div>
                </template>

                <!-- FOLLOW: 사용자 팔로우 -->
                <template v-if="action.action_type === 'FOLLOW'">
                  <div class="follow-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                    <span class="follow-label">Followed @{{ action.action_args?.target_user || action.action_args?.user_id || 'User' }}</span>
                  </div>
                </template>

                <!-- UPVOTE / DOWNVOTE -->
                <template v-if="action.action_type === 'UPVOTE_POST' || action.action_type === 'DOWNVOTE_POST'">
                  <div class="vote-info">
                    <svg v-if="action.action_type === 'UPVOTE_POST'" class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"></polyline></svg>
                    <svg v-else class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    <span class="vote-label">{{ action.action_type === 'UPVOTE_POST' ? 'Upvoted' : 'Downvoted' }} Post</span>
                  </div>
                  <div v-if="action.action_args?.post_content" class="voted-content">
                    "{{ truncateContent(action.action_args.post_content, 120) }}"
                  </div>
                </template>

                <!-- DO_NOTHING: 동작 없음 (대기) -->
                <template v-if="action.action_type === 'DO_NOTHING'">
                  <div class="idle-info">
                    <svg class="icon-small" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                    <span class="idle-label">Action Skipped</span>
                  </div>
                </template>

                <!-- 일반 폴백: 알 수 없는 유형이거나 content가 있지만 위에서 처리되지 않은 경우 -->
                <div v-if="!['CREATE_POST', 'QUOTE_POST', 'REPOST', 'LIKE_POST', 'CREATE_COMMENT', 'SEARCH_POSTS', 'FOLLOW', 'UPVOTE_POST', 'DOWNVOTE_POST', 'DO_NOTHING'].includes(action.action_type) && action.action_args?.content" class="content-text">
                  {{ action.action_args.content }}
                </div>
              </div>

              <div class="card-footer">
                <span class="time-tag">R{{ action.round_num }} • {{ formatActionTime(action.timestamp) }}</span>
                <!-- Platform tag removed as it is in header now -->
              </div>
            </div>
          </div>
        </TransitionGroup>

        <div v-if="allActions.length === 0" class="waiting-state">
          <div class="pulse-ring"></div>
          <span>Waiting for agent actions...</span>
        </div>
      </div>
    </div>

    <!-- System logs removed -->
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { 
  startSimulation, 
  stopSimulation,
  getRunStatus, 
  getRunStatusDetail
} from '../api/simulation'
import { generateReport } from '../api/report'
import { getCapacityState, isCapacityError, formatCapacityMessage } from '../api/capacity'
import { formatQueueMessage, getQueuePollSeconds, getQueueStatus, isQueuedResponse } from '../api/queue'
import { PROJECT_STATUS, normalizeProjectStatus } from '../utils/projectStatus.js'
import { buildAuthFetchOptions } from '../store/auth.js'

const props = defineProps({
  simulationId: String,
  maxRounds: Number, // Step2에서 전달된 최대 라운드 수
  minutesPerRound: {
    type: Number,
    default: 30 // 기본값: 라운드당 30분
  },
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

const router = useRouter()
const MIN_SIMULATION_ROUNDS = 10

// State
const isGeneratingReport = ref(false)
const phase = ref(0) // 0: 시작 전, 1: 실행 중, 2: 완료
const isStarting = ref(false)
const isStopping = ref(false)
const startError = ref(null)
const startWaiting = ref(false)
const startRetryCountdown = ref(0)
const startQueueState = ref(null)
const reportQueueState = ref(null)
const reportRetryCountdown = ref(0)
const runStatus = ref({})
const allActions = ref([]) // 모든 액션 (증분 누적)
const actionIds = ref(new Set()) // 중복 제거를 위한 액션 ID 집합
const autoStartTriggered = ref(false)

const isReportedProject = computed(() => {
  const normalizedStatus = normalizeProjectStatus(props.projectData?.status, {
    reportId: props.projectData?.report_id || props.projectData?.reportId || null,
  })

  return Boolean(
    props.projectData?.report_id ||
    props.projectData?.reportId ||
    normalizedStatus === PROJECT_STATUS.REPORT_COMPLETED ||
    normalizedStatus === PROJECT_STATUS.REPORT_GENERATING
  )
})
const scrollContainer = ref(null)

let lastStartQueueLogKey = ''
let lastReportQueueLogKey = ''
let queuedStartPayload = null
let queuedReportPayload = null

// Computed
// 시간순으로 액션 표시 (최신 항목이 하단에 위치)
const chronologicalActions = computed(() => {
  return allActions.value
})

// 각 플랫폼 액션 수
const twitterActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'twitter').length
})

const redditActionsCount = computed(() => {
  return allActions.value.filter(a => a.platform === 'reddit').length
})

// 시뮬레이션 경과 시간 포맷 (라운드 수와 라운드당 분으로 계산)
const formatElapsedTime = (currentRound) => {
  if (!currentRound || currentRound <= 0) return '0h 0m'
  const totalMinutes = currentRound * props.minutesPerRound
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}h ${minutes}m`
}

// Twitter 플랫폼의 시뮬레이션 경과 시간
const twitterElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.twitter_current_round || 0)
})

// Reddit 플랫폼의 시뮬레이션 경과 시간
const redditElapsedTime = computed(() => {
  return formatElapsedTime(runStatus.value.reddit_current_round || 0)
})

const reportQueueMessage = computed(() => {
  if (!reportQueueState.value) return ''
  return formatQueueMessage(reportQueueState.value, '현재 보고서 생성 대기열에 등록되었습니다.')
})

const requestedMaxRounds = computed(() => {
  if (!props.maxRounds) return null
  return Math.max(MIN_SIMULATION_ROUNDS, props.maxRounds)
})

const displayedTotalRounds = computed(() => {
  return runStatus.value.total_rounds || runStatus.value.max_rounds_applied || requestedMaxRounds.value || '-'
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

const stopStartRetry = () => {
  if (startRetryTimer) {
    clearInterval(startRetryTimer)
    startRetryTimer = null
  }
  startRetryCountdown.value = 0
}

const stopReportRetry = () => {
  if (reportRetryTimer) {
    clearInterval(reportRetryTimer)
    reportRetryTimer = null
  }
  reportRetryCountdown.value = 0
}

const stopStartQueue = () => {
  if (startQueuePollTimer) {
    clearTimeout(startQueuePollTimer)
    startQueuePollTimer = null
  }
  queuedStartPayload = null
  startQueueState.value = null
  lastStartQueueLogKey = ''
  stopStartRetry()
}

const stopReportQueue = () => {
  if (reportQueuePollTimer) {
    clearTimeout(reportQueuePollTimer)
    reportQueuePollTimer = null
  }
  queuedReportPayload = null
  reportQueueState.value = null
  lastReportQueueLogKey = ''
  stopReportRetry()
}

const logQueueState = (queue, type) => {
  if (!queue) return
  const logKey = `${queue.status}:${queue.position}:${queue.totalWaiting}:${queue.lastError || ''}`

  if (type === 'start') {
    if (logKey === lastStartQueueLogKey) return
    lastStartQueueLogKey = logKey
    addLog(formatQueueMessage(queue, '현재 시뮬레이션 시작 대기열에 등록되었습니다.'))
    return
  }

  if (logKey === lastReportQueueLogKey) return
  lastReportQueueLogKey = logKey
  addLog(formatQueueMessage(queue, '현재 보고서 생성 대기열에 등록되었습니다.'))
}

const scheduleQueueCountdown = (seconds, type) => {
  if (type === 'start') {
    stopStartRetry()
    startRetryCountdown.value = seconds
    startRetryTimer = setInterval(() => {
      startRetryCountdown.value -= 1
      if (startRetryCountdown.value <= 0) {
        stopStartRetry()
      }
    }, 1000)
    return
  }

  stopReportRetry()
  reportRetryCountdown.value = seconds
  reportRetryTimer = setInterval(() => {
    reportRetryCountdown.value -= 1
    if (reportRetryCountdown.value <= 0) {
      stopReportRetry()
    }
  }, 1000)
}

const enterStartQueue = (queue, payload) => {
  startWaiting.value = true
  startQueueState.value = queue
  queuedStartPayload = payload
  startError.value = formatQueueMessage(queue, '현재 시뮬레이션 시작 대기열에 등록되었습니다.')
  emit('update-status', 'processing')
  logQueueState(queue, 'start')
  scheduleStartQueuePoll(getQueuePollSeconds(queue))
}

const enterReportQueue = (queue, payload) => {
  reportQueueState.value = queue
  queuedReportPayload = payload
  isGeneratingReport.value = true
  logQueueState(queue, 'report')
  scheduleReportQueuePoll(getQueuePollSeconds(queue))
}

const scheduleStartQueuePoll = (seconds) => {
  if (startQueuePollTimer) {
    clearTimeout(startQueuePollTimer)
    startQueuePollTimer = null
  }
  scheduleQueueCountdown(seconds, 'start')
  startQueuePollTimer = setTimeout(async () => {
    startQueuePollTimer = null
    await pollStartQueueStatus()
  }, seconds * 1000)
}

const scheduleReportQueuePoll = (seconds) => {
  if (reportQueuePollTimer) {
    clearTimeout(reportQueuePollTimer)
    reportQueuePollTimer = null
  }
  scheduleQueueCountdown(seconds, 'report')
  reportQueuePollTimer = setTimeout(async () => {
    reportQueuePollTimer = null
    await pollReportQueueStatus()
  }, seconds * 1000)
}

const pollStartQueueStatus = async () => {
  const queueId = startQueueState.value?.id
  if (!queueId) return

  try {
    const response = await getQueueStatus(queueId)
    const queue = response.queue
    if (!queue) {
      stopStartQueue()
      return
    }

    if (queue.status === 'failed') {
      stopStartQueue()
      startError.value = queue.lastError || '시뮬레이션 시작 대기열 처리에 실패했습니다.'
      startWaiting.value = false
      emit('update-status', 'error')
      return
    }

    if (queue.status === 'completed') {
      stopStartQueue()
      phase.value = 1
      emit('update-status', 'processing')
      stopPolling()
      await fetchRunStatus()
      startStatusPolling()
      startDetailPolling()
      return
    }

    startQueueState.value = queue
    startError.value = formatQueueMessage(queue, '현재 시뮬레이션 시작 대기열에 등록되었습니다.')
    logQueueState(queue, 'start')

    if (queue.ready) {
      const payload = queuedStartPayload || buildStartPayload()
      stopStartQueue()
      await doStartSimulation({ queueId: queue.id, payload })
      return
    }

    scheduleStartQueuePoll(getQueuePollSeconds(queue))
  } catch {
    scheduleStartQueuePoll(3)
  }
}

const pollReportQueueStatus = async () => {
  const queueId = reportQueueState.value?.id
  if (!queueId) return

  try {
    const response = await getQueueStatus(queueId)
    const queue = response.queue
    if (!queue) {
      stopReportQueue()
      isGeneratingReport.value = false
      return
    }

    if (queue.status === 'failed') {
      stopReportQueue()
      isGeneratingReport.value = false
      addLog(`✗ ${queue.lastError || '보고서 생성 대기열 처리에 실패했습니다.'}`)
      return
    }

    if (queue.status === 'completed') {
      const payload = queuedReportPayload || buildReportPayload()
      stopReportQueue()
      await handleNextStep({ payload })
      return
    }

    reportQueueState.value = queue
    logQueueState(queue, 'report')

    if (queue.ready) {
      const payload = queuedReportPayload || buildReportPayload()
      stopReportQueue()
      await handleNextStep({ queueId: queue.id, payload })
      return
    }

    scheduleReportQueuePoll(getQueuePollSeconds(queue))
  } catch {
    scheduleReportQueuePoll(3)
  }
}

const scheduleStartRetry = (error) => {
  const state = getCapacityState(error)
  const retryAfter = state?.retryAfter || 60

  startWaiting.value = true
  startQueueState.value = null
  queuedStartPayload = null
  startError.value = formatCapacityMessage(error, '현재 다른 사용자의 시뮬레이션이 진행 중입니다. 잠시 후 다시 시도해주세요.')
  emit('update-status', 'processing')
  addLog(`⏳ ${startError.value}`)

  stopStartRetry()
  startRetryCountdown.value = retryAfter
  startRetryTimer = setInterval(async () => {
    startRetryCountdown.value -= 1
    if (startRetryCountdown.value > 0) {
      return
    }
    stopStartRetry()
    await doStartSimulation()
  }, 1000)
}

const syncProjectStatus = async (status) => {
  if (!props.projectData?.project_id) return

  try {
    const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
    await fetch(`${API_BASE}/api/projects/${props.projectData.project_id}`, buildAuthFetchOptions({
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status,
        simulation_id: props.simulationId
      })
    }))
  } catch (error) {
    console.warn('프로젝트 상태 동기화 실패:', error)
  }
}

// 모든 상태 초기화 (시뮬레이션 재시작 시 사용)
const resetAllState = () => {
  phase.value = 0
  runStatus.value = {}
  allActions.value = []
  actionIds.value = new Set()
  prevTwitterRound.value = 0
  prevRedditRound.value = 0
  startError.value = null
  startWaiting.value = false
  startQueueState.value = null
  isStarting.value = false
  isStopping.value = false
  stopPolling()  // 이전에 존재할 수 있는 폴링 중지
  stopStartQueue()
}

const buildStartPayload = () => {
  const params = {
    simulation_id: props.simulationId,
    platform: 'parallel',
    force: true,
    enable_graph_memory_update: true
  }

  if (props.maxRounds) {
    params.max_rounds = Math.max(MIN_SIMULATION_ROUNDS, props.maxRounds)
  }

  return params
}

const markReportedProjectBlocked = () => {
  startError.value = '이미 보고서가 생성된 프로젝트입니다. 기존 보고서를 확인해주세요.'
  phase.value = 2
  emit('update-status', 'completed')
}

// 시뮬레이션 시작
const doStartSimulation = async ({ queueId = null, payload = null } = {}) => {
  if (!props.simulationId) {
    addLog('오류: simulationId가 없습니다')
    return
  }

  if (isReportedProject.value) {
    markReportedProjectBlocked()
    addLog('이미 보고서가 생성된 프로젝트라 시뮬레이션 재시작을 막았습니다.')
    return
  }

  // 모든 상태를 먼저 초기화하여 이전 시뮬레이션의 영향을 받지 않도록 함
  resetAllState()

  isStarting.value = true
  startError.value = null
  addLog('듀얼 플랫폼 병렬 시뮬레이션 시작 중...')
  emit('update-status', 'processing')
  
  try {
    const params = payload || buildStartPayload()
    
    if (props.maxRounds) {
      params.max_rounds = Math.max(MIN_SIMULATION_ROUNDS, props.maxRounds)
      addLog(`최대 시뮬레이션 라운드 설정: ${params.max_rounds}`)
    }
    
    addLog('동적 그래프 업데이트 모드 활성화')
    
    const res = await startSimulation({
      ...params,
      ...(queueId ? { queue_id: queueId } : {})
    })

    if (isQueuedResponse(res)) {
      enterStartQueue(res.queue, params)
      return
    }
    
    if (res.success && res.data) {
      stopStartQueue()
      if (res.data.force_restarted) {
        addLog('✓ 이전 시뮬레이션 로그 정리 완료, 시뮬레이션 재시작')
      }
      addLog('✓ 시뮬레이션 엔진 시작 성공')
      addLog(`  ├─ PID: ${res.data.process_pid || '-'}`)
      if (res.data.max_rounds_applied) {
        addLog(`  ├─ 적용 라운드 상한: ${res.data.max_rounds_applied}`)
      }
      
      phase.value = 1
      runStatus.value = res.data
      await syncProjectStatus(PROJECT_STATUS.SIMULATION_RUNNING)
      
      startStatusPolling()
      startDetailPolling()
    } else {
      startError.value = res.error || '시작 실패'
      addLog(`✗ 시작 실패: ${res.error || '알 수 없는 오류'}`)
      emit('update-status', 'error')
    }
  } catch (err) {
    if (isCapacityError(err)) {
      scheduleStartRetry(err)
      return
    }
    if (err?.response?.data?.code === 'REPORT_ALREADY_EXISTS') {
      markReportedProjectBlocked()
      addLog('이미 보고서가 생성된 프로젝트라 시뮬레이션 재시작을 막았습니다.')
      return
    }
    startError.value = err.message
    startWaiting.value = false
    addLog(`✗ 시작 오류: ${err.message}`)
    emit('update-status', 'error')
  } finally {
    isStarting.value = false
  }
}

// 시뮬레이션 중지
const handleStopSimulation = async () => {
  if (!props.simulationId) return
  
  isStopping.value = true
  addLog('시뮬레이션 중지 중...')
  
  try {
    const res = await stopSimulation({ simulation_id: props.simulationId })
    
    if (res.success) {
      addLog('✓ 시뮬레이션 중지됨')
      phase.value = 2
      stopPolling()
      await syncProjectStatus(PROJECT_STATUS.SIMULATION_STOPPED)
      emit('update-status', 'completed')
    } else {
      addLog(`중지 실패: ${res.error || '알 수 없는 오류'}`)
    }
  } catch (err) {
    addLog(`중지 오류: ${err.message}`)
  } finally {
    isStopping.value = false
  }
}

// 상태 폴링
let statusTimer = null
let detailTimer = null
let startRetryTimer = null
let startQueuePollTimer = null
let reportRetryTimer = null
let reportQueuePollTimer = null

const startStatusPolling = () => {
  statusTimer = setInterval(fetchRunStatus, 2000)
}

const startDetailPolling = () => {
  detailTimer = setInterval(fetchRunStatusDetail, 3000)
}

const stopPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  if (detailTimer) {
    clearInterval(detailTimer)
    detailTimer = null
  }
}

// 각 플랫폼의 이전 라운드를 추적하여 변경 감지 및 로그 출력에 사용
const prevTwitterRound = ref(0)
const prevRedditRound = ref(0)

const fetchRunStatus = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatus(props.simulationId)
    
    if (res.success && res.data) {
      const data = res.data
      
      runStatus.value = data
      
      // 각 플랫폼의 라운드 변경을 감지하고 로그 출력
      if (data.twitter_current_round > prevTwitterRound.value) {
        addLog(`[Plaza] R${data.twitter_current_round}/${data.total_rounds} | T:${data.twitter_simulated_hours || 0}h | A:${data.twitter_actions_count}`)
        prevTwitterRound.value = data.twitter_current_round
      }
      
      if (data.reddit_current_round > prevRedditRound.value) {
        addLog(`[Community] R${data.reddit_current_round}/${data.total_rounds} | T:${data.reddit_simulated_hours || 0}h | A:${data.reddit_actions_count}`)
        prevRedditRound.value = data.reddit_current_round
      }
      
      // 시뮬레이션 완료 여부 감지 (runner_status 또는 플랫폼 완료 상태로 판단)
      const isCompleted = data.runner_status === 'completed' || data.runner_status === 'stopped'
      
      // 추가 확인: 백엔드가 아직 runner_status를 업데이트하지 않았지만 플랫폼이 완료를 보고한 경우
      // twitter_completed 및 reddit_completed 상태를 확인하여 판단
      const platformsCompleted = checkPlatformsCompleted(data)
      
      if (isCompleted || platformsCompleted) {
        if (platformsCompleted && !isCompleted) {
          addLog('✓ 모든 플랫폼 시뮬레이션 종료 감지')
        }
        addLog('✓ 시뮬레이션 완료')
        phase.value = 2
        stopPolling()
        await syncProjectStatus(
          data.runner_status === 'stopped'
            ? PROJECT_STATUS.SIMULATION_STOPPED
            : PROJECT_STATUS.SIMULATION_COMPLETED
        )
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn('실행 상태 가져오기 실패:', err)
  }
}

// 활성화된 모든 플랫폼의 완료 여부 확인
const checkPlatformsCompleted = (data) => {
  // 플랫폼 데이터가 없으면 false 반환
  if (!data) return false

  // 각 플랫폼의 완료 상태 확인
  const twitterCompleted = data.twitter_completed === true
  const redditCompleted = data.reddit_completed === true
  
  // 하나 이상의 플랫폼이 완료된 경우, 활성화된 모든 플랫폼이 완료되었는지 확인
  // actions_count로 플랫폼 활성화 여부 판단 (count > 0 또는 running이 true였던 경우)
  const twitterEnabled = (data.twitter_actions_count > 0) || data.twitter_running || twitterCompleted
  const redditEnabled = (data.reddit_actions_count > 0) || data.reddit_running || redditCompleted
  
  // 활성화된 플랫폼이 없으면 false 반환
  if (!twitterEnabled && !redditEnabled) return false

  // 활성화된 모든 플랫폼이 완료되었는지 확인
  if (twitterEnabled && !twitterCompleted) return false
  if (redditEnabled && !redditCompleted) return false
  
  return true
}

const fetchRunStatusDetail = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getRunStatusDetail(props.simulationId)
    
    if (res.success && res.data) {
      // all_actions를 사용하여 전체 액션 목록 가져오기
      const serverActions = res.data.all_actions || []
      
      // 새 액션 증분 추가 (중복 제거)
      let newActionsAdded = 0
      serverActions.forEach(action => {
        // 고유 ID 생성
        const actionId = action.id || `${action.timestamp}-${action.platform}-${action.agent_id}-${action.action_type}`
        
        if (!actionIds.value.has(actionId)) {
          actionIds.value.add(actionId)
          allActions.value.push({
            ...action,
            _uniqueId: actionId
          })
          newActionsAdded++
        }
      })
      
      // 자동 스크롤하지 않고 사용자가 자유롭게 타임라인을 확인할 수 있도록 함
      // 새 액션은 하단에 추가됨
    }
  } catch (err) {
    console.warn('상세 상태 가져오기 실패:', err)
  }
}

// Helpers
const getActionTypeLabel = (type) => {
  const labels = {
    'CREATE_POST': 'POST',
    'REPOST': 'REPOST',
    'LIKE_POST': 'LIKE',
    'CREATE_COMMENT': 'COMMENT',
    'LIKE_COMMENT': 'LIKE',
    'DO_NOTHING': 'IDLE',
    'FOLLOW': 'FOLLOW',
    'SEARCH_POSTS': 'SEARCH',
    'QUOTE_POST': 'QUOTE',
    'UPVOTE_POST': 'UPVOTE',
    'DOWNVOTE_POST': 'DOWNVOTE'
  }
  return labels[type] || type || 'UNKNOWN'
}

const getActionTypeClass = (type) => {
  const classes = {
    'CREATE_POST': 'badge-post',
    'REPOST': 'badge-action',
    'LIKE_POST': 'badge-action',
    'CREATE_COMMENT': 'badge-comment',
    'LIKE_COMMENT': 'badge-action',
    'QUOTE_POST': 'badge-post',
    'FOLLOW': 'badge-meta',
    'SEARCH_POSTS': 'badge-meta',
    'UPVOTE_POST': 'badge-action',
    'DOWNVOTE_POST': 'badge-action',
    'DO_NOTHING': 'badge-idle'
  }
  return classes[type] || 'badge-default'
}

const truncateContent = (content, maxLength = 100) => {
  if (!content) return ''
  if (content.length > maxLength) return content.substring(0, maxLength) + '...'
  return content
}

const formatActionTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

const buildReportPayload = () => ({
  simulation_id: props.simulationId,
  force_regenerate: false
})

const handleNextStep = async ({ queueId = null, payload = null } = {}) => {
  if (!props.simulationId) {
    addLog('오류: simulationId가 없습니다')
    return
  }

  if (isGeneratingReport.value && !queueId && !payload) {
    addLog('보고서 생성 요청이 전송되었습니다. 잠시 기다려주세요...')
    return
  }

  isGeneratingReport.value = true
  await syncProjectStatus(PROJECT_STATUS.REPORT_GENERATING)
  addLog('보고서 생성 시작 중...')
  
  try {
    const requestPayload = payload || buildReportPayload()
    const res = await generateReport({
      ...requestPayload,
      ...(queueId ? { queue_id: queueId } : {})
    })

    if (isQueuedResponse(res)) {
      enterReportQueue(res.queue, requestPayload)
      return
    }
    
    if (res.success && res.data) {
      stopReportQueue()
      const reportId = res.data.report_id
      addLog(`✓ 보고서 생성 작업 시작됨: ${reportId}`)

      // 보고서 페이지로 이동
      router.push({ name: 'Report', params: { reportId } })
    } else {
      addLog(`✗ 보고서 생성 시작 실패: ${res.error || '알 수 없는 오류'}`)
      await syncProjectStatus(PROJECT_STATUS.SIMULATION_COMPLETED)
      isGeneratingReport.value = false
    }
  } catch (err) {
    if (isCapacityError(err)) {
      addLog(`⏳ ${formatCapacityMessage(err, '현재 다른 보고서 생성 작업이 진행 중입니다. 잠시 후 다시 시도해주세요.')}`)
    } else {
      addLog(`✗ 보고서 생성 시작 오류: ${err.message}`)
      await syncProjectStatus(PROJECT_STATUS.SIMULATION_COMPLETED)
    }
    stopReportQueue()
    isGeneratingReport.value = false
  }
}

// Scroll log to bottom
const logContent = ref(null)
watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(() => {
  addLog('Step3 시뮬레이션 실행 초기화')
})

watch(
  () => [props.simulationId, props.projectData?.project_id, props.projectData?.report_id, props.projectData?.status],
  () => {
    if (autoStartTriggered.value || !props.simulationId || !props.projectData?.project_id) {
      return
    }

    autoStartTriggered.value = true

    if (isReportedProject.value) {
      markReportedProjectBlocked()
      addLog('이미 보고서가 생성된 프로젝트라 자동 재시작을 건너뜁니다.')
      return
    }

    doStartSimulation()
  },
  { immediate: true }
)

onUnmounted(() => {
  stopPolling()
  stopStartQueue()
  stopReportQueue()
})
</script>

<style scoped>
.simulation-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  overflow: hidden;
}

/* --- Control Bar --- */
.control-bar {
  background: var(--bg-secondary);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  z-index: 10;
  height: 64px;
}

.start-alert {
  margin: 12px 24px 0;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid #F3C7BC;
  background: #FFF4F1;
}

.start-alert.waiting {
  border-color: #E4D39A;
  background: #FFF9E8;
}

.start-alert-title {
  font-size: 12px;
  font-weight: 700;
  color: #B93815;
}

.start-alert.waiting .start-alert-title {
  color: #8A6A00;
}

.start-alert-message {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #7A4A3B;
}

.start-alert-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.start-alert-meta {
  font-size: 11px;
  color: #8A6A00;
}

.start-alert-btn {
  height: 32px;
  padding: 0 12px;
  border: none;
  border-radius: 6px;
  background: #111;
  color: #FFF;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.status-group {
  display: flex;
  gap: 12px;
}

/* Platform Status Cards */
.platform-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  opacity: 0.7;
  transition: all 0.3s;
  min-width: 140px;
  position: relative;
  cursor: pointer;
}

.platform-status.active {
  opacity: 1;
  border-color: var(--accent-color);
  background: var(--bg-secondary);
}

.platform-status.completed {
  opacity: 1;
  border-color: #1A936F;
  background: rgba(26, 147, 111, 0.08);
}

/* Actions Tooltip */
.actions-tooltip {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 8px;
  padding: 10px 14px;
  background: #000;
  color: #FFF;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 100;
  min-width: 180px;
  pointer-events: none;
}

.actions-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid #000;
}

.platform-status:hover .actions-tooltip {
  opacity: 1;
  visibility: visible;
}

.tooltip-title {
  font-size: 10px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.tooltip-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tooltip-action {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  color: #FFF;
  letter-spacing: 0.03em;
}

.platform-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.platform-name {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.completed-badge {
  font-size: 9px;
  font-weight: 600;
  color: #1A936F;
  background: rgba(26, 147, 111, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
}

.running-badge {
  font-size: 9px;
  font-weight: 600;
  color: #FF5722;
  background: rgba(255, 87, 34, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
}

.platform-status.twitter .platform-icon { color: var(--text-primary); }
.platform-status.reddit .platform-icon { color: var(--text-primary); }

.platform-stats {
  display: flex;
  gap: 10px;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.stat-label {
  font-size: 8px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-value {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-total, .stat-unit {
  font-size: 9px;
  color: var(--text-muted);
  font-weight: 400;
}

.status-badge {
  margin-left: auto;
}

/* Action Button */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.action-btn.primary {
  background: var(--accent-color);
  color: #FFF;
}

.action-btn.primary:hover:not(:disabled) {
  background: #5558e6;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* --- Main Content Area --- */
.main-content-area {
  flex: 1;
  overflow-y: auto;
  position: relative;
  background: var(--bg-primary);
}

/* Timeline Header */
.timeline-header {
  position: sticky;
  top: 0;
  background: rgba(17, 17, 24, 0.9);
  backdrop-filter: blur(8px);
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-color);
  z-index: 5;
  display: flex;
  justify-content: center;
}

.timeline-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 4px 12px;
  border-radius: 20px;
}

.total-count {
  font-weight: 600;
  color: var(--text-primary);
}

.platform-breakdown {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.breakdown-divider { color: var(--text-muted); }
.breakdown-item.twitter { color: var(--text-primary); }
.breakdown-item.reddit { color: var(--text-primary); }

/* --- Timeline Feed --- */
.timeline-feed {
  padding: 24px 0;
  position: relative;
  min-height: 100%;
  max-width: 900px;
  margin: 0 auto;
}

.timeline-axis {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--border-color);
  transform: translateX(-50%);
}

.timeline-item {
  display: flex;
  justify-content: center;
  margin-bottom: 32px;
  position: relative;
  width: 100%;
}

.timeline-marker {
  position: absolute;
  left: 50%;
  top: 24px;
  width: 10px;
  height: 10px;
  background: var(--bg-secondary);
  border: 1px solid var(--text-muted);
  border-radius: 50%;
  transform: translateX(-50%);
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.marker-dot {
  width: 4px;
  height: 4px;
  background: var(--text-muted);
  border-radius: 50%;
}

.timeline-item.twitter .marker-dot { background: var(--accent-color); }
.timeline-item.reddit .marker-dot { background: var(--accent-color); }
.timeline-item.twitter .timeline-marker { border-color: var(--accent-color); }
.timeline-item.reddit .timeline-marker { border-color: var(--accent-color); }

/* Card Layout */
.timeline-card {
  width: calc(100% - 48px);
  background: var(--bg-secondary);
  border-radius: 2px;
  padding: 16px 20px;
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  position: relative;
  transition: all 0.2s;
}

.timeline-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  border-color: rgba(255,255,255,0.1);
}

/* Left side (Twitter) */
.timeline-item.twitter {
  justify-content: flex-start;
  padding-right: 50%;
}
.timeline-item.twitter .timeline-card {
  margin-left: auto;
  margin-right: 32px; /* Gap from axis */
}

/* Right side (Reddit) */
.timeline-item.reddit {
  justify-content: flex-end;
  padding-left: 50%;
}
.timeline-item.reddit .timeline-card {
  margin-right: auto;
  margin-left: 32px; /* Gap from axis */
}

/* Card Content Styles */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-placeholder {
  width: 24px;
  height: 24px;
  background: var(--accent-color);
  color: #FFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.platform-indicator {
  color: var(--text-muted);
  display: flex;
  align-items: center;
}

.action-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 2px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border: 1px solid transparent;
}

/* Monochromatic Badges */
.badge-post { background: rgba(255,255,255,0.08); color: var(--text-primary); border-color: var(--border-color); }
.badge-comment { background: rgba(255,255,255,0.08); color: var(--text-secondary); border-color: var(--border-color); }
.badge-action { background: var(--bg-surface); color: var(--text-secondary); border: 1px solid var(--border-color); }
.badge-meta { background: var(--bg-surface); color: var(--text-muted); border: 1px dashed var(--border-color); }
.badge-idle { opacity: 0.5; }

.content-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.content-text.main-text {
  font-size: 14px;
  color: var(--text-primary);
}

/* Info Blocks (Quote, Repost, etc) */
.quoted-block, .repost-content {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  padding: 10px 12px;
  border-radius: 2px;
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.quote-header, .repost-info, .like-info, .search-info, .follow-info, .vote-info, .idle-info, .comment-context {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

.icon-small {
  color: var(--text-muted);
}
.icon-small.filled {
  color: var(--text-muted);
}

.search-query {
  font-family: 'JetBrains Mono', monospace;
  background: var(--bg-tertiary);
  padding: 0 4px;
  border-radius: 2px;
}

.card-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  font-size: 10px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

/* Waiting State */
.waiting-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.pulse-ring {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border-color);
  animation: ripple 2s infinite;
}

@keyframes ripple {
  0% { transform: scale(0.8); opacity: 1; border-color: var(--text-muted); }
  100% { transform: scale(2.5); opacity: 0; border-color: var(--border-color); }
}

/* Animation */
.timeline-item-enter-active,
.timeline-item-leave-active {
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.timeline-item-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.timeline-item-leave-to {
  opacity: 0;
}

/* Logs */
.system-logs {
  background: #08080c;
  color: var(--text-secondary);
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: var(--text-muted);
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar { width: 4px; }
.log-content::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time { color: var(--text-muted); min-width: 75px; }
.log-msg { color: var(--text-secondary); word-break: break-all; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* Loading spinner for button */
.loading-spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #FFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@media (max-width: 768px) {
  /* Control bar: stack vertically */
  .control-bar {
    flex-direction: column;
    height: auto;
    padding: 8px 12px;
    gap: 8px;
  }

  .status-group {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }

  .platform-status {
    min-width: 0;
    width: 100%;
  }

  /* Timeline: full width, no dual-column split */
  .timeline-feed {
    padding: 12px 0;
    max-width: 100%;
  }

  .timeline-axis {
    display: none;
  }

  .timeline-marker {
    display: none;
  }

  .timeline-item.twitter,
  .timeline-item.reddit {
    justify-content: stretch;
    padding-left: 12px;
    padding-right: 12px;
  }

  .timeline-item.twitter .timeline-card,
  .timeline-item.reddit .timeline-card {
    margin-left: 0;
    margin-right: 0;
    width: 100%;
  }

  .timeline-item {
    margin-bottom: 16px;
  }

  .timeline-card {
    width: 100% !important;
    padding: 12px 14px;
  }

  /* Hide simulation terminal/monitor/logs on mobile */
  .system-logs,
  .simulation-terminal,
  .simulation-monitor,
  .monitor-section,
  [class*="terminal"],
  [class*="monitor"] {
    display: none !important;
  }

  /* Make post/comment cards full width */
  .post-card,
  .action-card,
  .comment-card {
    max-width: 100% !important;
  }

  /* Compact headers */
  .platform-header {
    padding: 8px 12px !important;
    font-size: 12px !important;
  }

  .round-info,
  .elapsed-info {
    font-size: 10px !important;
  }

  /* Action button full width */
  .action-controls {
    width: 100%;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
    font-size: 12px;
    padding: 8px 12px;
  }
}
</style>
