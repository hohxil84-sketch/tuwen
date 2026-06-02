<template>
  <div class="ad-copy-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h2 class="page-title">AI 广告文案生成</h2>
      <p class="page-desc">输入产品信息，AI 帮您生成广告文案</p>
    </header>

    <!-- Not logged in -->
    <div v-if="!auth.isLoggedIn" class="empty-state">
      <p>请先登录后再使用 AI 功能。</p>
      <button class="btn-primary" @click="goLogin">去登录</button>
    </div>

    <!-- Form -->
    <form v-else class="ad-form" @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="productName">产品名称 <span class="required">*</span></label>
        <input
          id="productName"
          v-model="form.product_name"
          type="text"
          placeholder="例如：招牌奶茶"
          required
          :disabled="submitting"
        />
      </div>

      <div class="form-group">
        <label for="sellingPoints">卖点 <span class="required">*</span></label>
        <input
          id="sellingPoints"
          v-model="sellingPointsText"
          type="text"
          placeholder="多个卖点用中文逗号分隔，例如：口感醇厚，价格实惠"
          required
          :disabled="submitting"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="platform">平台</label>
          <select id="platform" v-model="form.platform" :disabled="submitting">
            <option value="朋友圈">朋友圈</option>
            <option value="抖音">抖音</option>
            <option value="小红书">小红书</option>
            <option value="公众号">公众号</option>
            <option value="宣传单">宣传单</option>
          </select>
        </div>

        <div class="form-group">
          <label for="tone">风格</label>
          <select id="tone" v-model="form.tone" :disabled="submitting">
            <option value="活泼">活泼</option>
            <option value="专业">专业</option>
            <option value="温馨">温馨</option>
            <option value="幽默">幽默</option>
            <option value="高端">高端</option>
          </select>
        </div>
      </div>

      <div v-if="errorMsg" class="error-msg">
        <span>{{ errorMsg }}</span>
        <button v-if="insufficientBalance" class="recharge-btn" @click="goMembership">去充值 →</button>
        <span v-if="errorRequestId" class="error-request-id">request_id: {{ errorRequestId }}</span>
      </div>

      <button type="submit" class="btn-generate" :disabled="submitting || !formValid">
        {{ submitting ? "生成中..." : "✨ 生成文案" }}
      </button>
    </form>

    <!-- Result -->
    <div v-if="result" class="result-card">
      <div class="result-header">
        <h3>生成结果</h3>
        <span class="result-meta">
          {{ result.provider }} / {{ result.model }} ·
          消耗 {{ result.credits_charged }} 积分
        </span>
      </div>
      <div class="result-text">{{ result.text }}</div>
      <div class="result-meta-bottom">
        request_id: {{ result.request_id }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/authStore";
import { sanitizeApiError, type MockAdCopyRequest, type MockAdCopyResponse, type CloudAPIErrorDetail } from "@/services/cloudApi";

const router = useRouter();
const auth = useAuthStore();

const form = ref<MockAdCopyRequest>({
  product_name: "",
  selling_points: [],
  platform: "朋友圈",
  tone: "活泼",
});
const sellingPointsText = ref("");
const submitting = ref(false);
const errorMsg = ref<string | null>(null);
const insufficientBalance = ref(false);
const errorRequestId = ref<string | null>(null);
const result = ref<MockAdCopyResponse | null>(null);

const formValid = computed(() => {
  return form.value.product_name.trim().length > 0 && sellingPointsText.value.trim().length > 0;
});

function goBack(): void {
  router.push("/");
}

function goLogin(): void {
  router.push("/login");
}

function goMembership(): void {
  router.push("/membership");
}

async function handleSubmit(): Promise<void> {
  errorMsg.value = null;
  insufficientBalance.value = false;
  errorRequestId.value = null;
  result.value = null;

  // Parse selling points from comma-separated text
  const points = sellingPointsText.value
    .split(/[，,、]/)
    .map((s) => s.trim())
    .filter(Boolean);

  if (points.length === 0) {
    errorMsg.value = "请至少输入一个卖点。";
    return;
  }

  form.value.selling_points = points;
  submitting.value = true;

  try {
    result.value = await auth.callMockAdCopy(form.value);
  } catch (err: unknown) {
    const apiErr = err as CloudAPIErrorDetail;
    errorMsg.value = sanitizeApiError(apiErr);
    if (apiErr.code === "INSUFFICIENT_BALANCE") {
      insufficientBalance.value = true;
      errorRequestId.value = apiErr.request_id || null;
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.ad-copy-page {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 24px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  margin-bottom: 8px;
}

.back-btn {
  display: inline-block;
  margin-bottom: 12px;
  padding: 4px 0;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
}

.back-btn:hover {
  color: var(--blue);
}

.page-title {
  margin-bottom: 6px;
  color: var(--text-main);
  font-size: 22px;
  font-weight: 700;
}

.page-desc {
  color: var(--text-muted);
  font-size: 13px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 60px 20px;
  color: var(--text-muted);
  text-align: center;
}

.btn-primary {
  padding: 10px 28px;
  background: var(--blue);
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.ad-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.form-group label {
  color: var(--text-main);
  font-size: 13px;
  font-weight: 500;
}

.required {
  color: #e04f5f;
}

.form-group input,
.form-group select {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-main);
  font-size: 14px;
  outline: none;
}

.form-group input:focus,
.form-group select:focus {
  border-color: rgba(47, 111, 237, 0.4);
}

.form-group select {
  cursor: pointer;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.error-msg {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(224, 79, 95, 0.1);
  border: 1px solid rgba(224, 79, 95, 0.2);
  border-radius: 6px;
  color: #e04f5f;
  font-size: 13px;
}

.recharge-btn {
  align-self: flex-start;
  padding: 6px 16px;
  background: rgba(47, 111, 237, 0.15);
  border: 1px solid rgba(47, 111, 237, 0.3);
  border-radius: 5px;
  color: var(--blue);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.15s;
}

.recharge-btn:hover {
  background: rgba(47, 111, 237, 0.25);
}

.error-request-id {
  color: var(--text-muted);
  font-family: "Consolas", "Menlo", monospace;
  font-size: 11px;
  word-break: break-all;
}

.btn-generate {
  align-self: flex-start;
  padding: 10px 32px;
  background: linear-gradient(135deg, #2f6fed, #1a5be0);
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: opacity 0.18s;
}

.btn-generate:hover:not(:disabled) {
  opacity: 0.88;
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-card {
  padding: 24px;
  background: var(--card-bg);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
}

.result-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}

.result-header h3 {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 600;
}

.result-meta {
  color: var(--text-soft);
  font-size: 12px;
}

.result-text {
  padding: 18px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.result-meta-bottom {
  margin-top: 12px;
  color: var(--text-soft);
  font-family: "Consolas", "Menlo", monospace;
  font-size: 11px;
}
</style>
