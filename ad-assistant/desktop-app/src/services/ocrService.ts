/**
 * OCR Service Layer — Sprint-01 Task-04.
 *
 * Encapsulates all HTTP calls to the local FastAPI OCR service
 * running on ``http://127.0.0.1:9100``.
 */

const BASE_URL = "http://127.0.0.1:9100";

/** Default request timeout in ms (30s — OCR can be slower). */
const REQUEST_TIMEOUT_MS = 30_000;

function createTimeout(timeoutMs: number = REQUEST_TIMEOUT_MS): {
  controller: AbortController;
  timer: ReturnType<typeof setTimeout>;
} {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  return { controller, timer };
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OCRTextBlock {
  text: string;
  confidence: number;
  bbox: number[]; // [x1, y1, x2, y2]
}

export interface OCRResult {
  text: string;
  blocks: OCRTextBlock[];
  engine: string;
  duration_ms: number;
  image_hash?: string;
  history_id?: string;
}

export interface OCRErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  error: OCRErrorDetail | null;
  request_id: string;
}

export interface HealthStatus {
  status: string;
  engine: string;
  error_code?: string;
  message?: string;
}

export interface HistoryRecord {
  id: string;
  image_filename: string;
  image_hash: string;
  local_copy_path: string | null;
  text: string;
  blocks: OCRTextBlock[];
  engine: string;
  duration_ms: number;
  created_at: string;
}

export interface HistoryListData {
  items: HistoryRecord[];
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

async function request<T>(url: string, options?: RequestInit): Promise<APIResponse<T>> {
  const { controller, timer } = createTimeout();
  const mergedOptions: RequestInit = {
    ...options,
    signal: controller.signal,
  };

  let response: Response;
  try {
    response = await fetch(url, mergedOptions);
  } catch (err: unknown) {
    clearTimeout(timer);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw {
        code: "REQUEST_TIMEOUT",
        message: "OCR 请求超时，请稍后重试。",
      } as OCRErrorDetail;
    }
    throw {
      code: "NETWORK_ERROR",
      message: "本地 OCR 服务连接失败，请确认服务已启动。",
    } as OCRErrorDetail;
  }
  clearTimeout(timer);

  const body = await response.json();

  if (!response.ok || !body.success) {
    const err: OCRErrorDetail = body.error || {
      code: "NETWORK_ERROR",
      message: `Request failed with status ${response.status}`,
    };
    throw err;
  }

  return body as APIResponse<T>;
}

/**
 * Upload an image file to the local OCR service and return recognized text.
 */
export async function uploadAndOCR(imageFile: File): Promise<OCRResult> {
  const formData = new FormData();
  formData.append("image", imageFile);

  const response = await request<OCRResult>(`${BASE_URL}/local/ocr`, {
    method: "POST",
    body: formData,
  });

  return response.data;
}

/**
 * Check whether the local OCR engine is ready.
 */
export async function checkHealth(): Promise<HealthStatus> {
  const response = await request<HealthStatus>(`${BASE_URL}/local/ocr/health`);
  return response.data;
}

/**
 * Fetch paginated OCR history list (most recent first).
 */
export async function getHistory(
  limit: number = 50,
  offset: number = 0,
): Promise<HistoryListData> {
  const response = await request<HistoryListData>(
    `${BASE_URL}/local/ocr/history?limit=${limit}&offset=${offset}`,
  );
  return response.data;
}

/**
 * Fetch a single OCR history record by ID.
 */
export async function getHistoryDetail(id: string): Promise<HistoryRecord> {
  const response = await request<HistoryRecord>(
    `${BASE_URL}/local/ocr/history/${encodeURIComponent(id)}`,
  );
  return response.data;
}
