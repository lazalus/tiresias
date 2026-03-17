<template>
  <div class="app-screen">
    <!-- App Header -->
    <header class="app-header">
      <div class="header-inner">
        <div class="header-left">
          <router-link to="/" class="header-home">
            <img src="/logoss.png" alt="TIRESIAS VIEW" class="app-logo" />
            <span class="app-name">TIRESIAS VIEW</span>
          </router-link>
        </div>
      </div>
    </header>

    <main class="profile-main">
      <!-- Profile Card -->
      <div class="section-card profile-card">
        <div class="profile-top">
          <div class="avatar-wrap" @click="triggerPhotoUpload">
            <img v-if="user?.profileImage" :src="user.profileImage" class="avatar-img" alt="프로필" />
            <div v-else class="avatar-placeholder">{{ userInitial }}</div>
            <div class="avatar-edit-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
            </div>
            <input
              ref="photoInput"
              type="file"
              accept="image/*"
              class="photo-file-input"
              @change="handlePhotoChange"
            />
          </div>
          <div class="profile-info">
            <div class="profile-name">{{ user?.name || '-' }}</div>
            <div class="profile-nickname">{{ user?.nickname ? `@${user.nickname}` : '' }}</div>
            <div class="profile-email">{{ user?.email || '-' }}</div>
          </div>
        </div>
        <button class="edit-profile-btn" @click="openEditModal">프로필 수정</button>
      </div>

      <!-- Credits Card -->
      <div class="section-card credits-card">
        <div class="credits-left">
          <div class="credits-label">보유 크레딧</div>
          <div class="credits-value">{{ credits ?? '-' }}</div>
        </div>
        <router-link to="/credits" class="credits-link">이용권 구매</router-link>
      </div>

      <!-- Service Section -->
      <div class="section-card menu-group">
        <div class="menu-item" @click="toggleTheme">
          <span class="menu-label">화면 모드</span>
          <div class="theme-toggle">
            <span class="theme-label">{{ theme === 'dark' ? '다크' : '라이트' }}</span>
            <div class="toggle-switch" :class="{ light: theme === 'light' }">
              <div class="toggle-knob"></div>
            </div>
          </div>
        </div>
        <div class="menu-divider"></div>
        <router-link to="/features" class="menu-item">
          <span class="menu-label">서비스 소개</span>
          <span class="menu-arrow">›</span>
        </router-link>
      </div>

      <!-- Accordion: 고객센터 -->
      <div class="section-card accordion-group">
        <button class="accordion-header" @click="toggleAccordion('support')">
          <span class="accordion-title">고객센터</span>
          <span class="accordion-chevron" :class="{ open: openAccordion === 'support' }">›</span>
        </button>
        <Transition name="accordion">
          <div v-if="openAccordion === 'support'" class="accordion-body">
            <div class="support-contact">
              <div class="support-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
              </div>
              <div>
                <div class="support-label">이메일 문의</div>
                <a href="mailto:support@tiresiasview.com" class="support-email">support@tiresiasview.com</a>
              </div>
            </div>
            <div class="faq-section">
              <div class="faq-title">자주 묻는 질문</div>
              <div v-for="(item, i) in faqItems" :key="i" class="faq-item">
                <button class="faq-question" @click.stop="toggleFaq(i)">
                  <span>{{ item.q }}</span>
                  <span class="faq-toggle" :class="{ open: openFaq === i }">›</span>
                </button>
                <Transition name="faq">
                  <div v-if="openFaq === i" class="faq-answer">
                    <p>{{ item.a }}</p>
                  </div>
                </Transition>
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Accordion: 이용약관 -->
      <div class="section-card accordion-group">
        <button class="accordion-header" @click="toggleAccordion('terms')">
          <span class="accordion-title">이용약관</span>
          <span class="accordion-chevron" :class="{ open: openAccordion === 'terms' }">›</span>
        </button>
        <Transition name="accordion">
          <div v-if="openAccordion === 'terms'" class="accordion-body">
            <!-- 서비스 이용약관 -->
            <div class="legal-block">
              <div class="legal-block-title">서비스 이용약관</div>
              <section class="legal-section">
                <h3>제1조 (목적)</h3>
                <p>이 약관은 TIRESIAS VIEW(이하 "서비스")가 제공하는 시뮬레이션 서비스의 이용에 관한 제반 사항을 규정함을 목적으로 합니다.</p>
              </section>
              <section class="legal-section">
                <h3>제2조 (정의)</h3>
                <p>1. "서비스"란 TIRESIAS VIEW가 제공하는 시뮬레이션 분석 및 보고서 생성 서비스를 의미합니다.</p>
                <p>2. "이용자"란 본 약관에 동의하고 서비스를 이용하는 자를 의미합니다.</p>
                <p>3. "이용권(크레딧)"이란 서비스 내에서 시뮬레이션을 실행하기 위해 필요한 디지털 이용 단위를 의미합니다.</p>
              </section>
              <section class="legal-section">
                <h3>제3조 (이용권 및 결제)</h3>
                <p>1. 이용권(크레딧) 1개는 시뮬레이션 1회 실행 권한에 해당합니다.</p>
                <p>2. 이용권은 구매 후 사용 기한 없이 보유할 수 있으며, 서비스 종료 시까지 유효합니다.</p>
                <p>3. 결제는 토스페이먼츠를 통해 처리되며, 결제 완료 후 즉시 크레딧이 충전됩니다.</p>
                <p>4. 환불은 미사용 크레딧에 한하여 구매일로부터 7일 이내에 고객센터를 통해 요청할 수 있습니다.</p>
              </section>
              <section class="legal-section">
                <h3>제4조 (서비스 이용)</h3>
                <p>1. 이용자는 서비스를 본래의 목적에 맞게 이용하여야 합니다.</p>
                <p>2. 이용자는 타인의 계정을 무단으로 사용하거나, 서비스를 부정한 방법으로 이용해서는 안 됩니다.</p>
                <p>3. 서비스는 시스템 점검, 업데이트 등의 사유로 사전 공지 후 일시적으로 중단될 수 있습니다.</p>
              </section>
              <section class="legal-section">
                <h3>제5조 (면책)</h3>
                <p>1. 서비스에서 제공하는 시뮬레이션 결과는 참고용이며, 실제 결과와 다를 수 있습니다.</p>
                <p>2. 이용자가 시뮬레이션 결과를 기반으로 내린 결정에 대해 서비스는 책임을 지지 않습니다.</p>
                <p>3. 천재지변, 시스템 장애 등 불가항력적 사유로 인한 서비스 중단에 대해 서비스는 책임을 지지 않습니다.</p>
              </section>
              <div class="legal-date">시행일: 2024년 1월 1일</div>
            </div>

            <div class="legal-divider"></div>

            <!-- 개인정보 처리방침 -->
            <div class="legal-block">
              <div class="legal-block-title">개인정보 처리방침</div>
              <section class="legal-section">
                <h3>1. 수집하는 개인정보</h3>
                <p>서비스는 회원가입 및 서비스 제공을 위해 다음의 개인정보를 수집합니다.</p>
                <ul>
                  <li>필수 항목: 이름, 이메일 주소, 비밀번호(암호화 저장)</li>
                  <li>결제 시: 결제 수단 정보(토스페이먼츠를 통해 처리, 서비스에 직접 저장하지 않음)</li>
                </ul>
              </section>
              <section class="legal-section">
                <h3>2. 이용 목적</h3>
                <p>수집된 개인정보는 다음의 목적으로 이용됩니다.</p>
                <ul>
                  <li>회원 식별 및 서비스 제공</li>
                  <li>이용권 결제 처리 및 이용 내역 관리</li>
                  <li>서비스 관련 공지 및 고객 문의 대응</li>
                </ul>
              </section>
              <section class="legal-section">
                <h3>3. 보관 기간</h3>
                <p>개인정보는 회원 탈퇴 시까지 보관되며, 탈퇴 후 즉시 파기합니다.</p>
                <ul>
                  <li>결제 기록: 전자상거래법에 따라 5년 보관</li>
                  <li>로그인 기록: 통신비밀보호법에 따라 3개월 보관</li>
                </ul>
              </section>
              <section class="legal-section">
                <h3>4. 제3자 제공</h3>
                <p>서비스는 이용자의 동의 없이 개인정보를 제3자에게 제공하지 않습니다. 다만, 다음의 경우는 예외로 합니다.</p>
                <ul>
                  <li>결제 처리를 위한 토스페이먼츠 연동 (결제 정보에 한함)</li>
                  <li>법령에 의한 수사기관의 요청</li>
                </ul>
              </section>
              <section class="legal-section">
                <h3>5. 이용자의 권리</h3>
                <p>이용자는 언제든지 개인정보 열람, 수정, 삭제, 처리 정지를 요청할 수 있습니다.</p>
                <p>상기 요청은 고객센터(support@tiresiasview.com)를 통해 접수할 수 있습니다.</p>
              </section>
              <div class="legal-date">시행일: 2024년 1월 1일</div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Footer -->
      <div class="profile-footer">
        <button class="logout-btn" @click="handleLogout">로그아웃</button>
        <div class="app-version">앱 버전 v1.0.0</div>
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

          <label class="modal-label">이름</label>
          <input
            v-model="editName"
            type="text"
            class="modal-input"
            placeholder="이름을 입력하세요"
          />

          <label class="modal-label" style="margin-top: 16px;">닉네임</label>
          <input
            v-model="editNickname"
            type="text"
            class="modal-input"
            placeholder="닉네임을 입력하세요"
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
import { useRouter } from 'vue-router'
import axios from 'axios'
import { currentUser, logout, getToken, updateUser } from '../store/auth.js'
import { useTheme } from '../store/theme.js'
import BottomNav from '../components/BottomNav.vue'

const { theme, toggleTheme } = useTheme()

const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const user = currentUser
const credits = ref(null)
const showEditModal = ref(false)
const editName = ref('')
const editNickname = ref('')
const editProfileImage = ref(null)
const photoInput = ref(null)

const openAccordion = ref(null)
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
    a: 'CSV, Excel(.xlsx) 형식의 데이터 파일을 업로드할 수 있습니다. 파일 크기는 최대 50MB까지 지원됩니다.'
  },
  {
    q: '시뮬레이션 결과는 얼마나 보관되나요?',
    a: '시뮬레이션 결과 및 보고서는 계정이 유지되는 동안 무기한 보관됩니다.'
  }
]

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/payments/credits`, {
      headers: { Authorization: `Bearer ${getToken()}` }
    })
    credits.value = res.data.credits ?? res.data
  } catch (e) {
    // Credits fetch failed silently
  }
})

function toggleAccordion(key) {
  openAccordion.value = openAccordion.value === key ? null : key
}

function toggleFaq(index) {
  openFaq.value = openFaq.value === index ? null : index
}

function openEditModal() {
  editName.value = user.value?.name || ''
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

function saveProfile() {
  const name = editName.value.trim()
  const nickname = editNickname.value.trim()
  if (!name) return
  updateUser({
    name,
    nickname,
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
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-home {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}

.app-logo {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  object-fit: cover;
}

.app-name {
  font-family: 'Outfit', sans-serif;
  font-weight: 700;
  letter-spacing: 0.08em;
  font-size: 0.9rem;
}

/* Main */
.profile-main {
  max-width: 680px;
  margin: 0 auto;
  padding: 24px 16px 100px;
}

/* Section Card */
.section-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  margin-bottom: 16px;
}

/* Profile Card */
.profile-card {
  padding: 24px;
}

.profile-top {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.avatar-wrap {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
  cursor: pointer;
}

.avatar-img {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-placeholder {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

.avatar-edit-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #1a1828;
  border: 2px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.6);
}

.photo-file-input {
  display: none;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.profile-name {
  font-size: 1.15rem;
  font-weight: 600;
}

.profile-nickname {
  font-size: 0.85rem;
  color: #818cf8;
  font-weight: 500;
}

.profile-email {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.35);
}

.edit-profile-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  padding: 10px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-profile-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

/* Credits Card */
.credits-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
}

.credits-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 6px;
}

.credits-value {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  background: linear-gradient(135deg, #818cf8, #6366f1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.credits-link {
  color: #818cf8;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 8px 20px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 10px;
  transition: all 0.2s;
}

.credits-link:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.5);
}

/* Menu Group */
.menu-group {
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.92rem;
  transition: background 0.15s;
  cursor: pointer;
}

.menu-item:hover {
  background: var(--bg-surface);
}

.menu-label {
  font-weight: 450;
}

.menu-arrow {
  color: rgba(255, 255, 255, 0.2);
  font-size: 1.3rem;
  font-weight: 300;
}

.menu-divider {
  height: 1px;
  background: var(--bg-surface);
  margin: 0 20px;
}

/* Theme Toggle */
.theme-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
}
.theme-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.toggle-switch {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  background: #6366f1;
  position: relative;
  cursor: pointer;
  transition: background 0.2s;
}
.toggle-switch.light {
  background: #d1d5db;
}
.toggle-knob {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
  top: 2px;
  left: 2px;
  transition: transform 0.2s;
}
.toggle-switch.light .toggle-knob {
  transform: translateX(20px);
}

/* Accordion */
.accordion-group {
  overflow: hidden;
}

.accordion-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.92rem;
  font-weight: 450;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
  text-align: left;
}

.accordion-header:hover {
  background: var(--bg-surface);
}

.accordion-chevron {
  color: rgba(255, 255, 255, 0.2);
  font-size: 1.3rem;
  font-weight: 300;
  transition: transform 0.25s ease;
}

.accordion-chevron.open {
  transform: rotate(90deg);
}

.accordion-body {
  padding: 0 20px 20px;
}

/* Accordion transition */
.accordion-enter-active,
.accordion-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}

.accordion-enter-from,
.accordion-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Support inside accordion */
.support-contact {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.support-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(99, 102, 241, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #818cf8;
  flex-shrink: 0;
}

.support-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.support-email {
  color: #818cf8;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
}

.support-email:hover {
  text-decoration: underline;
}

.faq-section {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.faq-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 14px 16px 8px;
}

.faq-item + .faq-item {
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.faq-question {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  font-weight: 450;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}

.faq-question:hover {
  background: var(--bg-secondary);
}

.faq-toggle {
  color: rgba(255, 255, 255, 0.2);
  font-size: 1.2rem;
  font-weight: 300;
  transition: transform 0.2s;
  flex-shrink: 0;
  margin-left: 12px;
}

.faq-toggle.open {
  transform: rotate(90deg);
}

.faq-answer {
  padding: 0 16px 14px;
}

.faq-answer p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

.faq-enter-active,
.faq-leave-active {
  transition: all 0.2s ease;
}

.faq-enter-from,
.faq-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Legal inside accordion */
.legal-block {
  margin-bottom: 8px;
}

.legal-block-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

.legal-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 24px 0;
}

.legal-section {
  margin-bottom: 16px;
}

.legal-section h3 {
  font-size: 0.82rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 8px;
}

.legal-section p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0 0 4px;
}

.legal-section ul {
  margin: 6px 0 0;
  padding-left: 18px;
}

.legal-section li {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.38);
  line-height: 1.8;
}

.legal-date {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.2);
  margin-top: 12px;
}

/* Footer */
.profile-footer {
  margin-top: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.logout-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.85rem;
  font-weight: 450;
  cursor: pointer;
  padding: 8px 16px;
  transition: color 0.2s;
}

.logout-btn:hover {
  color: rgba(255, 255, 255, 0.55);
}

.app-version {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.15);
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
  background: #1a1828;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 28px 24px;
  width: 100%;
  max-width: 360px;
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 20px;
}

.modal-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}

.modal-avatar-wrap {
  position: relative;
  width: 80px;
  height: 80px;
  cursor: pointer;
}

.modal-avatar-img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.modal-avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #818cf8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: 700;
  color: #fff;
}

.modal-avatar-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 26px;
  height: 26px;
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
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.78rem;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.2s;
}

.photo-remove-btn:hover {
  color: #f87171;
}

.modal-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 8px;
  display: block;
}

.modal-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 12px 14px;
  color: var(--text-primary);
  font-size: 0.92rem;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.modal-input:focus {
  border-color: rgba(99, 102, 241, 0.5);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.modal-cancel {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  padding: 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-cancel:hover {
  background: rgba(255, 255, 255, 0.08);
}

.modal-save {
  flex: 1;
  background: #6366f1;
  border: none;
  color: #fff;
  padding: 12px;
  border-radius: 10px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-save:hover {
  background: #5558e6;
}

/* Responsive */
@media (max-width: 640px) {
  .profile-main {
    padding: 20px 16px 100px;
  }
}
</style>
