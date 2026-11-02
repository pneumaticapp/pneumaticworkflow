import { useCheckDevice } from '../../hooks/useCheckDevice';

export function useMobileMenuPortalProps() {
  const { isMobile } = useCheckDevice();

  return isMobile ? { menuPortalTarget: document.body, menuPosition: 'fixed' as const } : {};
}
