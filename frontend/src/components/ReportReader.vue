<template>
  <div class="report-content-wrapper">
    <div class="report-header-block">
      <div class="report-meta">
        <span class="report-tag">{{ reportTag }}</span>
        <span v-if="reportId" class="report-id">ID: {{ reportId }}</span>
      </div>
      <h1 class="main-title">{{ title || '샘플 보고서' }}</h1>
      <p v-if="summary" class="sub-title">{{ summary }}</p>
      <div class="header-divider"></div>
    </div>

    <div class="sections-list">
      <div
        v-for="(section, idx) in normalizedSections"
        :key="idx"
        class="report-section-item"
        :class="{
          'is-active': currentSectionIndex === idx + 1,
          'is-completed': Boolean(section.content),
          'is-pending': !section.content && currentSectionIndex !== idx + 1
        }"
      >
        <div
          class="section-header-row"
          :class="{ clickable: Boolean(section.content) && collapsible }"
          @click="toggleSectionCollapse(idx)"
        >
          <span class="section-number">{{ String(idx + 1).padStart(2, '0') }}</span>
          <h3 class="section-title">{{ section.title }}</h3>
          <svg
            v-if="Boolean(section.content) && collapsible"
            class="collapse-icon"
            :class="{ 'is-collapsed': collapsedSections.has(idx) }"
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </div>

        <div class="section-body" v-show="!collapsedSections.has(idx)">
          <div
            v-if="section.content"
            class="generated-content"
            v-html="renderMarkdown(section.content)"
          ></div>

          <div v-else-if="currentSectionIndex === idx + 1" class="loading-state">
            <div class="loading-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" stroke-width="4" stroke="#E5E7EB"></circle>
                <path
                  d="M12 2a10 10 0 0 1 10 10"
                  stroke-width="4"
                  stroke="#4B5563"
                  stroke-linecap="round"
                ></path>
              </svg>
            </div>
            <span class="loading-text">{{ section.title }} 생성 중...</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { renderMarkdown } from '../utils/markdown.js'

const props = defineProps({
  title: { type: String, default: '' },
  summary: { type: String, default: '' },
  reportId: { type: String, default: '' },
  reportTag: { type: String, default: '예측 보고서' },
  sections: { type: Array, default: () => [] },
  generatedSections: { type: Object, default: () => ({}) },
  currentSectionIndex: { type: Number, default: null },
  collapsible: { type: Boolean, default: true }
})

const collapsedSections = ref(new Set())

const normalizedSections = computed(() =>
  (props.sections || []).map((section, idx) => ({
    title: section?.title || `섹션 ${idx + 1}`,
    content: props.generatedSections?.[idx + 1] ?? section?.content ?? ''
  }))
)

watch(
  () => props.sections,
  () => {
    collapsedSections.value = new Set()
  },
  { deep: true }
)

function toggleSectionCollapse(idx) {
  if (!props.collapsible || !normalizedSections.value[idx]?.content) return
  const next = new Set(collapsedSections.value)
  if (next.has(idx)) next.delete(idx)
  else next.add(idx)
  collapsedSections.value = next
}
</script>

<style scoped>
.report-content-wrapper {
  max-width: 1000px;
}

.report-header-block {
  margin-bottom: 32px;
}

.report-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.report-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-secondary);
}

.report-id {
  font-size: 12px;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.main-title {
  margin: 0;
  font-size: clamp(1.8rem, 3vw, 2.6rem);
  line-height: 1.14;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
}

.sub-title {
  margin: 16px 0 0;
  font-size: 1rem;
  line-height: 1.8;
  color: var(--text-secondary);
}

.header-divider {
  margin-top: 24px;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, var(--border-strong), transparent 78%);
}

.sections-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-section-item {
  border: 1px solid var(--border-color);
  border-radius: 20px;
  background: var(--bg-secondary);
  overflow: hidden;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.report-section-item.is-active {
  border-color: rgba(99, 102, 241, 0.34);
  box-shadow: 0 14px 40px rgba(15, 23, 42, 0.08);
}

.report-section-item.is-completed {
  border-color: rgba(15, 23, 42, 0.08);
}

.report-section-item.is-pending {
  opacity: 0.8;
}

.section-header-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
}

.section-header-row.clickable {
  cursor: pointer;
}

.section-number {
  width: 34px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.section-title {
  margin: 0;
  flex: 1;
  font-size: 1.02rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
}

.collapse-icon {
  flex-shrink: 0;
  color: var(--text-secondary);
  transition: transform 0.16s ease;
}

.collapse-icon.is-collapsed {
  transform: rotate(-90deg);
}

.section-body {
  padding: 0 22px 22px;
}

.generated-content {
  color: var(--text-primary);
  line-height: 1.82;
  font-size: 0.98rem;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 0 2px;
  color: var(--text-secondary);
}

.loading-icon {
  width: 18px;
  height: 18px;
  animation: rotate 1s linear infinite;
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.generated-content :deep(.md-p) {
  margin: 0 0 1rem;
}

.generated-content :deep(.md-h2),
.generated-content :deep(.md-h3),
.generated-content :deep(.md-h4),
.generated-content :deep(.md-h5) {
  margin: 1.6rem 0 0.7rem;
  line-height: 1.4;
  color: var(--text-primary);
}

.generated-content :deep(.md-ul),
.generated-content :deep(.md-ol) {
  margin: 0.8rem 0 1rem 1.3rem;
  padding: 0;
}

.generated-content :deep(.md-li),
.generated-content :deep(.md-oli) {
  margin: 0.32rem 0;
}

.generated-content :deep(.md-quote) {
  margin: 1rem 0;
  padding: 0.9rem 1rem;
  border-left: 3px solid var(--border-strong);
  background: rgba(15, 23, 42, 0.03);
  border-radius: 0 12px 12px 0;
}

.generated-content :deep(.code-block) {
  margin: 1rem 0;
  padding: 1rem;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 14px;
  overflow-x: auto;
}

.generated-content :deep(.inline-code) {
  padding: 0.16rem 0.42rem;
  background: rgba(15, 23, 42, 0.06);
  border-radius: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.92em;
}

.generated-content :deep(.md-hr) {
  border: 0;
  height: 1px;
  background: var(--border-color);
  margin: 1.4rem 0;
}

.generated-content :deep(.md-table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0 1.25rem;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 14px;
  background: var(--bg-primary);
}

.generated-content :deep(.md-th),
.generated-content :deep(.md-td) {
  padding: 0.75rem 0.85rem;
  border-bottom: 1px solid var(--border-color);
  text-align: left;
  vertical-align: top;
}

.generated-content :deep(.md-th) {
  font-weight: 700;
  color: var(--text-primary);
  background: rgba(15, 23, 42, 0.04);
}

.generated-content :deep(.md-table tr:last-child .md-td) {
  border-bottom: 0;
}

@keyframes rotate {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .report-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-header-row {
    padding: 18px 18px;
    gap: 12px;
  }

  .section-body {
    padding: 0 18px 18px;
  }
}
</style>
