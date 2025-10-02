import { useEffect } from 'react';
import * as DEFAULT_ICON_PATH from '../../assets/favicon.png';
import * as ALERT_ICON_PATH from '../../assets/favicon-alert.png';

const HAS_UPDATES_STORAGE_KEY = 'hasUpdates';

export function useFaviconUpdater(hasNewNotifications: boolean, hasNewTasks: boolean) {
  const handleStorageUpdates = () => {
    const storageHasUpdates = localStorage.getItem(HAS_UPDATES_STORAGE_KEY);
    const favicon = document.querySelector('link[rel="icon"]') as HTMLLinkElement;

    favicon.href = storageHasUpdates === 'true' ? ALERT_ICON_PATH : DEFAULT_ICON_PATH;
  };

  useEffect(() => {
    const hasUpdates = hasNewNotifications || hasNewTasks;

    localStorage.setItem(HAS_UPDATES_STORAGE_KEY, String(hasUpdates));
    handleStorageUpdates();

    window.addEventListener('storage', handleStorageUpdates);

    return () => {
      window.removeEventListener('storage', handleStorageUpdates);
    };
  }, [hasNewNotifications, hasNewTasks]);
}
