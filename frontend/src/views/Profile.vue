<template>
  <div class="app-screen">
    <!-- Header -->
    <header class="app-header">
      <div class="header-inner">
        <h1 class="header-title">내 정보</h1>
        <HeaderNav />
      </div>
    </header>

    <main class="settings-main">
      <!-- Profile Card -->
      <div class="settings-card profile-card">
        <div class="profile-row">
          <div class="avatar-wrap" @click="triggerPhotoUpload">
            <img v-if="user?.profileImage" :src="user.profileImage" class="avatar-img" alt="프로필" />
            <div v-else class="avatar-placeholder">{{ userInitial }}</div>
            <input
              ref="photoInput"
              type="file"
              accept="image/*"
              class="photo-file-input"
              @change="handlePhotoChange"
            />
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ user?.nickname || user?.name || '-' }}</div>
            <div class="profile-email">{{ user?.email || '-' }}</div>
          </div>
          <button class="edit-btn" @click="openEditModal">프로필 수정</button>
        </div>
      </div>

      <!-- Account Info -->
      <div class="settings-card">
        <div class="list-item">
          <span class="list-label">이메일</span>
          <span class="list-value">{{ user?.email || '-' }}</span>
        </div>
        <div class="list-divider"></div>
        <div class="list-item">
          <span class="list-label">가입일</span>
          <span class="list-value">{{ formatJoinDate(user?.createdAt || user?.created_at) }}</span>
        </div>
        <div class="list-divider"></div>
        <div class="list-item">
          <span class="list-label">역할</span>
          <span class="list-value">{{ user?.role === 'admin' ? '관리자' : '일반' }}</span>
        </div>
      </div>

      <!-- Credits -->
      <router-link to="/credits" class="settings-card credits-row">
        <div class="credits-left">
          <span class="list-label">결제 내역</span>
        </div>
        <span class="row-link">결제 내역 보기 <span class="row-arrow">&rsaquo;</span></span>
      </router-link>

      <!-- Settings -->
      <div class="settings-card">
        <div class="list-item">
          <span class="list-label">테마</span>
          <div class="theme-toggle" @click="toggleTheme">
            <span class="theme-mode-label">{{ theme === 'dark' ? '다크' : '라이트' }}</span>
            <div class="toggle-switch" :class="{ light: theme === 'light' }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 샘플 보고서 -->
      <div class="settings-card accordion-card">
        <button class="accordion-header" @click="openSampleReport">
          <span class="list-label" style="font-weight:500;">샘플 보고서</span>
          <span class="row-arrow">&rsaquo;</span>
        </button>
      </div>

      <!-- 고객센터 -->
      <div class="settings-card accordion-card">
        <button class="accordion-header" @click="toggleAccordion('support')">
          <span class="list-label" style="font-weight:500;">고객센터</span>
          <span class="accordion-chevron" :class="{ open: openAccordion === 'support' }">&rsaquo;</span>
        </button>
        <Transition name="accordion">
          <div v-if="openAccordion === 'support'" class="accordion-body">
            <router-link to="/support" class="support-link-item">
              <span>자주 묻는 질문</span>
              <span class="row-arrow">&rsaquo;</span>
            </router-link>
            <router-link to="/support?tab=feedback" class="support-link-item">
              <span>고객 의견</span>
              <span class="row-arrow">&rsaquo;</span>
            </router-link>
            <router-link to="/features?from=profile" class="support-link-item">
              <span>서비스 소개</span>
              <span class="row-arrow">&rsaquo;</span>
            </router-link>
            <router-link to="/terms" class="support-link-item">
              <span>서비스 이용약관</span>
              <span class="row-arrow">&rsaquo;</span>
            </router-link>
            <router-link to="/privacy" class="support-link-item">
              <span>개인정보 처리방침</span>
              <span class="row-arrow">&rsaquo;</span>
            </router-link>
          </div>
        </Transition>
      </div>

      <!-- Footer -->
      <div class="settings-footer">
        <button class="biz-info-btn" @click="showBizInfo = !showBizInfo">사업자정보보기</button>
        <Transition name="accordion">
          <div v-if="showBizInfo" class="biz-info">
            <p class="biz-name">에스아이</p>
            <p class="biz-detail">대표 정희수 · 서비스명 테이레시아스 뷰</p>
            <p class="biz-detail">경기도 안양시 동안구 엘에스로116번길91 금정역3차 SKV1센터 지하 1층 B104호</p>
            <p class="biz-detail">사업자등록번호 111-63-00101</p>
            <p class="biz-detail">통신판매업신고번호 2024-안양동안-0010</p>
            <p class="biz-detail">support@tiresiasview.com</p>
          </div>
        </Transition>
        <button class="logout-btn" @click="handleLogout">로그아웃</button>
        <div class="app-version">v1.0.0</div>
      </div>
    </main>

    <BottomNav />

    <!-- Edit Profile Modal -->
    <Teleport to="body">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal-content">
          <div class="modal-title">프로필 수정</div>

          <div class="modal-avatar-section">
            <div class="modal-avatar-wrap" @click="triggerPhotoUpload">
              <img v-if="editProfileImage" :src="editProfileImage" class="modal-avatar-img" alt="프로필" />
              <div v-else class="modal-avatar-placeholder">{{ userInitial }}</div>
              <div class="modal-avatar-badge">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                  <circle cx="12" cy="13" r="4"/>
                </svg>
              </div>
            </div>
            <button class="photo-remove-btn" v-if="editProfileImage" @click="editProfileImage = null">사진 삭제</button>
          </div>

          <label class="modal-label">이름 / 닉네임</label>
          <input
            v-model="editName"
            type="text"
            class="modal-input"
            placeholder="이름 또는 닉네임"
          />

          <div class="modal-actions">
            <button class="modal-cancel" @click="showEditModal = false">취소</button>
            <button class="modal-save" @click="saveProfile">저장</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { currentUser, logout, getToken, updateUser } from '../store/auth.js'
import { useTheme } from '../store/theme.js'
import BottomNav from '../components/BottomNav.vue'
import HeaderNav from '../components/HeaderNav.vue'

const { theme, toggleTheme } = useTheme()

const router = useRouter()
const route = useRoute()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const user = currentUser
const showEditModal = ref(false)
const editName = ref('')
const editNickname = ref('')
const editProfileImage = ref(null)
const photoInput = ref(null)

// 고객센터 서브페이지에서 돌아왔을 때 아코디언 열기
const openAccordion = ref(route.query.from === 'support' ? 'support' : null)

function openSampleReport() {
  router.push('/samples')
}
const showBizInfo = ref(false)
const openFaq = ref(null)

const userInitial = computed(() => {
  const name = user.value?.name || user.value?.email || '?'
  return name.charAt(0).toUpperCase()
})

const faqItems = [
  {
    q: '시뮬레이션은 얼마나 걸리나요?',
    a: '시뮬레이션은 데이터 크기와 설정에 따라 다르지만, 일반적으로 1~5분 이내에 완료됩니다. 복잡한 시뮬레이션의 경우 최대 10분까지 소요될 수 있습니다.'
  },
  {
    q: '이용권은 환불되나요?',
    a: '미사용 이용권에 한하여 구매일로부터 7일 이내에 환불 요청이 가능합니다. 환불은 고객센터 이메일을 통해 요청해주세요.'
  },
  {
    q: '어떤 파일을 업로드할 수 있나요?',
    a: 'PDF, Markdown, TXT, CSV 형식의 파일을 업로드할 수 있습니다. 파일 크기는 최대 50MB까지 지원됩니다.'
  },
  {
    q: '시뮬레이션 결과는 얼마나 보관되나요?',
    a: '프로젝트와 보고서는 이용자가 삭제하거나 회원 탈퇴를 요청할 때까지 보관됩니다. 다만 결제기록과 접근기록 등 일부 정보는 관계 법령에 따라 별도 보관될 수 있습니다.'
  }
]

onMounted(() => {})

function toggleAccordion(key) {
  openAccordion.value = openAccordion.value === key ? null : key
}

function toggleFaq(index) {
  openFaq.value = openFaq.value === index ? null : index
}

function formatJoinDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('ko-KR', {
    year: 'numeric', month: 'long', day: 'numeric'
  })
}

function openEditModal() {
  editName.value = user.value?.nickname || user.value?.name || ''
  editNickname.value = user.value?.nickname || ''
  editProfileImage.value = user.value?.profileImage || null
  showEditModal.value = true
}

function triggerPhotoUpload() {
  photoInput.value?.click()
}

function handlePhotoChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    alert('이미지는 5MB 이하만 가능합니다.')
    return
  }
  const reader = new FileReader()
  reader.onload = (ev) => {
    editProfileImage.value = ev.target.result
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}

async function saveProfile() {
  const name = editName.value.trim()
  const nickname = editNickname.value.trim()
  if (!name) return

  // DB에 저장
  const token = getToken()
  if (token) {
    try {
      await axios.put(`${API_BASE}/api/auth/profile`, {
        name,
        nickname: nickname || name,
        profile_image: editProfileImage.value
      }, { headers: { Authorization: `Bearer ${token}` } })
    } catch (e) {
      console.warn('프로필 저장 실패:', e)
    }
  }

  updateUser({
    name,
    nickname: nickname || name,
    profileImage: editProfileImage.value
  })
  showEditModal.value = false
}

function handleLogout() {
  logout()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.app-screen {
  min-height: 100vh;
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
  max-width: 680px;
  margin: 0 auto;
  height: 52px;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
}

/* Main */
.settings-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 16px 16px 100px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Settings Card */
.settings-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
}

/* Profile Card */
.profile-card {
  padding: 16px;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.avatar-wrap {
  position: relative;
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  cursor: pointer;
}

.avatar-img {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
}

.photo-file-input {
  display: none;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-name {
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.3;
}

.profile-email {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 1px;
}

.edit-btn {
  flex-shrink: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-btn:hover {
  border-color: var(--text-muted);
}

/* List Items */
.list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 16px;
}

.list-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
}

.list-value {
  font-size: 0.82rem;
  color: var(--text-primary);
  font-weight: 500;
}

.list-divider {
  height: 1px;
  background: var(--border-color);
  margin: 0 16px;
}

/* Credits Row */
.credits-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  text-decoration: none;
  color: inherit;
  transition: background 0.1s;
}

.credits-row:hover {
  background: var(--bg-surface);
}

.credits-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.credits-num {
  font-size: 1.2rem;
  font-weight: 700;
  color: #6366f1;
}

.row-link {
  font-size: 0.78rem;
  color: #6366f1;
  font-weight: 500;
}

.row-arrow {
  font-size: 1rem;
  margin-left: 2px;
}

/* Theme Toggle */
.theme-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.theme-mode-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.toggle-switch {
  width: 40px;
  height: 22px;
  border-radius: 11px;
  background: #6366f1;
  position: relative;
  transition: background 0.2s;
}

.toggle-switch.light {
  background: #d1d5db;
}

.toggle-knob {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}

.toggle-switch.light .toggle-knob {
  transform: translateX(18px);
}

/* Accordion */
.accordion-card {
  overflow: hidden;
}

.accordion-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 44px;
  padding: 0 16px;
  background: none;
  border: none;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.1s;
  font-family: inherit;
  text-align: left;
}

.accordion-header:hover {
  background: var(--bg-surface);
}

.accordion-chevron {
  color: var(--text-muted);
  font-size: 1.2rem;
  font-weight: 300;
  transition: transform 0.2s ease;
}

.accordion-chevron.open {
  transform: rotate(90deg);
}

.accordion-body {
  padding: 0 16px 12px;
}

.support-link-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  color: var(--text-primary);
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 450;
  border-bottom: 1px solid var(--border-color);
  transition: opacity 0.1s;
}

.support-link-item:last-child {
  border-bottom: none;
}

.support-link-item:hover {
  opacity: 0.7;
}

.support-link-item .row-arrow {
  color: var(--text-muted);
  font-size: 1rem;
}

/* Accordion transitions */
.accordion-enter-active,
.accordion-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* Footer */
.settings-footer {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.biz-info-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 400;
  cursor: pointer;
  padding: 6px 4px;
  transition: color 0.15s;
  align-self: flex-start;
}

.biz-info-btn:hover {
  color: var(--text-secondary);
}

.biz-info {
  text-align: left;
  padding: 4px 4px 8px;
  align-self: flex-start;
}

.biz-name {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 0 0 4px;
  font-weight: 500;
}

.biz-detail {
  font-size: 0.65rem;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.6;
  opacity: 0.7;
}

.logout-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.78rem;
  font-weight: 400;
  cursor: pointer;
  padding: 6px 12px;
  transition: color 0.15s;
}

.logout-btn:hover {
  color: var(--text-secondary);
}

.app-version {
  font-size: 0.68rem;
  color: var(--text-muted);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 500;
  padding: 24px;
}

.modal-content {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 24px 20px;
  width: 100%;
  max-width: 340px;
}

.modal-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 18px;
}

.modal-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.modal-avatar-wrap {
  position: relative;
  width: 72px;
  height: 72px;
  cursor: pointer;
}

.modal-avatar-img {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
}

.modal-avatar-placeholder {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 700;
  color: #fff;
}

.modal-avatar-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.photo-remove-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.72rem;
  cursor: pointer;
  padding: 2px 6px;
  transition: color 0.15s;
}

.photo-remove-btn:hover {
  color: #f87171;
}

.modal-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 6px;
  display: block;
}

.modal-input {
  width: 100%;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  color: var(--text-primary);
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.15s;
  box-sizing: border-box;
}

.modal-input:focus {
  border-color: rgba(99, 102, 241, 0.5);
}

.modal-actions {
  display: flex;
  gap: 8px;
  margin-top: 18px;
}

.modal-cancel {
  flex: 1;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 10px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.modal-cancel:hover {
  opacity: 0.8;
}

.modal-save {
  flex: 1;
  background: #6366f1;
  border: none;
  color: #fff;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.modal-save:hover {
  background: #5558e6;
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
    justify-content: space-between;
  }

  .header-title {
    font-size: 1rem;
  }

  .settings-main {
    max-width: 760px;
    padding: 48px 40px 60px;
  }
}
</style>
