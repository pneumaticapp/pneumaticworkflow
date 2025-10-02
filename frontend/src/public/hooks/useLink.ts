import { useEffect } from 'react';

interface IUseLinkProps {
  rel?: HTMLLinkElement['rel'];
  href: HTMLLinkElement['href'];
}

export const useLink = ({ href, rel = 'stylesheet' }: IUseLinkProps) => {
  useEffect(() => {
    const link = document.createElement('link');
    link.rel = rel;
    link.href = href;

    document.body.appendChild(link);

    return () => {
      document.body.removeChild(link);
    };
  }, [href]);
};
