/**
 * Cloud API Service — Sprint-02 Task-05.
 *
 * Typed HTTP client for the cloud backend API.
 * Only talks to the project's own cloud backend — never calls
 * third-party AI APIs (OpenAI, DeepSeek, Claude, ComfyUI, etc.).
 *
 * Tokens, passwords, device fingerprints, and request bodies containing
 * user text must never be logged by this module.
 */

// ---------------------------------------------------------------------------
// Base URL
// ---------------------------------------------------------------------------

/** Default points to local cloud backend; override via Vite env. */
const BASE_URL: string =
  import.meta.env.VITE_CLOUD_API_BASE_URL || "http://127.0.0.1:8000";

// ---------------------------------------------------------------------------
// Unified response shape (mirrors backend)
// ---------------------------------------------------------------------------

export interface CloudAPIResponse<T = unknown> {
  success: boolean;
  data: T;
  error: CloudAPIErrorDetail | null;
  request_id: string;
}

export interface CloudAPIErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface LoginRequest {
  account: string;
  password: string;
  device_fingerprint: string;
}

export interface LoginData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
  device: DeviceInfo;
}

/** 对齐 cloud-backend/app/schemas/auth.py:UserInfo */
export interface UserInfo {
  id: string;
  account: string;
  plan_code: string;
}

/** 对齐 cloud-backend/app/schemas/auth.py:DeviceInfo */
export interface DeviceInfo {
  id: string;
  status: string;
  is_new: boolean;
}

// ---------------------------------------------------------------------------
// Mock AI
// ---------------------------------------------------------------------------

export interface MockAdCopyRequest {
  product_name: string;
  selling_points: string[];
  platform: string;
  tone: string;
}

export interface MockAdCopyData {
  feature: string;
  provider: string;
  model: string;
  text: string;
  estimated_cost: number;
  credits_charged: number;
}

/** Mock ad-copy response: data fields + top-level request_id from the unified envelope. */
export interface MockAdCopyResponse extends MockAdCopyData {
  request_id: string;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/** Current access token set by authStore after login. */
let accessToken: string | null = null;

/** Set the in-memory access token for subsequent requests. */
export function setAccessToken(token: string | null): void {
  accessToken = token;
}

/** Return the current access token (may be null). */
export function getAccessToken(): string | null {
  return accessToken;
}

/**
 * Internal fetch wrapper that adds auth header when available and
 * handles the unified response envelope.
 */
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<CloudAPIResponse<T>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  let body: CloudAPIResponse<T>;
  try {
    body = (await response.json()) as CloudAPIResponse<T>;
  } catch {
    throw {
      code: "NETWORK_ERROR",
      message: `服务器响应异常 (HTTP ${response.status})`,
    } as CloudAPIErrorDetail;
  }

  if (!response.ok || !body.success) {
    const err = body.error || {
      code: "UNKNOWN_ERROR",
      message: `请求失败 (HTTP ${response.status})`,
    };
    throw err;
  }

  return body;
}

// ---------------------------------------------------------------------------
// Public API functions
// ---------------------------------------------------------------------------

/**
 * Login with account, password, and device fingerprint.
 * Returns tokens and user/device info. Caller must store tokens
 * in memory only — never persist to disk or browser storage.
 */
export async function login(
  payload: LoginRequest,
): Promise<LoginData> {
  const response = await request<LoginData>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}

/**
 * Logout from the cloud backend (best-effort).
 * Sends refresh_token in the body so the backend can revoke the session.
 */
export async function logout(refreshToken: string | null): Promise<void> {
  try {
    await request("/api/v1/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  } catch {
    // Best-effort logout — always clear local token state.
  }
}

/**
 * Call the mock AI ad-copy endpoint.
 * Returns data fields plus the backend-assigned request_id from the
 * unified response envelope.
 * Requires a valid access token set via setAccessToken().
 * Never sends provider, model, cost, credits, user_id, device_id,
 * plan, or permission decisions from the client.
 */
export async function mockAdCopy(
  payload: MockAdCopyRequest,
): Promise<MockAdCopyResponse> {
  const response = await request<MockAdCopyData>(
    "/api/v1/mock-ai/ad-copy",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
  return { ...response.data, request_id: response.request_id };
}

// ---------------------------------------------------------------------------
// Error sanitization (shared)
// ---------------------------------------------------------------------------

/**
 * Sanitize a CloudAPIErrorDetail for user-facing display.
 * Maps known error codes to Chinese user-friendly messages,
 * filters internal-looking messages (stack traces, JSON dumps, etc.),
 * and falls back to a generic message when the raw message is unsafe.
 */
export function sanitizeApiError(err: CloudAPIErrorDetail): string {
  const codeMap: Record<string, string> = {
    UNAUTHORIZED: "账号或密码错误，请重试。",
    AUTH_REQUIRED: "请先登录后再使用 AI 功能。",
    FORBIDDEN: "当前账户无权限，请联系管理员。",
    DEVICE_NOT_BOUND: "设备未绑定，请先绑定设备。",
    DEVICE_INACTIVE: "设备已被禁用。",
    PLAN_EXPIRED: "套餐已过期，请续费。",
    FEATURE_DISABLED: "当前套餐不支持此功能。",
    VALIDATION_ERROR: "输入格式不正确，请检查后重试。",
    RATE_LIMITED: "请求过于频繁，请稍后再试。",
    NETWORK_ERROR: "网络连接失败，请检查网络后重试。",
  };

  if (err.code && codeMap[err.code]) {
    return codeMap[err.code];
  }

  // Use server message only if it passes the internal-data heuristic
  if (err.message && !looksInternal(err.message)) {
    return err.message;
  }

  return "服务暂时不可用，请稍后再试。";
}

/** Heuristic: reject messages that look like stack traces or raw data dumps. */
function looksInternal(msg: string): boolean {
  if (/at\s+\S+\.(py|ts|js):\d+/.test(msg)) return true;
  if (/traceback|stack\s*trace/i.test(msg)) return true;
  if (/internal\s*server\s*error/i.test(msg)) return true;
  if (/^\s*\{.*\}\s*$/.test(msg)) return true;
  return false;
}
