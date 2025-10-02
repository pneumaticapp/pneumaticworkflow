import * as React from 'react';

export function useDelayUnmount(isMounted: boolean, delayTime: number) {
  const [shouldRender, setShouldRender] = React.useState(false);

  React.useEffect(() => {
    let timeoutId: NodeJS.Timeout | number;
    if (isMounted && !shouldRender) {
      setShouldRender(true);
    } else if (!isMounted && shouldRender) {
      timeoutId = setTimeout(
        () => setShouldRender(false),
        delayTime,
      );
    }

    return () => clearTimeout(timeoutId as number);
  }, [isMounted, delayTime, shouldRender]);

  return shouldRender;
}
