import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI 图文广告助手",
  description: "面向图文广告行业的 AI 工作台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
