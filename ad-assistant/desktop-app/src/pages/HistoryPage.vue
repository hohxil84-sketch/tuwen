<!-- Sprint-01 Task-04: OCR history list page -->
<template>
  <div class="history-page">
    <h2>识别历史</h2>

    <!-- Error banner -->
    <div v-if="errorMessage" class="error-banner">
      <p>{{ errorMessage }}</p>
      <button class="btn btn-sm btn-secondary" @click="errorMessage = null">关闭</button>
    </div>

    <!-- Loading state -->
    <div v-if="isLoading && items.length === 0" class="loading">
      加载中...
    </div>

    <!-- Empty state -->
    <div v-else-if="!isLoading && items.length === 0" class="empty-state">
      <p>暂无识别记录</p>
      <router-link to="/ocr" class="btn btn-primary">去识别</router-link>
    </div>

    <!-- History list -->
    <template v-else>
      <ul class="history-list">
        <li
          v-for="item in items"
          :key="item.id"
          :class="['history-card', { 'is-selected': selectedId === item.id }]"
          @click="selectItem(item)"
        >
          <div class="card-header">
            <span class="card-filename">{{ item.image_filename }}</span>
            <span class="card-date">{{ formatDate(item.created_at) }}</span>
          </div>
          <div class="card-preview">{{ truncateText(item.text, 100) }}</div>
          <div class="card-meta">
            <span>引擎：{{ item.engine }}</span>
            <span>耗时：{{ item.duration_ms }}ms</span>
          </div>
        </li>
      </ul>

      <!-- Pagination -->
      <div class="pagination">
        <button
          class="btn btn-sm btn-secondary"
          :disabled="currentOffset === 0"
          @click="goToPage(0)"
        >
          首页
        </button>
        <button
          class="btn btn-sm btn-secondary"
          :disabled="currentOffset === 0"
          @click="goToPage(Math.max(0, currentOffset - pageSize))"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ currentOffset / pageSize + 1 }} 页
        </span>
        <button
          class="btn btn-sm btn-secondary"
          :disabled="items.length < pageSize"
          @click="goToPage(currentOffset + pageSize)"
        >
          下一页
        </button>
      </div>
    </template>

    <!-- Detail modal -->
    <div v-if="selectedRecord" class="modal-overlay" @click.self="selectedRecord = null; selectedId = null">
      <div class="modal-content">
        <h3>OCR 详情</h3>
        <div class="detail-meta">
          <p><strong>文件名：</strong>{{ selectedRecord.image_filename }}</p>
          <p><strong>识别时间：</strong>{{ formatDate(selectedRecord.created_at) }}</p>
          <p><strong>引擎：</strong>{{ selectedRecord.engine }}</p>
          <p><strong>耗时：</strong>{{ selectedRecord.duration_ms }}ms</p>
          <p><strong>Hash：</strong>{{ selectedRecord.image_hash }}</p>
        </div>

        <div class="detail-section">
          <h4>全文</h4>
          <pre class="full-text">{{ selectedRecord.text || '<无识别文本>' }}</pre>
        </div>

        <div v-if="selectedRecord.blocks && selectedRecord.blocks.length > 0" class="detail-section">
          <h4>文本块（{{ selectedRecord.blocks.length }} 个）</h4>
          <ul class="block-list">
            <li v-for="(block, idx) in selectedRecord.blocks" :key="idx" class="block-item">
              <span class="block-confidence">{{ (block.confidence * 100).toFixed(1) }}%</span>
              <span class="block-text">{{ block.text }}</span>
              <span class="block-bbox">
                [{{ block.bbox[0] }}, {{ block.bbox[1] }}, {{ block.bbox[2] }}, {{ block.bbox[3] }}]
              </span>
            </li>
          </ul>
        </div>

        <button class="btn btn-primary" @click="selectedRecord = null; selectedId = null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  getHistory,
  getHistoryDetail,
  type HistoryRecord,
  type OCRErrorDetail,
} from "@/services/ocrService";

// ---- Constants ----
const pageSize = 50;

// ---- Reactive state ----
const items = ref<HistoryRecord[]>([]);
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const currentOffset = ref(0);

const selectedId = ref<string | null>(null);
const selectedRecord = ref<HistoryRecord | null>(null);

// ---- Lifecycle ----
onMounted(() => {
  loadPage(0);
});

// ---- Methods ----
async function loadPage(offset: number) {
  isLoading.value = true;
  errorMessage.value = null;
  try {
    const data = await getHistory(pageSize, offset);
    items.value = data.items;
    currentOffset.value = offset;
  } catch (err: unknown) {
    const ocrErr = err as OCRErrorDetail;
    errorMessage.value = ocrErr?.message || "加载历史记录失败，请检查本地服务是否正常运行。";
    items.value = [];
  } finally {
    isLoading.value = false;
  }
}

function goToPage(offset: number) {
  loadPage(offset);
}

async function selectItem(item: HistoryRecord) {
  selectedId.value = item.id;
  try {
    selectedRecord.value = await getHistoryDetail(item.id);
  } catch {
    // Fallback: use the list item data
    selectedRecord.value = item;
  }
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString("zh-CN");
  } catch {
    return iso;
  }
}

function truncateText(text: string, maxLen: number): string {
  if (!text) return "<无文本>";
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + "...";
}
</script>

<style scoped>
.history-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

h2 {
  margin-bottom: 16px;
}

/* Loading & empty */
.loading,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}
.empty-state p {
  margin-bottom: 16px;
}

/* Error */
.error-banner {
  background-color: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.error-banner p {
  margin: 0;
  color: #b91c1c;
}

/* History list */
.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.history-card {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.history-card:hover,
.history-card.is-selected {
  border-color: #3b82f6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 6px;
}
.card-filename {
  font-weight: 600;
  font-size: 14px;
}
.card-date {
  font-size: 12px;
  color: #999;
}
.card-preview {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}
.page-info {
  font-size: 13px;
  color: #666;
}

/* Buttons */
.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary {
  background-color: #3b82f6;
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}
.btn-secondary {
  background-color: #e5e7eb;
  color: #333;
}
.btn-secondary:hover:not(:disabled) {
  background-color: #d1d5db;
}
.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal-content {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  max-width: 640px;
  max-height: 80vh;
  overflow-y: auto;
  width: 90%;
}

.detail-meta {
  font-size: 13px;
  margin-bottom: 16px;
}
.detail-meta p {
  margin: 4px 0;
}

.detail-section {
  margin-bottom: 16px;
}
.detail-section h4 {
  font-size: 14px;
  margin-bottom: 8px;
}

.full-text {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 12px;
  white-space: pre-wrap;
  font-size: 13px;
  max-height: 200px;
  overflow-y: auto;
  user-select: text;
}

.block-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 320px;
  overflow-y: auto;
}
.block-item {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}
.block-confidence {
  flex-shrink: 0;
  min-width: 50px;
  font-weight: 600;
  color: #3b82f6;
}
.block-text {
  flex: 1;
}
.block-bbox {
  flex-shrink: 0;
  font-size: 11px;
  color: #999;
  font-family: monospace;
}
</style>
