import { useEffect } from 'react';
import { history } from '../utils/history';

type THashLinkHandler = {
  hash: string;
  element: React.MutableRefObject<HTMLDivElement | null>;
  handle?(): void;
};

export function useHashLink(settings: THashLinkHandler[]) {
  useEffect(() => {
    const handleHashLinkUrl = () => {
      const { hash } = history.location;
      if (!hash) {
        return;
      }

      const currentSetting = settings.find((setting) => `#${setting.hash}` === hash);
      if (!currentSetting) {
        return;
      }

      const { element, handle } = currentSetting;
      handle?.();
      element.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    handleHashLinkUrl();

    const unregister = history.listen(handleHashLinkUrl);

    return unregister;
  }, []);
}
