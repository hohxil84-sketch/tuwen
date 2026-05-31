<!-- Sprint-01 Task-04 + Sprint-02 Task-05: OCR workspace page + Mock AI panel -->
<template>
  <div class="ocr-page">
    <h2>OCR 文字识别</h2>

    <!-- Status bar -->
    <div class="status-bar">
      <span :class="['status-dot', engineReady ? 'ready' : 'pending']"></span>
      <span>{{ engineReady ? '引擎就绪' : '引擎未就绪' }}</span>
      <span v-if="auth.isLoggedIn" class="auth-badge">已登录 · {{ auth.userName }}</span>
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

    <!-- ============================================================ -->
    <!-- Mock AI Ad-Copy Panel  (Sprint-02 Task-05)                    -->
    <!-- ============================================================ -->
    <div v-if="auth.isLoggedIn" class="mock-ai-panel">
      <h3>
        <span class="mock-badge">Mock / 测试</span>
        AI 广告文案生成
      </h3>
      <p class="mock-notice">
        ⚠ 当前为 Mock 测试接口，不产生真实 AI 调用与扣费。服务端将返回固定测试文本。
      </p>

      <form class="mock-ai-form" @submit.prevent="handleMockAdCopy">
        <div class="form-group">
          <label for="product-name">产品名称</label>
          <input
            id="product-name"
            v-model.trim="mockForm.product_name"
            type="text"
            placeholder="例如：夏季冰咖啡"
            :disabled="mockSubmitting"
          />
        </div>

        <div class="form-group">
          <label for="selling-points">卖点（一行一个）</label>
          <textarea
            id="selling-points"
            v-model="mockForm.selling_points_raw"
            rows="3"
            placeholder="纯手工制作&#10;买一送一&#10;限时特惠"
            :disabled="mockSubmitting"
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="platform">投放平台</label>
            <select
              id="platform"
              v-model="mockForm.platform"
              :disabled="mockSubmitting"
            >
              <option value="douyin">抖音</option>
              <option value="xiaohongshu">小红书</option>
              <option value="wechat">微信朋友圈</option>
              <option value="kuaishou">快手</option>
            </select>
          </div>

          <div class="form-group">
            <label for="tone">文案风格</label>
            <select
              id="tone"
              v-model="mockForm.tone"
              :disabled="mockSubmitting"
            >
              <option value="direct">直白促销</option>
              <option value="story">故事叙事</option>
              <option value="trendy">潮流种草</option>
              <option value="professional">专业背书</option>
            </select>
          </div>
        </div>

        <!-- Mock AI error -->
        <div v-if="mockError" class="error-banner">
          <p><strong>生成失败：</strong>{{ mockError }}</p>
          <button class="btn btn-sm btn-secondary" @click="mockError = null">关闭</button>
        </div>

        <button
          type="submit"
          class="btn btn-primary"
          :disabled="mockSubmitting || !mockFormValid"
        >
          <span v-if="mockSubmitting" class="spinner"></span>
          {{ mockSubmitting ? '生成中...' : '生成 Mock 文案' }}
        </button>
      </form>

      <!-- Mock AI result -->
      <div v-if="mockResult" class="mock-result-area">
        <div class="mock-result-header">
          <span class="mock-badge">Mock 测试输出</span>
        </div>

        <div class="mock-result-meta">
          <span>Provider：{{ mockResult.provider }}</span>
          <span>Model：{{ mockResult.model }}</span>
          <span>扣点：{{ mockResult.credits_charged }}</span>
          <span>Request ID：{{ mockResult.request_id }}</span>
        </div>

        <div class="mock-result-text">
          <h4>生成文案</h4>
          <pre class="full-text">{{ mockResult.text }}</pre>
        </div>

        <button class="btn btn-sm btn-secondary" @click="clearMockResult">清除结果</button>
      </div>
    </div>

    <!-- Mock AI login prompt (when not logged in) -->
    <div v-else class="mock-ai-login-prompt">
      <p>💡 登录后可使用 AI 广告文案生成（当前为 Mock 测试接口）</p>
      <router-link to="/login" class="btn btn-secondary">去登录</router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import {
  checkHealth,
  uploadAndOCR,
  type OCRErrorDetail,
  type OCRResult,
  type OCRTextBlock,
} from "@/services/ocrService";
import { useAuthStore } from "@/stores/authStore";
import { sanitizeApiError, type MockAdCopyResponse, type CloudAPIErrorDetail } from "@/services/cloudApi";

// ---- Auth ----
const auth = useAuthStore();

// ---- OCR reactive state ----
const fileInput = ref<HTMLInputElement>();
const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const isDragging = ref(false);
const isProcessing = ref(false);
const engineReady = ref(false);
const result = ref<OCRResult | null>(null);
const errorMessage = ref<string | null>(null);

const allowedExtensions = ".png,.jpg,.jpeg,.bmp,.tiff,.webp";

// ---- OCR computed ----
const sortedBlocks = computed<OCRTextBlock[]>(() => {
  if (!result.value) return [];
  return [...result.value.blocks].sort((a, b) => b.confidence - a.confidence);
});

// ---- OCR lifecycle ----
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

// ---- OCR methods ----
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
  clearMockResult();
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

// ---- Mock AI ad-copy state ----
const mockSubmitting = ref(false);
const mockError = ref<string | null>(null);
const mockResult = ref<MockAdCopyResponse | null>(null);

const mockForm = reactive({
  product_name: "",
  selling_points_raw: "",
  platform: "douyin",
  tone: "direct",
});

const mockFormValid = computed(() => mockForm.product_name.length > 0);

// ---- Mock AI methods ----

/** Build selling_points array from raw text input. */
function buildSellingPoints(): string[] {
  return mockForm.selling_points_raw
    .split("\n")
    .map((s: string) => s.trim())
    .filter((s: string) => s.length > 0);
}

async function handleMockAdCopy(): Promise<void> {
  if (!mockFormValid.value || mockSubmitting.value) return;

  mockSubmitting.value = true;
  mockError.value = null;
  mockResult.value = null;

  try {
    const data = await auth.callMockAdCopy({
      product_name: mockForm.product_name,
      selling_points: buildSellingPoints(),
      platform: mockForm.platform,
      tone: mockForm.tone,
    });

    mockResult.value = data;
  } catch (err: unknown) {
    const apiErr = err as CloudAPIErrorDetail;
    mockError.value = sanitizeApiError(apiErr);
  } finally {
    mockSubmitting.value = false;
  }
}

function clearMockResult(): void {
  mockResult.value = null;
  mockError.value = null;
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

.auth-badge {
  margin-left: auto;
  color: #3b82f6;
  font-weight: 500;
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
  display: inline-flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
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

/* ============================================================ */
/* Mock AI panel styles  (Sprint-02 Task-05)                     */
/* ============================================================ */
.mock-ai-panel {
  border: 2px solid #fbbf24;
  border-radius: 8px;
  padding: 24px;
  margin-top: 32px;
  background-color: #fffbeb;
}

.mock-ai-panel h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  margin-bottom: 12px;
}

.mock-badge {
  display: inline-block;
  background-color: #f59e0b;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
}

.mock-notice {
  font-size: 13px;
  color: #92400e;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #fef3c7;
  border-radius: 4px;
}

/* Mock AI form */
.mock-ai-form .form-group {
  margin-bottom: 14px;
}

.mock-ai-form label {
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.mock-ai-form input,
.mock-ai-form textarea,
.mock-ai-form select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  box-sizing: border-box;
  font-family: inherit;
}

.mock-ai-form input:focus,
.mock-ai-form textarea:focus,
.mock-ai-form select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.mock-ai-form input:disabled,
.mock-ai-form textarea:disabled,
.mock-ai-form select:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .form-group {
  flex: 1;
}

/* Mock AI result */
.mock-result-area {
  margin-top: 20px;
  border: 1px solid #fbbf24;
  border-radius: 6px;
  padding: 16px;
  background-color: #fff;
}

.mock-result-header {
  margin-bottom: 12px;
}

.mock-result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: #666;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f3f4f6;
}

.mock-result-text h4 {
  font-size: 13px;
  margin-bottom: 6px;
}

/* Mock AI login prompt */
.mock-ai-login-prompt {
  text-align: center;
  padding: 32px;
  margin-top: 32px;
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  background-color: #f9fafb;
}

.mock-ai-login-prompt p {
  font-size: 14px;
  color: #666;
  margin-bottom: 14px;
}
</style>
