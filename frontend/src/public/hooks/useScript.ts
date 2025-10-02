import { useEffect } from 'react';

interface IUseScriptProps {
  src: HTMLScriptElement['src'];
  type?: HTMLScriptElement['type'];
}

export const useScript = ({ src, type }: IUseScriptProps) => {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = src;
    if (type) {
      script.type = type;
    }
    script.async = true;

    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [src]);
};
