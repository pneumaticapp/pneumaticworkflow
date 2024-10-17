import * as React from 'react';

export const useTransitionSwitch = (active?: boolean): [boolean, React.Dispatch<React.SetStateAction<boolean>>] => {
  const [visibleActive, setVisibleActive] = React.useState(false);
  React.useEffect(() => {
    if (active !== undefined) {
      setVisibleActive(active);
    }
  }, [active]);

  return [visibleActive, setVisibleActive];
};
