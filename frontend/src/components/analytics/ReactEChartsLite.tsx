import React, { useEffect, useRef, useState } from 'react';

type Props = {
  option: any;
  style?: React.CSSProperties;
  className?: string;
};

const ReactEChartsLite: React.FC<Props> = ({ option, style, className }) => {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any | null>(null);
  const [ready, setReady] = useState<boolean>(false);

  // Cargar ECharts desde CDN si no está disponible
  const ensureEcharts = () =>
    new Promise<any>((resolve, reject) => {
      const w = window as any;
      if (w.echarts) return resolve(w.echarts);
      const existing = document.querySelector('script[data-echarts-cdn="true"]') as HTMLScriptElement | null;
      if (existing) {
        existing.addEventListener('load', () => resolve(w.echarts));
        existing.addEventListener('error', reject);
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js';
      script.async = true;
      script.dataset.echartsCdn = 'true';
      script.onload = () => resolve(w.echarts);
      script.onerror = () => reject(new Error('No se pudo cargar ECharts desde CDN'));
      document.body.appendChild(script);
    });

  useEffect(() => {
    let disposed = false;
    (async () => {
      try {
        const echarts = await ensureEcharts();
        if (disposed || !ref.current) return;
        if (!chartRef.current) {
          chartRef.current = echarts.init(ref.current);
        }
        chartRef.current.setOption(option, { notMerge: true });
        setReady(true);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error(e);
      }
    })();
    const onResize = () => chartRef.current && chartRef.current.resize();
    window.addEventListener('resize', onResize);
    return () => {
      disposed = true;
      window.removeEventListener('resize', onResize);
      chartRef.current && chartRef.current.dispose();
      chartRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (chartRef.current && ready) {
      chartRef.current.setOption(option, { notMerge: true });
    }
  }, [option, ready]);

  return <div ref={ref} style={style} className={className} />;
};

export default ReactEChartsLite;


