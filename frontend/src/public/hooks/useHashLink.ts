import { MutableRefObject, useEffect, useRef } from 'react';
import { scrollToElementWhenStable } from '../utils/scroll';
import { history } from '../utils/history';

type THashLinkHandler = {
  hash: string;
  element: MutableRefObject<HTMLDivElement | null>;
  handle?(): void;
};

export function useHashLink(settings: THashLinkHandler[]) {
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  const cancelScrollRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    const handleHashLinkUrl = () => {
      cancelScrollRef.current?.();
      cancelScrollRef.current = null;

      const { hash } = history.location;
      if (!hash) {
        return;
      }

      const currentSetting = settingsRef.current.find((setting) => `#${setting.hash}` === hash);
      if (!currentSetting) {
        return;
      }

      const { element, handle } = currentSetting;
      handle?.();

      if (!element.current) {
        return;
      }

      cancelScrollRef.current = scrollToElementWhenStable(element.current);
    };

    handleHashLinkUrl();

    const unregister = history.listen(handleHashLinkUrl);

    return () => {
      cancelScrollRef.current?.();
      unregister();
    };
  }, []);
}
