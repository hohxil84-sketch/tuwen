/** Shared DTO for recharge/orders — aligned with cloud-backend schemas/recharge.py */

export interface RechargeRequestDto {
  plan_code?: string | null;
  amount_cny?: number | null;
}

export interface RechargeResponseDto {
  order_id: string;
  plan_code: string | null;
  amount_cny: number;
  credits: number;
  new_balance: number;
  status: string;
}

export interface OrderItemDto {
  id: string;
  plan_code: string | null;
  amount_cny: number;
  credits: number;
  payment_method: string;
  status: string;
  description: string | null;
  created_at: string | null;
}

export interface OrderListDto {
  items: OrderItemDto[];
  total: number;
  limit: number;
  offset: number;
}
