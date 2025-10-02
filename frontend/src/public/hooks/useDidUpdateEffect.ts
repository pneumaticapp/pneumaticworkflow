import { useEffect, useRef } from 'react';

export const useDidUpdateEffect = (func: Function, deps?: React.DependencyList | undefined) => {
  const didMount = useRef(false);

  useEffect(() => {
    if (didMount.current) {
      func();
    } else {
      didMount.current = true;
    }
  }, deps);
};
