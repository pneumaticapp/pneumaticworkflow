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

      // the target section is still expanding and its content is still loading,
      // so the scroll has to wait until its position stops moving
      cancelScrollRef.current?.();
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
