export interface DashboardStat {
  label: string;
  value: string;
  helper: string;
  icon: string;
  tone: "blue" | "green" | "orange" | "purple";
}

export interface QuickEntry {
  title: string;
  description: string;
  icon: string;
  tone: "blue" | "orange" | "cyan" | "green" | "purple";
  route?: string;
  disabled?: boolean;
}

export interface RecentOrder {
  orderNo: string;
  customerName: string;
  projectName: string;
  status: "已完成" | "进行中" | "待确认";
  updatedAt: string;
}

export interface GeneratedImage {
  title: string;
  time: string;
  gradient: string;
}

export const MOCK_STATS: DashboardStat[] = [
  { label: "今日使用次数", value: "23 / 500", helper: "剩余额度 477", icon: "📊", tone: "blue" },
  { label: "本月订单", value: "18", helper: "较上月 +12%", icon: "📈", tone: "green" },
  { label: "生成图片", value: "56", helper: "较昨日 +8", icon: "🖼️", tone: "purple" },
  { label: "会员等级", value: "高级版", helper: "到期 2025-12-31", icon: "👑", tone: "orange" },
];

export const MOCK_QUICK_ENTRIES: QuickEntry[] = [
  { title: "AI 效果图生成", description: "输入描述，生成效果图", icon: "🎨", tone: "purple", disabled: true },
  { title: "AI 文案生成", description: "生成广告语、店名等", icon: "✍️", tone: "orange", route: "/ai-ad-copy" },
  { title: "图片改尺寸", description: "修改尺寸、DPI", icon: "📐", tone: "cyan", disabled: true },
  { title: "图片转 SVG", description: "位图转矢量图", icon: "🔷", tone: "blue", disabled: true },
  { title: "印刷检查", description: "检查文件是否适合印刷", icon: "✅", tone: "green", disabled: true },
  { title: "OCR", description: "识别图片/PDF 文字", icon: "📝", tone: "purple", route: "/ocr" },
];

export const MOCK_RECENT_ORDERS: RecentOrder[] = [
  { orderNo: "DD2024052001", customerName: "宠物医院-小李", projectName: "门头设计", status: "已完成", updatedAt: "2024-05-20 20:30" },
  { orderNo: "DD2024052002", customerName: "奶茶店-王老板", projectName: "灯箱设计", status: "进行中", updatedAt: "2024-05-20 19:15" },
  { orderNo: "DD2024052003", customerName: "超市-张姐", projectName: "宣传单页", status: "已完成", updatedAt: "2024-05-20 18:50" },
  { orderNo: "DD2024052004", customerName: "理发店-小陈", projectName: "价目表设计", status: "待确认", updatedAt: "2024-05-20 17:20" },
  { orderNo: "DD2024052005", customerName: "烧烤店-老周", projectName: "门头+灯箱", status: "进行中", updatedAt: "2024-05-20 16:10" },
];

export const MOCK_IMAGES: GeneratedImage[] = [
  { title: "宠物医院门头设计", time: "2024-05-20 20:30", gradient: "linear-gradient(135deg, #263c5a, #142438)" },
  { title: "奶茶店灯箱设计", time: "2024-05-20 19:15", gradient: "linear-gradient(135deg, #453151, #18233b)" },
  { title: "烧烤店门头设计", time: "2024-05-20 18:22", gradient: "linear-gradient(135deg, #344149, #172838)" },
  { title: "美甲店装修效果图", time: "2024-05-20 17:45", gradient: "linear-gradient(135deg, #4b4d62, #172335)" },
  { title: "超市招牌设计", time: "2024-05-20 16:50", gradient: "linear-gradient(135deg, #294064, #14263e)" },
  { title: "健身房门头设计", time: "2024-05-20 15:30", gradient: "linear-gradient(135deg, #383065, #19223b)" },
];
