import React from 'react';
import GraphViewer from '@/components/GraphViewer';

export default function GraphPage() {
  return (
    // 强制 main 容器没有任何 padding 或 margin，并且占满全屏
    <main className="w-screen h-screen overflow-hidden bg-slate-50">
      <GraphViewer />
    </main>
  );
}