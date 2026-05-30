<!-- Sprint-01 Task-04: OCR workspace page -->
<template>
  <div class="ocr-page">
    <h2>OCR 文字识别</h2>

    <!-- Status bar -->
    <div class="status-bar">
      <span :class="['status-dot', engineReady ? 'ready' : 'pending']"></span>
      <span>{{ engineReady ? '引擎就绪' : '引擎未就绪' }}</span>
    </div>

    <!-- Upload area: click + drag-drop -->
    <div
      :class="['upload-area', { 'drag-over': isDragging }]"
      @click="triggerFileInput"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="allowedExtensions"
        style="display: none"
        @change="onFileSelected"
      />

      <template v-if="!previewUrl">
        <p class="upload-hint">点击选择图片，或拖拽图片到此区域</p>
        <p class="upload-formats">支持格式：PNG / JPG / BMP / TIFF / WebP（最大 50MB）</p>
      </template>

      <template v-else>
        <div class="preview-container">
          <img :src="previewUrl" alt="预览图片" class="image-preview" />
          <button class="btn btn-sm btn-secondary" @click.stop="clearImage">重新选择</button>
        </div>
      </template>
    </div>

    <!-- OCR trigger -->
    <div class="actions">
      <button
        class="btn btn-primary"
        :disabled="!selectedFile || isProcessing"
        @click="runOCR"
      >
        <span v-if="isProcessing" class="spinner"></span>
        {{ isProcessing ? '识别中...' : '开始 OCR 识别' }}
      </button>
    </div>

    <!-- Error display -->
    <div v-if="errorMessage" class="error-banner">
      <p><strong>识别失败：</strong>{{ errorMessage }}</p>
      <button class="btn btn-sm btn-secondary" @click="clearError">关闭</button>
    </div>

    <!-- Result display -->
    <div v-if="result" class="result-area">
      <h3>识别结果</h3>
      <div class="result-meta">
        <span>引擎：{{ result.engine }}</span>
        <span>耗时：{{ result.duration_ms }}ms</span>
      </div>

      <div class="result-section">
        <h4>全文</h4>
        <pre class="full-text">{{ result.text || '<无识别文本>' }}</pre>
      </div>

      <div v-if="result.blocks.length > 0" class="result-section">
        <h4>文本块（{{ result.blocks.length }} 个）</h4>
        <ul class="block-list">
          <li v-for="(block, idx) in sortedBlocks" :key="idx" class="block-item">
            <span class="block-confidence">{{ (block.confidence * 100).toFixed(1) }}%</span>
            <span class="block-text">{{ block.text }}</span>
            <span class="block-bbox">
              [{{ block.bbox[0] }}, {{ block.bbox[1] }}, {{ block.bbox[2] }}, {{ block.bbox[3] }}]
            </span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  checkHealth,
  uploadAndOCR,
  type OCRErrorDetail,
  type OCRResult,
  type OCRTextBlock,
} from "@/services/ocrService";

// ---- Reactive state ----
const fileInput = ref<HTMLInputElement>();
const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const isDragging = ref(false);
const isProcessing = ref(false);
const engineReady = ref(false);
const result = ref<OCRResult | null>(null);
const errorMessage = ref<string | null>(null);

const allowedExtensions = ".png,.jpg,.jpeg,.bmp,.tiff,.webp";

// ---- Computed ----
const sortedBlocks = computed<OCRTextBlock[]>(() => {
  if (!result.value) return [];
  return [...result.value.blocks].sort((a, b) => b.confidence - a.confidence);
});

// ---- Lifecycle ----
onMounted(async () => {
  try {
    const health = await checkHealth();
    engineReady.value = health.status === "ok";
    if (!engineReady.value) {
      errorMessage.value = health.message || "OCR 引擎未就绪，请检查本地服务是否已启动。";
    }
  } catch {
    engineReady.value = false;
    errorMessage.value = "无法连接到本地 OCR 服务（127.0.0.1:9100），请确认服务已启动。";
  }
});

// ---- Methods ----
function triggerFileInput() {
  if (isProcessing.value) return;
  fileInput.value?.click();
}

function validateAndSetFile(file: File) {
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  const allowed = allowedExtensions.split(",");
  if (!allowed.includes(ext)) {
    errorMessage.value = `不支持的文件格式 "${ext}"。支持：PNG / JPG / BMP / TIFF / WebP`;
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    errorMessage.value = `文件过大（${(file.size / 1024 / 1024).toFixed(1)} MB），最大允许 50 MB。`;
    return;
  }

  selectedFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
  result.value = null;
  errorMessage.value = null;
}

function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files[0]) {
    validateAndSetFile(input.files[0]);
  }
}

function onDrop(event: DragEvent) {
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  if (files && files[0]) {
    validateAndSetFile(files[0]);
  }
}

function clearImage() {
  selectedFile.value = null;
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }
  result.value = null;
  errorMessage.value = null;
}

function clearError() {
  errorMessage.value = null;
}

async function runOCR() {
  if (!selectedFile.value || isProcessing.value) return;

  isProcessing.value = true;
  errorMessage.value = null;
  result.value = null;

  try {
    result.value = await uploadAndOCR(selectedFile.value);
  } catch (err: unknown) {
    const ocrErr = err as OCRErrorDetail;
    errorMessage.value = ocrErr?.message || "OCR 请求失败，请检查本地服务是否正常运行。";
  } finally {
    isProcessing.value = false;
  }
}
</script>

<style scoped>
.ocr-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

h2 {
  margin-bottom: 16px;
}

/* Status bar */
.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.status-dot.ready {
  background-color: #22c55e;
}
.status-dot.pending {
  background-color: #f59e0b;
}

/* Upload area */
.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
  margin-bottom: 16px;
}
.upload-area:hover,
.upload-area.drag-over {
  border-color: #3b82f6;
  background-color: #f0f5ff;
}
.upload-hint {
  font-size: 16px;
  color: #666;
  margin-bottom: 8px;
}
.upload-formats {
  font-size: 12px;
  color: #999;
}

/* Preview */
.preview-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.image-preview {
  max-width: 100%;
  max-height: 300px;
  object-fit: contain;
  border-radius: 4px;
}

/* Actions */
.actions {
  margin-bottom: 16px;
}

/* Buttons */
.btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary {
  background-color: #3b82f6;
  color: #fff;
  padding: 10px 28px;
  font-size: 16px;
}
.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}
.btn-secondary {
  background-color: #e5e7eb;
  color: #333;
}
.btn-secondary:hover {
  background-color: #d1d5db;
}
.btn-sm {
  padding: 4px 12px;
  font-size: 12px;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 6px;
  vertical-align: middle;
}
@keyframes spin {
  to { transform: rotate(360deg); }
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

/* Result area */
.result-area {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  margin-top: 16px;
}
.result-meta {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: #666;
  margin-bottom: 16px;
}

.result-section {
  margin-bottom: 16px;
}
.result-section h4 {
  font-size: 14px;
  margin-bottom: 8px;
  color: #333;
}

.full-text {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  padding: 12px;
  white-space: pre-wrap;
  font-size: 14px;
  max-height: 240px;
  overflow-y: auto;
  user-select: text;
}

/* Block list */
.block-list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 360px;
  overflow-y: auto;
}
.block-item {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 13px;
}
.block-confidence {
  flex-shrink: 0;
  min-width: 52px;
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
