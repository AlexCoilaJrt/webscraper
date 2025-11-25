declare module 'echarts-for-react' {
  import * as React from 'react';
  interface ReactEChartsProps {
    option: any;
    style?: React.CSSProperties;
    className?: string;
    notMerge?: boolean;
    lazyUpdate?: boolean;
    theme?: string | object;
    onChartReady?: (chart: any) => void;
  }
  const ReactECharts: React.FC<ReactEChartsProps>;
  export default ReactECharts;
}







