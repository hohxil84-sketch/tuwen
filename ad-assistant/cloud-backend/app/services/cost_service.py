"""成本估算服务 — Mock 与真实 Provider 成本计算。

Sprint-02 Task-03: MockProvider 确定性 mock 计价公式。
Sprint-03 Task-02: DeepSeekProvider 官方定价计算。

不执行真实扣费，不写 credit_ledger。
"""


# ---------------------------------------------------------------------------
# 模拟单价常量（人民币，仅供 mock 测试）
# ---------------------------------------------------------------------------

# 每 1000 input units 的 mock 价格
_MOCK_PRICE_PER_1K_INPUT = 0.035  # CNY

# 每 1000 output units 的 mock 价格
_MOCK_PRICE_PER_1K_OUTPUT = 0.11  # CNY

# 每张图片的 mock 处理价格
_MOCK_PRICE_PER_IMAGE = 0.05  # CNY

# 每 GPU 秒的 mock 价格
_MOCK_PRICE_PER_GPU_SECOND = 1.2  # CNY


# ---------------------------------------------------------------------------
# DeepSeek 官方定价常量（人民币 / 每 1M tokens）
# ---------------------------------------------------------------------------
# https://api-docs.deepseek.com/quick_start/pricing

_DEEPSEEK_PRICE_PER_1M_INPUT = 1.0    # ¥1 / 1M input tokens
_DEEPSEEK_PRICE_PER_1M_OUTPUT = 2.0   # ¥2 / 1M output tokens


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------


def calculate_mock_cost(
    *,
    input_units: int,
    output_units: int,
    image_units: int,
    gpu_seconds: float,
) -> float:
    """计算 mock 估算成本（人民币）。

    所有输入必须非负。返回非负 float。
    这是确定性测试函数，**不是**真实定价逻辑。

    Raises:
        ValueError: 任一输入为负。

    Returns:
        float: 估算成本（人民币），精确到小数点后 8 位。
    """
    # 拒绝负数输入
    if input_units < 0:
        raise ValueError(f"input_units must be >= 0, got {input_units}")
    if output_units < 0:
        raise ValueError(f"output_units must be >= 0, got {output_units}")
    if image_units < 0:
        raise ValueError(f"image_units must be >= 0, got {image_units}")
    if gpu_seconds < 0:
        raise ValueError(f"gpu_seconds must be >= 0, got {gpu_seconds}")

    # 确定性 mock 计价公式
    cost = (
        (input_units / 1000.0) * _MOCK_PRICE_PER_1K_INPUT
        + (output_units / 1000.0) * _MOCK_PRICE_PER_1K_OUTPUT
        + image_units * _MOCK_PRICE_PER_IMAGE
        + gpu_seconds * _MOCK_PRICE_PER_GPU_SECOND
    )

    # 四舍五入到 8 位小数
    return round(cost, 8)


def calculate_deepseek_cost(
    *,
    input_units: int,
    output_units: int,
) -> float:
    """Calculate DeepSeek estimated cost (CNY) using official pricing.

    Pricing (as of 2026-06):
    - Input:  ¥1.00 / 1M tokens
    - Output: ¥2.00 / 1M tokens

    Only ``input_units`` and ``output_units`` are relevant; DeepSeek
    is text-only so image_units and gpu_seconds are always 0.

    Raises:
        ValueError: if either input is negative.

    Returns:
        float: estimated cost in CNY, rounded to 8 decimal places.
    """
    if input_units < 0:
        raise ValueError(f"input_units must be >= 0, got {input_units}")
    if output_units < 0:
        raise ValueError(f"output_units must be >= 0, got {output_units}")

    cost = (
        (input_units / 1_000_000.0) * _DEEPSEEK_PRICE_PER_1M_INPUT
        + (output_units / 1_000_000.0) * _DEEPSEEK_PRICE_PER_1M_OUTPUT
    )
    return round(cost, 8)
