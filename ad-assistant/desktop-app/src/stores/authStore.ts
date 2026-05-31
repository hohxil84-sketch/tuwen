/**
 * Auth Store — Sprint-02 Task-05.
 *
 * Pinia store for in-memory auth/session state.
 *
 * SECURITY: Tokens are stored in JavaScript memory only.
 * Do NOT use localStorage, sessionStorage, IndexedDB, SQLite,
 * cookies, Tauri secure storage, or files for token persistence
 * in this task.
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import {
  login as cloudLogin,
  logout as cloudLogout,
  setAccessToken,
  getAccessToken,
  sanitizeApiError,
  mockAdCopy,
  type LoginData,
  type UserInfo,
  type DeviceInfo,
  type MockAdCopyRequest,
  type MockAdCopyResponse,
  type CloudAPIErrorDetail,
} from "@/services/cloudApi";

export const useAuthStore = defineStore("auth", () => {
  // ---- In-memory state (never persisted) ----
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);
  const user = ref<UserInfo | null>(null);
  const device = ref<DeviceInfo | null>(null);
  const isLoggingIn = ref(false);
  const loginError = ref<string | null>(null);

  // ---- Computed ----
  const isLoggedIn = computed(() => !!accessToken.value);
  const userName = computed(() => user.value?.account || "");

  // ---- Actions ----

  /**
   * Login with account, password, and device fingerprint.
   * Stores tokens and user/device info in memory only.
   */
  async function login(payload: {
    account: string;
    password: string;
    device_fingerprint: string;
  }): Promise<void> {
    isLoggingIn.value = true;
    loginError.value = null;

    try {
      const data: LoginData = await cloudLogin({
        account: payload.account,
        password: payload.password,
        device_fingerprint: payload.device_fingerprint,
      });

      // Store in memory
      accessToken.value = data.access_token;
      refreshToken.value = data.refresh_token;
      user.value = data.user;
      device.value = data.device;

      // Sync with cloudApi service
      setAccessToken(data.access_token);
    } catch (err: unknown) {
      const apiErr = err as CloudAPIErrorDetail;
      const msg = sanitizeApiError(apiErr);
      loginError.value = msg;
      throw apiErr;
    } finally {
      isLoggingIn.value = false;
    }
  }

  /**
   * Logout — clear in-memory state and notify cloud (best-effort).
   * Passes the refresh token so the backend can revoke the session.
   */
  async function logout(): Promise<void> {
    try {
      await cloudLogout(refreshToken.value);
    } catch {
      // Best-effort — always clear local state.
    } finally {
      clearState();
    }
  }

  /**
   * Clear all in-memory auth state without calling the cloud.
   */
  function clearState(): void {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    device.value = null;
    loginError.value = null;
    setAccessToken(null);
  }

  /**
   * Initialize token state from the cloudApi service (e.g. on app mount).
   * Currently, tokens are only in memory, so this always starts fresh.
   */
  function initFromService(): void {
    const token = getAccessToken();
    if (token) {
      accessToken.value = token;
    }
  }

  /**
   * Call the mock AI ad-copy endpoint using stored auth state.
   * Returns the data fields plus the backend-assigned request_id.
   */
  async function callMockAdCopy(
    payload: MockAdCopyRequest,
  ): Promise<MockAdCopyResponse> {
    if (!accessToken.value) {
      throw {
        code: "UNAUTHORIZED",
        message: "请先登录后再使用 AI 功能。",
      } as CloudAPIErrorDetail;
    }
    return mockAdCopy(payload);
  }

  return {
    // State
    accessToken,
    refreshToken,
    user,
    device,
    isLoggingIn,
    loginError,
    // Computed
    isLoggedIn,
    userName,
    // Actions
    login,
    logout,
    clearState,
    initFromService,
    callMockAdCopy,
  };
});
