/**
 * Mock AI API — shared TypeScript DTOs
 * Sprint-02 Task-08: first real DTO in shared/dto/
 *
 * Mirrors the contract defined in shared/openapi/mock-ai.yaml and the
 * backend Pydantic schemas in cloud-backend/app/schemas/mock_ai.py.
 *
 * All API responses use the unified envelope APIResponse<T>.
 */

// ---------------------------------------------------------------------------
// Unified response envelope
// ---------------------------------------------------------------------------

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

/**
 * Generic unified API response.
 *
 * Successful response:  success=true,  data=T,        error=null
 * Error response:       success=false, data=null,     error=ErrorDetail
 */
export interface APIResponse<T = unknown> {
  success: boolean;
  data: T | null;
  error: ErrorDetail | null;
  request_id: string | null;
}

// ---------------------------------------------------------------------------
// POST /api/v1/mock-ai/ad-copy
// ---------------------------------------------------------------------------

export interface MockAdCopyRequest {
  product_name: string;
  selling_points?: string[];
  platform?: string; // default: "douyin"
  tone?: string; // default: "direct"
}

export interface MockAdCopyData {
  feature: string; // "mock_ad_copy"
  provider: string; // "mock"
  model: string; // "mock-text-v1"
  text: string;
  estimated_cost: number;
  credits_charged: number; // always 0 in mock
}

/** Typed alias for the ad-copy endpoint response. */
export type MockAdCopyResponse = APIResponse<MockAdCopyData>;
