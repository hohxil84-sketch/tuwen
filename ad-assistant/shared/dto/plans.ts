/** Shared DTO for membership plans — aligned with cloud-backend schemas/plan.py */

export interface PlanDto {
  id: string;
  name: string;
  code: string;
  price_cny: number;
  monthly_credits: number;
  features: string[];
  sort_order: number;
  status: string;
}

export interface PlanListDto {
  items: PlanDto[];
  total: number;
}
