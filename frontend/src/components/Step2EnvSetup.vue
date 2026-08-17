<template>
  <div class="env-setup-panel">
    <div class="scroll-container">
      <!-- Step 01: 시뮬레이션 인스턴스 -->
      <div class="step-card" :class="{ 'active': phase === 0, 'completed': phase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">환경 설정</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 0" class="badge success">완료</span>
            <span v-else class="badge processing">준비 중</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="description">
            프로젝트와 구조도를 바탕으로 분석 실행 인스턴스를 만들고 기본 실행 컨텍스트를 불러옵니다
          </p>

          <div v-if="simulationId" class="info-card">
            <div class="info-row">
              <span class="info-label">프로젝트 ID</span>
              <span class="info-value mono">{{ projectData?.project_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">구조도 ID</span>
              <span class="info-value mono">{{ projectData?.graph_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">시뮬레이션 ID</span>
              <span class="info-value mono">{{ simulationId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">작업 ID</span>
              <span class="info-value mono">{{ taskId || '비동기 준비 완료' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 02: Agent 페르소나 생성 -->
      <div class="step-card" :class="{ 'active': phase === 1, 'completed': phase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">에이전트 프로필 생성</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 1" class="badge success">완료</span>
            <span v-else-if="phase === 1" class="badge processing">{{ personaProgress }}%</span>
            <span v-else class="badge pending">대기</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            구조 분석 결과와 요구사항을 결합해 에이전트별 특성, 관심 주제, 행동 성향을 모델링합니다
          </p>

          <div v-if="prepareError" class="prepare-error-panel">
            <div class="prepare-error-title">{{ prepareWaiting ? '현재 다른 사용자의 작업이 진행 중입니다' : '환경 준비가 중단되었습니다' }}</div>
            <p class="prepare-error-message">{{ prepareError }}</p>
            <p v-if="prepareWaiting && prepareQueueState?.position" class="prepare-error-meta">
              현재 대기열 {{ prepareQueueState.position }}번입니다.
            </p>
            <p v-if="prepareWaiting && prepareRetryCountdown > 0" class="prepare-error-meta">
              약 {{ prepareRetryCountdown }}초 후 자동으로 다시 시도합니다.
            </p>
            <button
              class="prepare-error-btn"
              @click="prepareWaiting ? startPrepareSimulation() : emit('go-back')"
            >
              {{ prepareWaiting ? '지금 다시 시도' : '구조 분석 단계로 돌아가기' }}
            </button>
          </div>

          <!-- Profiles Stats -->
          <div v-if="profiles.length > 0" class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ profiles.length }}</span>
              <span class="stat-label">생성된 에이전트</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ expectedTotal || '-' }}</span>
              <span class="stat-label">예상 총 에이전트</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ totalTopicsCount }}</span>
              <span class="stat-label">관심 토픽 합계</span>
            </div>
          </div>

          <!-- Profiles List Preview -->
          <div v-if="profiles.length > 0" class="profiles-preview">
            <div class="preview-header">
              <span class="preview-title">생성된 에이전트 모델</span>
            </div>
            <div class="profiles-list">
              <div 
                v-for="(profile, idx) in profiles" 
                :key="idx" 
                class="profile-card"
                @click="selectProfile(profile)"
              >
                <div class="profile-header">
                  <span class="profile-realname">{{ profile.username || 'Unknown' }}</span>
                  <span class="profile-username">@{{ profile.name || `agent_${idx}` }}</span>
                </div>
                <div class="profile-meta">
                  <span class="profile-profession">{{ profile.profession || '알 수 없는 직업' }}</span>
                </div>
                <p class="profile-bio">{{ profile.bio || '소개 없음' }}</p>
                <div v-if="profile.interested_topics?.length" class="profile-topics">
                  <span 
                    v-for="topic in profile.interested_topics.slice(0, 3)" 
                    :key="topic" 
                    class="topic-tag"
                  >{{ topic }}</span>
                  <span v-if="profile.interested_topics.length > 3" class="topic-more">
                    +{{ profile.interested_topics.length - 3 }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 03: 듀얼 플랫폼 시뮬레이션 설정 생성 -->
      <div class="step-card" :class="{ 'active': phase === 2, 'completed': phase > 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">시나리오 실행 조건 구성</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 2" class="badge success">완료</span>
            <span v-else-if="phase === 2" class="badge processing">생성 중</span>
            <span v-else class="badge pending">대기</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            분석 질문과 현실 시드를 바탕으로 시간 흐름, 활성도, 확산 조건, 추천 알고리즘 파라미터를 구성합니다
          </p>
          
          <!-- Config Preview -->
          <div v-if="simulationConfig" class="config-detail-panel">
            <!-- 시간 설정 -->
            <div class="config-block">
              <div class="config-grid">
                <div class="config-item">
                  <span class="config-item-label">시뮬레이션 시간</span>
                  
                  <span class="config-item-value">{{ simulationConfig.time_config?.total_simulation_hours || '-' }} 시간</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">라운드당 시간</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.minutes_per_round || '-' }} 분</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">총 라운드 수</span>
                  <span class="config-item-value">{{ Math.floor((simulationConfig.time_config?.total_simulation_hours * 60 / simulationConfig.time_config?.minutes_per_round)) || '-' }} 라운드</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">시간당 활성</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.agents_per_hour_min }}-{{ simulationConfig.time_config?.agents_per_hour_max }}</span>
                </div>
              </div>
              <div class="time-periods">
                <div class="period-item">
                  <span class="period-label">피크 시간대</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.peak_hours?.join(':00, ') }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.peak_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">업무 시간대</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.work_hours?.[0] }}:00-{{ simulationConfig.time_config?.work_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.work_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">오전 시간대</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.morning_hours?.[0] }}:00-{{ simulationConfig.time_config?.morning_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.morning_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">비활성 시간대</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.off_peak_hours?.[0] }}:00-{{ simulationConfig.time_config?.off_peak_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.off_peak_activity_multiplier }}</span>
                </div>
              </div>
            </div>

            <!-- Agent 설정 -->
            <div class="config-block">
              <div class="config-block-header">
                  <span class="config-block-title">에이전트 설정</span>
                  <span class="config-block-badge">{{ simulationConfig.agent_configs?.length || 0 }} 개</span>
              </div>
              <div class="agents-cards">
                <div 
                  v-for="agent in simulationConfig.agent_configs" 
                  :key="agent.agent_id" 
                  class="agent-card"
                >
                  <!-- 카드 헤더 -->
                  <div class="agent-card-header">
                    <div class="agent-identity">
                        <span class="agent-id">에이전트 {{ agent.agent_id }}</span>
                      <span class="agent-name">{{ agent.entity_name }}</span>
                    </div>
                    <div class="agent-tags">
                      <span class="agent-type">{{ agent.entity_type }}</span>
                      <span class="agent-stance" :class="'stance-' + agent.stance">{{ agent.stance }}</span>
                    </div>
                  </div>
                  
                  <!-- 활성 타임라인 -->
                  <div class="agent-timeline">
                    <span class="timeline-label">활성 시간대</span>
                    <div class="mini-timeline">
                      <div 
                        v-for="hour in 24" 
                        :key="hour - 1" 
                        class="timeline-hour"
                        :class="{ 'active': agent.active_hours?.includes(hour - 1) }"
                        :title="`${hour - 1}:00`"
                      ></div>
                    </div>
                    <div class="timeline-marks">
                      <span>0</span>
                      <span>6</span>
                      <span>12</span>
                      <span>18</span>
                      <span>24</span>
                    </div>
                  </div>

                  <!-- 행동 파라미터 -->
                  <div class="agent-params">
                    <div class="param-group">
                      <div class="param-item">
                        <span class="param-label">게시/시간</span>
                        <span class="param-value">{{ agent.posts_per_hour }}</span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">댓글/시간</span>
                        <span class="param-value">{{ agent.comments_per_hour }}</span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">응답 지연</span>
                        <span class="param-value">{{ agent.response_delay_min }}-{{ agent.response_delay_max }}min</span>
                      </div>
                    </div>
                    <div class="param-group">
                      <div class="param-item">
                        <span class="param-label">활성도</span>
                        <span class="param-value with-bar">
                          <span class="mini-bar" :style="{ width: (agent.activity_level * 100) + '%' }"></span>
                          {{ (agent.activity_level * 100).toFixed(0) }}%
                        </span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">감성 편향</span>
                        <span class="param-value" :class="agent.sentiment_bias > 0 ? 'positive' : agent.sentiment_bias < 0 ? 'negative' : 'neutral'">
                          {{ agent.sentiment_bias > 0 ? '+' : '' }}{{ agent.sentiment_bias?.toFixed(1) }}
                        </span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">영향력</span>
                        <span class="param-value highlight">{{ agent.influence_weight?.toFixed(1) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 플랫폼 설정 -->
            <div class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">추천 알고리즘 설정</span>
              </div>
              <div class="platforms-grid">
                <div v-if="simulationConfig.twitter_config" class="platform-card">
                  <div class="platform-card-header">
                    <span class="platform-name">월드 1: 광장 / 피드</span>
                  </div>
                  <div class="platform-params">
                    <div class="param-row">
                      <span class="param-label">시간 가중치</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.recency_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">인기 가중치</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.popularity_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">관련성 가중치</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.relevance_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">바이럴 임계값</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.viral_threshold }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">에코 챔버 강도</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.echo_chamber_strength }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="simulationConfig.reddit_config" class="platform-card">
                  <div class="platform-card-header">
                    <span class="platform-name">월드 2: 토픽 / 커뮤니티</span>
                  </div>
                  <div class="platform-params">
                    <div class="param-row">
                      <span class="param-label">시간 가중치</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.recency_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">인기 가중치</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.popularity_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">관련성 가중치</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.relevance_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">바이럴 임계값</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.viral_threshold }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">에코 챔버 강도</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.echo_chamber_strength }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- LLM 설정 추론 -->
            <div v-if="simulationConfig.generation_reasoning" class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">구성 근거 요약</span>
              </div>
              <div class="reasoning-content">
                <div 
                  v-for="(reason, idx) in simulationConfig.generation_reasoning.split('|').slice(0, 2)" 
                  :key="idx" 
                  class="reasoning-item"
                >
                  <p class="reasoning-text">{{ reason.trim() }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 04: 초기 활성화 오케스트레이션 -->
      <div class="step-card" :class="{ 'active': phase === 3, 'completed': phase > 3 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">04</span>
            <span class="step-title">초기 확산 조건 설정</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 3" class="badge success">완료</span>
            <span v-else-if="phase === 3" class="badge processing">편성 중</span>
            <span v-else class="badge pending">대기</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            시나리오의 출발점이 될 초기 게시물, 주요 토픽, 확산 방향을 설정합니다
          </p>

          <div v-if="simulationConfig?.event_config" class="orchestration-content">
            <!-- 내러티브 방향 -->
            <div class="narrative-box">
              <span class="box-label narrative-label">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="special-icon">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M16.24 7.76L14.12 14.12L7.76 16.24L9.88 9.88L16.24 7.76Z" fill="url(#paint0_linear)" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <defs>
                    <linearGradient id="paint0_linear" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                      <stop stop-color="#0F5FDB"/>
                      <stop offset="1" stop-color="#0F766E"/>
                    </linearGradient>
                  </defs>
                </svg>
                내러티브 가이드 방향
              </span>
              <p class="narrative-text">{{ simulationConfig.event_config.narrative_direction }}</p>
            </div>

            <!-- 인기 토픽 -->
            <div class="topics-section">
              <span class="box-label">초기 핵심 토픽</span>
              <div class="hot-topics-grid">
                <span v-for="topic in simulationConfig.event_config.hot_topics" :key="topic" class="hot-topic-tag">
                  # {{ topic }}
                </span>
              </div>
            </div>

            <!-- 초기 게시물 흐름 -->
            <div class="initial-posts-section">
              <span class="box-label">초기 활성화 시퀀스 ({{ simulationConfig.event_config.initial_posts.length }})</span>
              <div class="posts-timeline">
                <div v-for="(post, idx) in simulationConfig.event_config.initial_posts" :key="idx" class="timeline-item">
                  <div class="timeline-marker"></div>
                  <div class="timeline-content">
                    <div class="post-header">
                      <span class="post-role">{{ post.poster_type }}</span>
                      <span class="post-agent-info">
                        <span class="post-id">에이전트 {{ post.poster_agent_id }}</span>
                        <span class="post-username">@{{ getAgentUsername(post.poster_agent_id) }}</span>
                      </span>
                    </div>
                    <p class="post-text">{{ post.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 05: 준비 완료 -->
      <div class="step-card" :class="{ 'active': phase === 4 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">05</span>
            <span class="step-title">실행 준비 완료</span>
          </div>
          <div class="step-status">
            <span v-if="phase >= 4" class="badge processing">진행 중</span>
            <span v-else class="badge pending">대기</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">분석 실행 환경이 준비되었습니다. 시나리오 실행을 시작할 수 있습니다</p>
          
          <!-- 시뮬레이션 라운드 설정 - 설정 생성 완료 후 라운드 수가 계산된 경우에만 표시 -->
          <div v-if="simulationConfig && autoGeneratedRounds" class="rounds-config-section">
            <div class="rounds-header">
              <span class="section-title">시뮬레이션 라운드 설정</span>
              <span class="section-desc">Tiresias가 현실 <span class="desc-highlight">{{ simulationConfig?.time_config?.total_simulation_hours || '-' }}</span> 시간 범위를 기준으로 시나리오를 구성하며, 각 라운드는 현실 <span class="desc-highlight">{{ simulationConfig?.time_config?.minutes_per_round || '-' }}</span> 분의 시간 경과를 나타냅니다. 실행 라운드는 최소 <span class="desc-highlight">{{ MIN_SIMULATION_ROUNDS }}</span>부터 조정할 수 있습니다</span>
              <label class="switch-control">
                <input type="checkbox" v-model="useCustomRounds">
                <span class="switch-track"></span>
                <span class="switch-label">사용자 지정</span>
              </label>
            </div>
            
            <Transition name="fade" mode="out-in">
              <div v-if="useCustomRounds" class="rounds-content custom" key="custom">
                <div class="slider-display">
                  <span class="val-num">{{ customMaxRounds }}</span>
                  <span class="val-unit">라운드</span>
                  <span class="slider-meta-info">약 {{ Math.round(customMaxRounds * 0.6) }}분 소요</span>
                </div>

                <div class="range-wrapper">
                  <input 
                    type="range" 
                    v-model.number="customMaxRounds" 
                    :min="MIN_SIMULATION_ROUNDS"
                    :max="autoGeneratedRounds"
                    step="5"
                    class="minimal-slider"
                    :style="{ '--percent': sliderPercent }"
                  />
                  <div class="range-marks">
                    <span>{{ MIN_SIMULATION_ROUNDS }}</span>
                    <span 
                      class="mark-recommend" 
                      :class="{ active: customMaxRounds === recommendedCustomRounds }"
                      @click="customMaxRounds = recommendedCustomRounds"
                      :style="{ position: 'absolute', left: recommendedMarkLeft }"
                    >{{ recommendedCustomRounds }} (권장)</span>
                    <span>{{ autoGeneratedRounds }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else class="rounds-content auto" key="auto">
                <div class="auto-info-card-v">
                  <div class="auto-top-row">
                  <span class="val-num">{{ autoGeneratedRounds }}</span>
                  <span class="val-unit">라운드</span>
                  <span class="duration-badge-inline">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                      약 {{ Math.round(autoGeneratedRounds * 0.6) }}분 소요
                    </span>
                </div>
                  <p class="highlight-tip" @click="useCustomRounds = true">검토 범위를 빠르게 확인하려면 ‘사용자 지정’으로 {{ MIN_SIMULATION_ROUNDS }}~{{ autoGeneratedRounds }} 라운드 범위에서 축소 실행할 수 있습니다 ➝</p>
                </div>
              </div>
            </Transition>
          </div>

          <div class="action-group">
            <button
              class="action-btn primary"
              :disabled="phase < 4"
              @click="handleStartSimulation"
            >
              시나리오 실행 시작 ➝
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Detail Modal -->
    <Transition name="modal">
      <div v-if="selectedProfile" class="profile-modal-overlay" @click.self="selectedProfile = null">
        <div class="profile-modal">
          <div class="modal-header">
          <div class="modal-header-info">
            <div class="modal-name-row">
              <span class="modal-realname">{{ selectedProfile.username }}</span>
              <span class="modal-username">@{{ selectedProfile.name }}</span>
            </div>
            <span class="modal-profession">{{ selectedProfile.profession }}</span>
          </div>
          <button class="close-btn" @click="selectedProfile = null">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 기본 정보 -->
          <div class="modal-info-grid">
            <div class="info-item">
              <span class="info-label">이벤트 표시 나이</span>
              
              <span class="info-value">{{ selectedProfile.age || '-' }} 세</span>
            </div>
            <div class="info-item">
              <span class="info-label">이벤트 표시 성별</span>
              <span class="info-value">{{ { male: '남성', female: '여성', other: '기타' }[selectedProfile.gender] || selectedProfile.gender }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">국가/지역</span>
              <span class="info-value">{{ selectedProfile.country || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">이벤트 표시 MBTI</span>
              <span class="info-value mbti">{{ selectedProfile.mbti || '-' }}</span>
            </div>
          </div>

          <!-- 소개 -->
          <div class="modal-section">
            <span class="section-label">페르소나 소개</span>
            
            <p class="section-bio">{{ selectedProfile.bio || '소개 없음' }}</p>
          </div>

          <!-- 관심 토픽 -->
          <div class="modal-section" v-if="selectedProfile.interested_topics?.length">
            <span class="section-label">관심 토픽</span>
            <div class="topics-grid">
              <span 
                v-for="topic in selectedProfile.interested_topics" 
                :key="topic" 
                class="topic-item"
              >{{ topic }}</span>
            </div>
          </div>

          <!-- 상세 페르소나 -->
          <div class="modal-section" v-if="selectedProfile.persona">
            <span class="section-label">상세 모델 배경</span>
            
            <!-- 페르소나 차원 개요 -->
            <div class="persona-dimensions">
              <div class="dimension-card">
                <span class="dim-title">상황 경험</span>
                <span class="dim-desc">이 이슈에서의 전체 행동 궤적</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">행동 패턴 프로파일</span>
                <span class="dim-desc">요약된 행동 스타일과 선호도</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">기억 맥락</span>
                <span class="dim-desc">현실 시드를 기반으로 형성된 기억</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">사회적 관계 네트워크</span>
                <span class="dim-desc">연결 관계와 상호작용 구조</span>
              </div>
            </div>

            <div class="persona-content">
              <p class="section-persona">{{ selectedProfile.persona }}</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </Transition>

    <!-- System logs removed -->
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  prepareSimulation, 
  getPrepareStatus, 
  getSimulationProfilesRealtime,
  getSimulationConfig,
  getSimulationConfigRealtime 
} from '../api/simulation'
import { getCapacityState, isCapacityError } from '../api/capacity'
import { formatQueueMessage, getQueuePollSeconds, getQueueStatus, isQueuedResponse } from '../api/queue'
import { PROJECT_STATUS, normalizeProjectStatus } from '../utils/projectStatus.js'
import { buildAuthFetchOptions } from '../store/auth.js'

const props = defineProps({
  simulationId: String,  // 부모 컴포넌트에서 전달
  projectData: Object,
  graphData: Object,
  systemLogs: Array,
  autoStartEnabled: {
    type: Boolean,
    default: true,
  }
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

// State
const phase = ref(0) // 0: 초기화, 1: 페르소나 생성, 2: 설정 생성, 3: 완료
const taskId = ref(null)
const prepareProgress = ref(0)
const currentStage = ref('')
const currentStageProgress = ref(0)
const progressMessage = ref('')
const profiles = ref([])
const entityTypes = ref([])
const expectedTotal = ref(null)
const simulationConfig = ref(null)
const selectedProfile = ref(null)
const showProfilesDetail = ref(true)
const prepareError = ref('')
const prepareWaiting = ref(false)
const prepareRetryCountdown = ref(0)
const prepareQueueState = ref(null)
const hasStartedInitialPrepare = ref(false)

// 로그 중복 제거: 마지막으로 출력된 핵심 정보를 기록
let lastLoggedMessage = ''
let lastLoggedProfileCount = 0
let lastLoggedConfigStage = ''
let lastPrepareQueueLogKey = ''

// 시뮬레이션 라운드 설정
const MIN_SIMULATION_ROUNDS = 10
const DEFAULT_RECOMMENDED_CUSTOM_ROUNDS = 40
const useCustomRounds = ref(false) // 기본적으로 자동 설정 라운드 수 사용
const customMaxRounds = ref(DEFAULT_RECOMMENDED_CUSTOM_ROUNDS)

// Watch stage to update phase
watch(currentStage, (newStage) => {
  if (newStage === 'Agent 페르소나 생성' || newStage === 'generating_profiles') {
    phase.value = 1
  } else if (newStage === '시뮬레이션 설정 생성' || newStage === 'generating_config') {
    phase.value = 2
    // 설정 생성 단계 진입, 설정 폴링 시작
    if (!configTimer) {
      addLog('듀얼 플랫폼 시뮬레이션 설정 생성 시작...')
      startConfigPolling()
    }
  } else if (newStage === '시뮬레이션 스크립트 준비' || newStage === 'copying_scripts') {
    phase.value = 2 // 여전히 설정 단계에 해당
  }
})

// 설정에서 자동 생성된 라운드 수 계산 (하드코딩된 기본값 사용하지 않음)
const autoGeneratedRounds = computed(() => {
  if (!simulationConfig.value?.time_config) {
    return null // 설정이 생성되지 않은 경우 null 반환
  }
  const totalHours = simulationConfig.value.time_config.total_simulation_hours
  const minutesPerRound = simulationConfig.value.time_config.minutes_per_round
  if (!totalHours || !minutesPerRound) {
    return null // 설정 데이터가 불완전한 경우 null 반환
  }
  const calculatedRounds = Math.floor((totalHours * 60) / minutesPerRound)
  return Math.min(Math.max(calculatedRounds, MIN_SIMULATION_ROUNDS), 60)
})

const recommendedCustomRounds = computed(() => {
  const upperBound = autoGeneratedRounds.value || DEFAULT_RECOMMENDED_CUSTOM_ROUNDS
  return Math.min(DEFAULT_RECOMMENDED_CUSTOM_ROUNDS, upperBound)
})

const sliderPercent = computed(() => {
  const max = autoGeneratedRounds.value || MIN_SIMULATION_ROUNDS
  const span = Math.max(max - MIN_SIMULATION_ROUNDS, 1)
  const clamped = Math.min(Math.max(customMaxRounds.value, MIN_SIMULATION_ROUNDS), max)
  return `${((clamped - MIN_SIMULATION_ROUNDS) / span) * 100}%`
})

const recommendedMarkLeft = computed(() => {
  const max = autoGeneratedRounds.value || MIN_SIMULATION_ROUNDS
  const span = Math.max(max - MIN_SIMULATION_ROUNDS, 1)
  const mark = Math.min(recommendedCustomRounds.value, max)
  return `calc(${((mark - MIN_SIMULATION_ROUNDS) / span) * 100}% - 30px)`
})

watch(autoGeneratedRounds, (newRounds) => {
  if (!newRounds) return
  if (customMaxRounds.value < MIN_SIMULATION_ROUNDS || customMaxRounds.value > newRounds) {
    customMaxRounds.value = Math.min(Math.max(recommendedCustomRounds.value, MIN_SIMULATION_ROUNDS), newRounds)
  }
}, { immediate: true })

// Polling timer
let pollTimer = null
let profilesTimer = null
let configTimer = null
let prepareRetryTimer = null
let prepareQueuePollTimer = null
let queuedPreparePayload = null

// Computed
const displayProfiles = computed(() => {
  if (showProfilesDetail.value) {
    return profiles.value
  }
  return profiles.value.slice(0, 6)
})

// agent_id로 해당 username 가져오기
const getAgentUsername = (agentId) => {
  if (profiles.value && profiles.value.length > agentId && agentId >= 0) {
    const profile = profiles.value[agentId]
    return profile?.username || `agent_${agentId}`
  }
  return `agent_${agentId}`
}

// 모든 페르소나의 연관 토픽 총 수 계산
const totalTopicsCount = computed(() => {
  return profiles.value.reduce((sum, p) => {
    return sum + (p.interested_topics?.length || 0)
  }, 0)
})

const personaProgress = computed(() => {
  const total = Number(expectedTotal.value || 0)
  const generated = profiles.value.length

  if (phase.value !== 1) {
    return prepareProgress.value
  }

  if (total > 0 && generated > 0) {
    return Math.min(
      99,
      Math.max(
        currentStageProgress.value || 0,
        Math.round((generated / total) * 100)
      )
    )
  }

  if (currentStageProgress.value > 0) {
    return currentStageProgress.value
  }

  if (prepareProgress.value > 20 && prepareProgress.value < 70) {
    return Math.min(99, Math.max(0, Math.round(((prepareProgress.value - 20) / 50) * 100)))
  }

  return prepareProgress.value
})

const normalizedProjectStatus = computed(() => {
  return normalizeProjectStatus(props.projectData?.status, {
    reportId: props.projectData?.report_id || props.projectData?.reportId || null,
  })
})

const isReportLockedProject = computed(() => {
  const status = normalizedProjectStatus.value
  return Boolean(
    props.projectData?.report_id ||
    props.projectData?.reportId ||
    status === PROJECT_STATUS.REPORT_GENERATING ||
    status === PROJECT_STATUS.REPORT_COMPLETED
  )
})

const shouldLoadExistingPrepareResult = computed(() => {
  const status = normalizedProjectStatus.value
  return new Set([
    PROJECT_STATUS.SIMULATION_READY,
    PROJECT_STATUS.SIMULATION_COMPLETED,
    PROJECT_STATUS.SIMULATION_STOPPED,
    PROJECT_STATUS.REPORT_GENERATING,
    PROJECT_STATUS.REPORT_COMPLETED,
  ]).has(status)
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

const stopPrepareRetry = () => {
  if (prepareRetryTimer) {
    clearInterval(prepareRetryTimer)
    prepareRetryTimer = null
  }
  prepareRetryCountdown.value = 0
}

const stopPrepareQueue = () => {
  if (prepareQueuePollTimer) {
    clearTimeout(prepareQueuePollTimer)
    prepareQueuePollTimer = null
  }
  queuedPreparePayload = null
  prepareQueueState.value = null
  lastPrepareQueueLogKey = ''
  stopPrepareRetry()
}

const logPrepareQueueState = (queue) => {
  if (!queue) return
  const logKey = `${queue.status}:${queue.position}:${queue.totalWaiting}:${queue.lastError || ''}`
  if (logKey === lastPrepareQueueLogKey) {
    return
  }
  lastPrepareQueueLogKey = logKey
  addLog(formatQueueMessage(queue, '현재 환경 준비 대기열에 등록되었습니다.'))
}

const schedulePrepareQueuePoll = (seconds) => {
  if (prepareQueuePollTimer) {
    clearTimeout(prepareQueuePollTimer)
    prepareQueuePollTimer = null
  }

  stopPrepareRetry()
  prepareRetryCountdown.value = seconds
  prepareRetryTimer = setInterval(() => {
    prepareRetryCountdown.value -= 1
    if (prepareRetryCountdown.value <= 0) {
      stopPrepareRetry()
    }
  }, 1000)

  prepareQueuePollTimer = setTimeout(async () => {
    prepareQueuePollTimer = null
    await pollPrepareQueueStatus()
  }, seconds * 1000)
}

const enterPrepareQueue = (queue, payload) => {
  prepareWaiting.value = true
  prepareQueueState.value = queue
  queuedPreparePayload = payload
  prepareError.value = formatQueueMessage(queue, '현재 환경 준비 대기열에 등록되었습니다.')
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
  emit('update-status', 'processing')
  logPrepareQueueState(queue)
  schedulePrepareQueuePoll(getQueuePollSeconds(queue))
}

const pollPrepareQueueStatus = async () => {
  const queueId = prepareQueueState.value?.id
  if (!queueId) {
    return
  }

  try {
    const response = await getQueueStatus(queueId)
    const queue = response.queue

    if (!queue) {
      stopPrepareQueue()
      return
    }

    if (queue.status === 'failed') {
      stopPrepareQueue()
      await markPrepareFailed(queue.lastError || '환경 준비 대기열 처리에 실패했습니다.')
      return
    }

    if (queue.status === 'completed') {
      const payload = queuedPreparePayload || {
        simulation_id: props.simulationId,
        use_llm_for_profiles: true,
        parallel_profile_count: 5
      }
      stopPrepareQueue()
      await startPrepareSimulation({ payload })
      return
    }

    prepareQueueState.value = queue
    prepareError.value = formatQueueMessage(queue, '현재 환경 준비 대기열에 등록되었습니다.')
    logPrepareQueueState(queue)

    if (queue.ready) {
      const payload = queuedPreparePayload || {
        simulation_id: props.simulationId,
        use_llm_for_profiles: true,
        parallel_profile_count: 5
      }
      stopPrepareQueue()
      await startPrepareSimulation({ queueId: queue.id, payload })
      return
    }

    schedulePrepareQueuePoll(getQueuePollSeconds(queue))
  } catch (error) {
    prepareError.value = '대기열 상태를 다시 확인하는 중입니다...'
    schedulePrepareQueuePoll(3)
  }
}

const schedulePrepareRetry = (error) => {
  const state = getCapacityState(error)
  const retryAfter = state?.retryAfter || 60
  const waitMessage = state?.message || '현재 다른 사용자의 준비 작업이 진행 중입니다. 잠시 후 자동으로 다시 시도합니다.'

  prepareWaiting.value = true
  prepareQueueState.value = null
  queuedPreparePayload = null
  prepareError.value = waitMessage
  prepareRetryCountdown.value = retryAfter
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
  addLog(`⏳ ${waitMessage}`)
  emit('update-status', 'processing')

  stopPrepareRetry()
  prepareRetryCountdown.value = retryAfter
  prepareRetryTimer = setInterval(async () => {
    prepareRetryCountdown.value -= 1
    if (prepareRetryCountdown.value > 0) {
      return
    }
    stopPrepareRetry()
    await startPrepareSimulation()
  }, 1000)
}

const markPrepareFailed = async (message) => {
  prepareWaiting.value = false
  stopPrepareQueue()
  prepareError.value = message || '환경 준비에 실패했습니다'
  addLog(`✗ ${prepareError.value}`)
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
  await syncProjectStatus(PROJECT_STATUS.FAILED)
  emit('update-status', 'error')
}

const getPreparedAgentCount = (data) => {
  return Math.max(
    data?.summary?.total_agents || 0,
    data?.config?.agent_configs?.length || 0,
    profiles.value.length
  )
}

const hasUsablePreparedConfig = (data) => {
  return Boolean(
    data?.config_generated &&
    data?.config &&
    getPreparedAgentCount(data) > 0
  )
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

// 시뮬레이션 시작 버튼 클릭 처리
const handleStartSimulation = () => {
  // 부모 컴포넌트에 전달할 파라미터 구성
  const params = {}
  
  if (useCustomRounds.value) {
    // 사용자 지정 라운드 수, max_rounds 파라미터 전달
    const appliedCustomRounds = Math.max(
      MIN_SIMULATION_ROUNDS,
      Math.min(customMaxRounds.value, autoGeneratedRounds.value || customMaxRounds.value)
    )
    params.maxRounds = appliedCustomRounds
    addLog(`시뮬레이션 시작, 사용자 지정 라운드 수: ${appliedCustomRounds} 라운드`)
  } else {
    // 사용자가 자동 생성된 라운드 수 유지 선택, max_rounds 파라미터 전달하지 않음
    addLog(`시뮬레이션 시작, 자동 설정 라운드 수 사용: ${autoGeneratedRounds.value} 라운드`)
  }
  
  emit('next-step', params)
}

const truncateBio = (bio) => {
  if (bio.length > 80) {
    return bio.substring(0, 80) + '...'
  }
  return bio
}

const selectProfile = (profile) => {
  selectedProfile.value = profile
}

const maybeStartInitialPrepare = async () => {
  if (hasStartedInitialPrepare.value || !props.simulationId || !props.autoStartEnabled) {
    return
  }

  if (isReportLockedProject.value) {
    stopPrepareQueue()
    stopPolling()
    stopProfilesPolling()
    stopConfigPolling()
    return
  }

  hasStartedInitialPrepare.value = true
  addLog('Step2 환경 설정 초기화')

  if (shouldLoadExistingPrepareResult.value) {
    await loadPreparedData()
    return
  }

  await startPrepareSimulation()
}

// 자동으로 시뮬레이션 준비 시작
const startPrepareSimulation = async ({ queueId = null, payload = null } = {}) => {
  if (!props.simulationId) {
    addLog('오류: simulationId가 없습니다')
    emit('update-status', 'error')
    return
  }

  if (isReportLockedProject.value) {
    stopPrepareQueue()
    stopPolling()
    stopProfilesPolling()
    stopConfigPolling()
    return
  }
  
  stopPrepareQueue()
  prepareWaiting.value = false
  prepareError.value = ''
  // 첫 번째 단계 완료 표시, 두 번째 단계 시작
  phase.value = 1
  addLog(`시뮬레이션 인스턴스 생성됨: ${props.simulationId}`)
  addLog('시뮬레이션 환경 준비 중...')
  emit('update-status', 'processing')
  
  try {
    const requestPayload = payload || {
      simulation_id: props.simulationId,
      use_llm_for_profiles: true,
      parallel_profile_count: 5
    }

    const res = await prepareSimulation({
      ...requestPayload,
      ...(queueId ? { queue_id: queueId } : {})
    })

    if (isQueuedResponse(res)) {
      enterPrepareQueue(res.queue, requestPayload)
      return
    }
    
    if (res.success && res.data) {
      if (res.data.already_prepared) {
        addLog('완료된 준비 작업이 감지되었습니다. 바로 사용합니다')
        await loadPreparedData()
        return
      }
      
      taskId.value = res.data.task_id
      addLog(`준비 작업이 시작되었습니다`)
      addLog(`  └─ Task ID: ${res.data.task_id}`)
      
      // 예상 Agent 총 수 즉시 설정 (prepare 인터페이스 반환값에서 가져옴)
      if (res.data.expected_entities_count) {
        expectedTotal.value = res.data.expected_entities_count
        addLog(`지식 그래프에서 ${res.data.expected_entities_count}개의 엔티티를 읽었습니다`)
        if (res.data.entity_types && res.data.entity_types.length > 0) {
          addLog(`  └─ 엔티티 유형: ${res.data.entity_types.join(', ')}`)
        }
      }
      
      addLog('준비 진행 상황 폴링 시작...')
      // 진행 상황 폴링 시작
      startPolling()
      // 실시간 Profiles 가져오기 시작
      startProfilesPolling()
    } else {
      await markPrepareFailed(res.error || '알 수 없는 오류')
    }
  } catch (err) {
    if (isCapacityError(err)) {
      schedulePrepareRetry(err)
      return
    }
    await markPrepareFailed(err.message)
  }
}

const startPolling = () => {
  pollTimer = setInterval(pollPrepareStatus, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const startProfilesPolling = () => {
  profilesTimer = setInterval(fetchProfilesRealtime, 3000)
}

const stopProfilesPolling = () => {
  if (profilesTimer) {
    clearInterval(profilesTimer)
    profilesTimer = null
  }
}

const pollPrepareStatus = async () => {
  if (!taskId.value && !props.simulationId) return
  
  try {
    const res = await getPrepareStatus({
      task_id: taskId.value,
      simulation_id: props.simulationId
    })
    
    if (res.success && res.data) {
      const data = res.data
      
      // 진행률 업데이트
      prepareProgress.value = data.progress || 0
      progressMessage.value = data.message || ''
      
      // 단계 정보를 파싱하고 상세 로그 출력
      if (data.progress_detail) {
        currentStage.value = data.progress_detail.current_stage_name || ''
        currentStageProgress.value = data.progress_detail.stage_progress || 0
        
        // 상세 진행 로그 출력 (중복 방지)
        const detail = data.progress_detail
        const logKey = `${detail.current_stage}-${detail.current_item}-${detail.total_items}`
        if (logKey !== lastLoggedMessage && detail.item_description) {
          lastLoggedMessage = logKey
          const stageInfo = `[${detail.stage_index}/${detail.total_stages}]`
          if (detail.total_items > 0) {
            addLog(`${stageInfo} ${detail.current_stage_name}: ${detail.current_item}/${detail.total_items} - ${detail.item_description}`)
          } else {
            addLog(`${stageInfo} ${detail.current_stage_name}: ${detail.item_description}`)
          }
        }
      } else if (data.message) {
        currentStageProgress.value = 0
        // 메시지에서 단계 추출
        const match = data.message.match(/\[(\d+)\/(\d+)\]\s*([^:]+)/)
        if (match) {
          currentStage.value = match[3].trim()
        }
        // 메시지 로그 출력 (중복 방지)
        if (data.message !== lastLoggedMessage) {
          lastLoggedMessage = data.message
          addLog(data.message)
        }
      }
      
      // 완료 여부 확인
      if (data.status === 'completed' || data.status === 'ready' || data.already_prepared) {
        addLog('✓ 준비 작업이 완료되었습니다')
        stopPolling()
        stopProfilesPolling()
        await loadPreparedData()
      } else if (data.status === 'failed') {
        await markPrepareFailed(data.error || '알 수 없는 오류')
      }
    }
  } catch (err) {
    console.warn('상태 폴링 실패:', err)
  }
}

const fetchProfilesRealtime = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getSimulationProfilesRealtime(props.simulationId, 'reddit')
    
    if (res.success && res.data) {
      const prevCount = profiles.value.length
      profiles.value = res.data.profiles || []
      // API가 유효한 값을 반환한 경우에만 업데이트하여, 기존 유효값 덮어쓰기 방지
      if (res.data.total_expected) {
        expectedTotal.value = res.data.total_expected
      }
      
      // 엔티티 유형 추출
      const types = new Set()
      profiles.value.forEach(p => {
        if (p.entity_type) types.add(p.entity_type)
      })
      entityTypes.value = Array.from(types)
      
      // Profile 생성 진행 로그 출력 (수량 변경 시에만)
      const currentCount = profiles.value.length
      if (currentCount > 0 && currentCount !== lastLoggedProfileCount) {
        lastLoggedProfileCount = currentCount
        const total = expectedTotal.value || '?'
        const latestProfile = profiles.value[currentCount - 1]
        const profileName = latestProfile?.name || latestProfile?.username || `Agent_${currentCount}`
        if (currentCount === 1) {
          addLog(`Agent 페르소나 생성 시작...`)
        }
        addLog(`→ Agent 페르소나 ${currentCount}/${total}: ${profileName} (${latestProfile?.profession || '알 수 없는 직업'})`)
        
        // 전체 생성 완료 시
        if (expectedTotal.value && currentCount >= expectedTotal.value) {
          addLog(`✓ 전체 ${currentCount} 개 Agent 페르소나 생성 완료`)
        }
      }
    }
  } catch (err) {
    console.warn('Profiles 가져오기 실패:', err)
  }
}

// 설정 폴링
const startConfigPolling = () => {
  configTimer = setInterval(fetchConfigRealtime, 2000)
}

const stopConfigPolling = () => {
  if (configTimer) {
    clearInterval(configTimer)
    configTimer = null
  }
}

const fetchConfigRealtime = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    
    if (res.success && res.data) {
      const data = res.data
      
      // 설정 생성 단계 로그 출력 (중복 방지)
      if (data.generation_stage && data.generation_stage !== lastLoggedConfigStage) {
        lastLoggedConfigStage = data.generation_stage
        if (data.generation_stage === 'generating_profiles') {
          addLog('Agent 페르소나 설정 생성 중...')
        } else if (data.generation_stage === 'generating_config') {
          addLog('LLM을 호출하여 시뮬레이션 설정 파라미터 생성 중...')
        }
      }
      
      // 설정이 이미 생성된 경우
      if (hasUsablePreparedConfig(data)) {
        simulationConfig.value = data.config
        addLog('✓ 시뮬레이션 설정 생성 완료')

        // 상세 설정 요약 표시
        if (data.summary) {
          addLog(`  ├─ Agent 수: ${data.summary.total_agents}개`)
          addLog(`  ├─ 시뮬레이션 시간: ${data.summary.simulation_hours}시간`)
          addLog(`  ├─ 초기 게시물: ${data.summary.initial_posts_count}개`)
          addLog(`  ├─ 인기 토픽: ${data.summary.hot_topics_count}개`)
          addLog(`  └─ 플랫폼 설정: Twitter ${data.summary.has_twitter_config ? '✓' : '✗'}, Reddit ${data.summary.has_reddit_config ? '✓' : '✗'}`)
        }
        
        // 시간 설정 상세 표시
        if (data.config.time_config) {
          const tc = data.config.time_config
          addLog(`시간 설정: 라운드당 ${tc.minutes_per_round}분, 총 ${Math.floor((tc.total_simulation_hours * 60) / tc.minutes_per_round)} 라운드`)
        }
        
        // 이벤트 설정 표시
        if (data.config.event_config?.narrative_direction) {
          const narrative = data.config.event_config.narrative_direction
          addLog(`내러티브 방향: ${narrative.length > 50 ? narrative.substring(0, 50) + '...' : narrative}`)
        }
        
        stopConfigPolling()
        phase.value = 4
        addLog('✓ 환경 설정 완료, 시뮬레이션을 시작할 수 있습니다')
        await syncProjectStatus(PROJECT_STATUS.SIMULATION_READY)
        emit('update-status', 'completed')
      } else if (data.config_generated && data.config) {
        await markPrepareFailed('생성된 Agent가 없어 환경 설정을 완료 처리할 수 없습니다')
      }
    }
  } catch (err) {
    console.warn('설정 가져오기 실패:', err)
  }
}

const loadPreparedData = async () => {
  phase.value = 2
  addLog('기존 설정 데이터 로딩 중...')

  // 마지막으로 한 번 Profiles 가져오기
  await fetchProfilesRealtime()
  addLog(`${profiles.value.length} 개 Agent 페르소나 로드 완료`)

  // 설정 가져오기 (실시간 인터페이스 사용)
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    if (res.success && res.data) {
      if (hasUsablePreparedConfig(res.data)) {
        simulationConfig.value = res.data.config
        addLog('✓ 시뮬레이션 설정 로드 성공')

        // 상세 설정 요약 표시
        if (res.data.summary) {
          addLog(`  ├─ Agent 수: ${res.data.summary.total_agents}개`)
          addLog(`  ├─ 시뮬레이션 시간: ${res.data.summary.simulation_hours}시간`)
          addLog(`  └─ 초기 게시물: ${res.data.summary.initial_posts_count}개`)
        }
        
        addLog('✓ 환경 설정 완료, 시뮬레이션을 시작할 수 있습니다')
        phase.value = 4
        await syncProjectStatus(PROJECT_STATUS.SIMULATION_READY)
        emit('update-status', 'completed')
      } else if (res.data.config_generated && res.data.config) {
        await markPrepareFailed('생성된 Agent가 없어 환경 설정을 완료 처리할 수 없습니다')
      } else {
        // 설정이 아직 생성되지 않음, 폴링 시작
        addLog('설정 생성 중, 폴링 대기 시작...')
        startConfigPolling()
      }
    }
  } catch (err) {
    await markPrepareFailed(`설정 로드 실패: ${err.message}`)
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

watch(
  () => [props.autoStartEnabled, props.simulationId, props.projectData?.status, props.projectData?.report_id, props.projectData?.reportId],
  async () => {
    if (isReportLockedProject.value) {
      stopPrepareQueue()
      stopPolling()
      stopProfilesPolling()
      stopConfigPolling()
      return
    }

    await maybeStartInitialPrepare()
  },
  { immediate: true }
)

onMounted(async () => {
  await maybeStartInitialPrepare()
})

onUnmounted(() => {
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
  stopPrepareQueue()
})
</script>

<style scoped>
.env-setup-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  font-family: 'Inter', 'Noto Sans KR', system-ui, sans-serif;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Step Card */
.step-card {
  background: var(--bg-secondary);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  position: relative;
}

.step-card.active {
  border-color: #0F5FDB;
  box-shadow: 0 8px 24px rgba(15, 95, 219, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-muted);
}

.step-card.active .step-num,
.step-card.completed .step-num {
  color: var(--text-primary);
}

.step-title {
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.5px;
  line-height: 1.3;
  color: var(--text-primary);
}

.badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  text-transform: uppercase;
}

.badge.success { background: rgba(46, 125, 50, 0.15); color: #4CAF50; }
.badge.processing { background: #0F5FDB; color: #FFF; }
.badge.pending { background: var(--bg-tertiary); color: var(--text-muted); }
.badge.accent { background: rgba(99, 102, 241, 0.15); color: #818CF8; }

.card-content {
  /* No extra padding - uses step-card's padding */
}

.api-note {
  display: none;
}

.description {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 16px;
}

.prepare-error-panel {
  margin-bottom: 16px;
  padding: 14px;
  border-radius: 8px;
  border: 1px solid #D5E3FF;
  background: #F6F9FF;
}

.prepare-error-title {
  font-size: 12px;
  font-weight: 700;
  color: #0F5FDB;
  margin-bottom: 6px;
}

.prepare-error-message {
  margin: 0 0 12px;
  font-size: 11px;
  line-height: 1.5;
  color: #475569;
  white-space: pre-wrap;
}

.prepare-error-meta {
  margin: 0 0 12px;
  font-size: 11px;
  color: #64748B;
}

.prepare-error-btn {
  height: 34px;
  padding: 0 12px;
  border: none;
  border-radius: 6px;
  background: #0F5FDB;
  color: #FFF;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

/* Action Section */
.action-section {
  margin-top: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: var(--accent-color);
  color: #FFF;
}

.action-btn.primary:hover:not(:disabled) {
  opacity: 0.8;
}

.action-btn.secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn.secondary:hover:not(:disabled) {
  background: var(--surface-hover);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-group {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.action-group.dual {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.action-group.dual .action-btn {
  width: 100%;
}

/* Info Card */
.info-card {
  background: var(--bg-tertiary);
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed var(--border-color);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.info-value.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  background: var(--bg-tertiary);
  padding: 16px;
  border-radius: 6px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

.stat-label {
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-top: 4px;
  display: block;
}

/* Profiles Preview */
.profiles-preview {
  margin-top: 20px;
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.profiles-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

@media (min-width: 768px) {
  .profiles-list {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

.profiles-list::-webkit-scrollbar {
  width: 4px;
}

.profiles-list::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
}

.profiles-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.15);
}

.profile-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.profile-card:hover {
  border-color: rgba(255,255,255,0.12);
  background: var(--surface-hover);
}

.profile-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.profile-realname {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
}

.profile-username {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-muted);
}

.profile-meta {
  margin-bottom: 8px;
}

.profile-profession {
  font-size: 11px;
  color: var(--text-secondary);
  background: var(--bg-surface);
  padding: 2px 8px;
  border-radius: 3px;
}

.profile-bio {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.profile-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-tag {
  font-size: 10px;
  color: #818CF8;
  background: rgba(99, 102, 241, 0.12);
  padding: 2px 8px;
  border-radius: 10px;
}

.topic-more {
  font-size: 10px;
  color: var(--text-muted);
  padding: 2px 6px;
}

/* Config Preview */
/* Config Detail Panel */
.config-detail-panel {
  margin-top: 16px;
}

.config-block {
  margin-top: 16px;
  border-top: 1px solid var(--border-color);
  padding-top: 12px;
}

.config-block:first-child {
  margin-top: 0;
  border-top: none;
  padding-top: 0;
}

.config-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-block-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.config-block-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  padding: 2px 8px;
  border-radius: 10px;
}

/* Config Grid */
.config-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.config-item {
  background: var(--bg-tertiary);
  padding: 12px 14px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item-label {
  font-size: 11px;
  color: var(--text-muted);
}

.config-item-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Time Periods */
.time-periods {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.period-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
}

.period-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 70px;
}

.period-hours {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: var(--text-secondary);
  flex: 1;
}

.period-multiplier {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: #818CF8;
  background: rgba(99, 102, 241, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Agents Cards */
.agents-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

.agents-cards::-webkit-scrollbar {
  width: 4px;
}

.agents-cards::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
}

.agents-cards::-webkit-scrollbar-thumb:hover {
  background: rgba(255,255,255,0.15);
}

.agent-card {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 14px;
  transition: all 0.2s ease;
}

.agent-card:hover {
  border-color: rgba(255,255,255,0.12);
  background: var(--surface-hover);
}

/* Agent Card Header */
.agent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.agent-identity {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-tags {
  display: flex;
  gap: 6px;
}

.agent-type {
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--bg-surface);
  padding: 2px 8px;
  border-radius: 4px;
}

.agent-stance {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
}

.stance-neutral {
  background: rgba(100, 116, 139, 0.15);
  color: #94A3B8;
}

.stance-supportive {
  background: rgba(22, 163, 74, 0.15);
  color: #4ADE80;
}

.stance-opposing {
  background: rgba(220, 38, 38, 0.15);
  color: #F87171;
}

.stance-observer {
  background: rgba(217, 119, 6, 0.15);
  color: #FBBF24;
}

/* Agent Timeline */
.agent-timeline {
  margin-bottom: 14px;
}

.timeline-label {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.mini-timeline {
  display: flex;
  gap: 2px;
  height: 16px;
  background: var(--bg-surface);
  border-radius: 4px;
  padding: 3px;
}

.timeline-hour {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  transition: all 0.2s;
}

.timeline-hour.active {
  background: linear-gradient(180deg, #6366F1, #818CF8);
}

.timeline-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--text-muted);
}

/* Agent Params */
.agent-params {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.param-group {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.param-item .param-label {
  font-size: 10px;
  color: var(--text-muted);
}

.param-item .param-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.param-value.with-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mini-bar {
  height: 4px;
  background: linear-gradient(90deg, #6366F1, #A855F7);
  border-radius: 2px;
  min-width: 4px;
  max-width: 40px;
}

.param-value.positive {
  color: #4ADE80;
}

.param-value.negative {
  color: #F87171;
}

.param-value.neutral {
  color: var(--text-secondary);
}

.param-value.highlight {
  color: #818CF8;
}

/* Platforms Grid */
.platforms-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.platform-card {
  background: var(--bg-tertiary);
  padding: 14px;
  border-radius: 6px;
}

.platform-card-header {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.platform-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.platform-params {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.param-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Reasoning Content */
.reasoning-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reasoning-item {
  padding: 12px 14px;
  background: var(--bg-tertiary);
  border-radius: 6px;
}

.reasoning-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

/* Profile Modal */
.profile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.profile-modal {
  background: var(--bg-secondary);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--border-color);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.modal-header-info {
  flex: 1;
}

.modal-name-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.modal-realname {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.modal-username {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--text-muted);
}

.modal-profession {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-block;
  font-weight: 500;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--text-muted);
  border-radius: 50%;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: color 0.2s;
  padding: 0;
}

.close-btn:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* 기본 정보 그리드 */
.modal-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px 16px;
  margin-bottom: 32px;
  padding: 0;
  background: transparent;
  border-radius: 0;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.info-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.info-value.mbti {
  font-family: 'JetBrains Mono', monospace;
  color: #0F5FDB;
}

/* 모듈 영역 */
.modal-section {
  margin-bottom: 28px;
}

.section-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.section-bio {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  margin: 0;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  border-left: 3px solid var(--border-color);
}

/* 토픽 태그 */
.topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-item {
  font-size: 11px;
  color: #818CF8;
  background: rgba(99, 102, 241, 0.12);
  padding: 4px 10px;
  border-radius: 12px;
  transition: all 0.2s;
  border: none;
}

.topic-item:hover {
  background: rgba(99, 102, 241, 0.2);
  color: #A5B4FC;
}

/* 상세 페르소나 */
.persona-dimensions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.dimension-card {
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid var(--border-color);
  transition: all 0.2s;
}

.dimension-card:hover {
  background: var(--surface-hover);
  border-left-color: var(--text-muted);
}

.dim-title {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.dim-desc {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  line-height: 1.4;
}

.persona-content {
  max-height: none;
  overflow: visible;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

.persona-content::-webkit-scrollbar {
  width: 4px;
}

.persona-content::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
}

.section-persona {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0;
  text-align: justify;
}

/* System Logs */
.system-logs {
  background: #08080c;
  color: var(--text-secondary);
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .system-logs {
    display: none;
  }
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
  height: 80px; /* Approx 4 lines visible */
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar {
  width: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.1);
  border-radius: 2px;
}

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time {
  color: var(--text-muted);
  min-width: 75px;
}

.log-msg {
  color: var(--text-secondary);
  word-break: break-all;
}

@media (max-width: 768px) {
  .step-card {
    padding: 16px;
  }

  .card-header {
    flex-wrap: nowrap;
    gap: 8px;
  }

  .step-num {
    font-size: 16px;
    min-width: 28px;
  }

  .step-title {
    font-size: 12px;
  }

  .stats-grid {
    grid-template-columns: 1fr !important;
    gap: 8px;
  }

  .config-grid {
    grid-template-columns: 1fr 1fr !important;
  }

  .agents-cards {
    grid-template-columns: 1fr !important;
  }

  .api-note {
    font-size: 9px;
  }

  .description {
    font-size: 12px;
  }

  /* Round config section */
  .round-config,
  .round-setting {
    flex-direction: column;
  }

  .tooltip-card {
    max-width: 100% !important;
    font-size: 11px !important;
  }

  .badge {
    white-space: nowrap !important;
    flex-shrink: 0 !important;
  }

  .profiles-list {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
  }

  /* CRITICAL: Fix action buttons at bottom - prevent vertical text */
  .action-group.dual {
    display: flex !important;
    flex-direction: column !important;
    grid-template-columns: none !important;
    gap: 10px !important;
  }

  .action-group .action-btn,
  .action-btn.primary,
  .action-btn.secondary {
    width: 100% !important;
    min-width: 0 !important;
    white-space: normal !important;
    word-break: keep-all !important;
    padding: 14px 16px !important;
    font-size: 13px !important;
    text-align: center !important;
    justify-content: center !important;
  }
}

/* Spinner */
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-color);
  border-top-color: #0F5FDB;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
/* Orchestration Content */
.orchestration-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 16px;
}

.box-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
}

.narrative-box {
  background: var(--bg-secondary);
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 24px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.narrative-box .box-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  font-weight: 600;
}

.special-icon {
  filter: drop-shadow(0 2px 4px rgba(15, 95, 219, 0.18));
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.narrative-box:hover .special-icon {
  transform: rotate(180deg);
}

.narrative-text {
  font-family: 'Inter', 'Noto Sans KR', system-ui, sans-serif;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0;
  text-align: justify;
  letter-spacing: 0.01em;
}

.topics-section {
  background: var(--bg-secondary);
}

.hot-topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-topic-tag {
  font-size: 12px;
  color: #FF8A65;
  background: rgba(255, 87, 34, 0.12);
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.hot-topic-more {
  font-size: 11px;
  color: var(--text-muted);
  padding: 4px 6px;
}

.initial-posts-section {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}

.posts-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-left: 8px;
  border-left: 2px solid var(--border-color);
  margin-top: 12px;
}

.timeline-item {
  position: relative;
  padding-left: 20px;
}

.timeline-marker {
  position: absolute;
  left: 0;
  top: 14px;
  width: 12px;
  height: 2px;
  background: var(--text-muted);
}

.timeline-content {
  background: var(--bg-tertiary);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.post-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.post-role {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-primary);
  text-transform: uppercase;
}

.post-agent-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.post-id,
.post-username {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--text-secondary);
  line-height: 1;
  vertical-align: baseline;
}

.post-username {
  margin-right: 6px;
}

.post-text {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* 시뮬레이션 라운드 설정 스타일 */
.rounds-config-section {
  margin: 24px 0;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.rounds-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.section-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.desc-highlight {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-tertiary);
  padding: 1px 6px;
  border-radius: 4px;
  margin: 0 2px;
}

/* Switch Control */
.switch-control {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px 4px 4px;
  border-radius: 20px;
  transition: background 0.2s;
}

.switch-control:hover {
  background: var(--bg-surface);
}

.switch-control input {
  display: none;
}

.switch-track {
  width: 36px;
  height: 20px;
  background: rgba(255,255,255,0.1);
  border-radius: 10px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.switch-track::after {
  content: '';
  position: absolute;
  left: 2px;
  top: 2px;
  width: 16px;
  height: 16px;
  background: var(--text-secondary);
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.switch-control input:checked + .switch-track {
  background: var(--accent-color);
}

.switch-control input:checked + .switch-track::after {
  transform: translateX(16px);
  background: #FFF;
}

.switch-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.switch-control input:checked ~ .switch-label {
  color: var(--text-primary);
}

/* Slider Content */
.rounds-content {
  animation: fadeIn 0.3s ease;
}

.slider-display {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.val-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.val-unit {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.slider-meta-info {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-left: auto;
}

.range-wrapper {
  position: relative;
  padding: 0 2px;
}

.minimal-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 6px;
  background: #E5E7EB;
  border-radius: 3px;
  outline: none;
  background-image: linear-gradient(var(--accent-color, #6366f1), var(--accent-color, #6366f1));
  background-size: var(--percent, 0%) 100%;
  background-repeat: no-repeat;
  cursor: pointer;
}

.minimal-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--text-primary);
  border: 2px solid var(--accent-color);
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,0.3);
  transition: transform 0.1s;
  margin-top: -6px; /* Center thumb */
}

.minimal-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.minimal-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 3px;
}

.range-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  position: relative;
}

.mark-recommend {
  cursor: pointer;
  transition: color 0.2s;
  position: relative;
}

.mark-recommend:hover {
  color: var(--text-primary);
}

.mark-recommend.active {
  color: var(--text-primary);
  font-weight: 600;
}

.mark-recommend::after {
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 4px;
  background: var(--text-muted);
}

/* Auto Info */
.auto-info-card {
  display: flex;
  align-items: center;
  gap: 24px;
  background: var(--bg-tertiary);
  padding: 16px 20px;
  border-radius: 8px;
}

.auto-info-card-v {
  background: var(--bg-tertiary);
  padding: 16px 20px;
  border-radius: 8px;
}

.auto-top-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.duration-badge-inline {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-left: auto;
}

.auto-value {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 4px;
  padding-right: 24px;
  border-right: 1px solid var(--border-color);
}

.auto-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.auto-meta-row {
  display: flex;
  align-items: center;
}

.duration-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 3px 8px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.auto-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auto-desc p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.highlight-tip {
  margin-top: 4px !important;
  font-size: 12px !important;
  color: var(--text-primary) !important;
  font-weight: 500;
  cursor: pointer;
}

.highlight-tip:hover {
  text-decoration: underline;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .profile-modal {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-leave-active .profile-modal {
  transition: all 0.3s ease-in;
}

.modal-enter-from .profile-modal,
.modal-leave-to .profile-modal {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
</style>
