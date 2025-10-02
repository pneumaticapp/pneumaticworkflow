import { useCallback, useEffect } from 'react';
import { ELoggedState } from '../../types/redux';

export const LOGGED_STATE_STORAGE_KEY = 'logged_state';

export const getLoggedStorageState = () => {
  return localStorage.getItem(LOGGED_STATE_STORAGE_KEY);
};

export const setLoggedStorageState = (loggedState: ELoggedState) => {
  localStorage.setItem(LOGGED_STATE_STORAGE_KEY, loggedState);
};

// used to log out each tab if at least one of them is logged out
export function useSyncLoggedTabsState(loggedState: ELoggedState, onLogout: () => void) {
  const handleChangeLoggedState = useCallback(() => {
    const storageLoggedState = getLoggedStorageState();
    if (storageLoggedState === ELoggedState.LoggedOut && loggedState === ELoggedState.LoggedIn) {
      onLogout();
    }
  }, [loggedState]);

  useEffect(() => {
    setLoggedStorageState(loggedState);
  }, [loggedState]);

  useEffect(() => {
    const storageLoggedState = getLoggedStorageState();
    if (!storageLoggedState) {
      setLoggedStorageState(loggedState);
    }

    window.addEventListener('storage', handleChangeLoggedState);

    return () => {
      window.removeEventListener('storage', handleChangeLoggedState);
    };
  }, []);
}
