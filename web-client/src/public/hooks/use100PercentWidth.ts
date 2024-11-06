import { useLayoutEffect, useState } from 'react';

export function use100PercentWidth() {
  const [bgWidth, setBgWidth] = useState(0);
  useLayoutEffect(() => {
    // manually setting backgroud width,
    // because 100vw is causing horizontall scrolling in Windows
    const set100PercentBgWidth = () => {
      setBgWidth(document.documentElement.clientWidth);
    };
    window.addEventListener('resize', set100PercentBgWidth);
    set100PercentBgWidth();

    return () => window.removeEventListener('resize', set100PercentBgWidth);
  }, []);

  return bgWidth;
}
