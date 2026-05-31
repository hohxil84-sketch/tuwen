<!-- Sprint-02 Task-05: Login page with cloud auth -->
<template>
  <div class="login-page">
    <h1>AI 图文广告助手</h1>
    <p class="subtitle">登录以使用云端 AI 功能</p>

    <!-- Login form -->
    <form v-if="!auth.isLoggedIn" class="login-form" @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="account">账号</label>
        <input
          id="account"
          v-model.trim="form.account"
          type="text"
          placeholder="请输入账号"
          :disabled="auth.isLoggingIn"
          autocomplete="username"
        />
      </div>

      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          placeholder="请输入密码"
          :disabled="auth.isLoggingIn"
          autocomplete="current-password"
        />
      </div>

      <div class="form-group">
        <label for="fingerprint">设备指纹</label>
        <input
          id="fingerprint"
          v-model.trim="form.device_fingerprint"
          type="text"
          placeholder="请输入设备指纹"
          :disabled="auth.isLoggingIn"
        />
      </div>

      <!-- Error display -->
      <div v-if="auth.loginError" class="error-banner">
        <p>{{ auth.loginError }}</p>
      </div>

      <button
        type="submit"
        class="btn btn-primary btn-block"
        :disabled="auth.isLoggingIn || !isFormValid"
      >
        <span v-if="auth.isLoggingIn" class="spinner"></span>
        {{ auth.isLoggingIn ? '登录中...' : '登录' }}
      </button>
    </form>

    <!-- Logged-in state -->
    <div v-else class="logged-in">
      <div class="status-card">
        <div class="status-dot ready"></div>
        <span>已登录</span>
      </div>
      <p class="user-info">
        账号：<strong>{{ auth.userName }}</strong>
      </p>
      <p v-if="auth.device" class="device-info">
        设备 ID：{{ auth.device.id }}（{{ auth.device.status }}<span v-if="auth.device.is_new"> · 新设备</span>）
      </p>

      <div class="actions">
        <router-link to="/ocr" class="btn btn-primary">进入工作台</router-link>
        <button class="btn btn-secondary" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();
const router = useRouter();

// ---- Form state ----
const form = reactive({
  account: "",
  password: "",
  device_fingerprint: "",
});

// ---- Computed ----
const isFormValid = computed(
  () => form.account.length > 0 && form.password.length > 0 && form.device_fingerprint.length > 0,
);

// ---- Methods ----
async function handleLogin(): Promise<void> {
  if (!isFormValid.value) return;
  try {
    await auth.login({
      account: form.account,
      password: form.password,
      device_fingerprint: form.device_fingerprint,
    });
    // Navigate to OCR workspace after successful login
    router.push("/ocr");
  } catch {
    // Error is already stored in auth.loginError
  }
}

async function handleLogout(): Promise<void> {
  await auth.logout();
}
</script>

<style scoped>
.login-page {
  max-width: 400px;
  margin: 64px auto 0;
  padding: 32px;
  text-align: center;
}

h1 {
  margin-bottom: 8px;
  font-size: 24px;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin-bottom: 32px;
}

/* Form */
.login-form {
  text-align: left;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.form-group input:disabled {
  background-color: #f9fafb;
  cursor: not-allowed;
}

/* Error */
.error-banner {
  background-color: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 16px;
}

.error-banner p {
  margin: 0;
  color: #b91c1c;
  font-size: 13px;
}

/* Buttons */
.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.2s, background-color 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
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

.btn-secondary:hover {
  background-color: #d1d5db;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Logged-in state */
.logged-in {
  text-align: center;
}

.status-card {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background-color: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 6px;
  padding: 8px 20px;
  font-size: 14px;
  margin-bottom: 16px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.ready {
  background-color: #22c55e;
}

.user-info,
.device-info {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}
</style>
