import { useEffect } from 'react';

const INTERCOM_COMPONENTS_ID = ['intercom-frame', 'intercom-container'];
const INTERCOM_CLASSES = ['intercom-lightweight-app'];

export const useShouldHideIntercom = (shouldHideIntercom: boolean = true) => {
  useEffect(() => {
    const intercomObserver = new MutationObserver(mutationList => {
      // eslint-disable-next-line no-restricted-syntax
      for (const mutation of mutationList) {
        const nodes = Array.from(mutation.addedNodes);

        // eslint-disable-next-line no-restricted-syntax
        for (const node of nodes) {
          if (node instanceof HTMLElement && INTERCOM_COMPONENTS_ID.includes(node.id)) {
            node.remove();
          }
        }
      }
    });

    if (!shouldHideIntercom) {
      intercomObserver.disconnect();

      return undefined;
    }

    const hideIntercom = () => {
      delete window.Intercom;
      INTERCOM_COMPONENTS_ID.forEach(id => document.getElementById(id)?.remove());
      INTERCOM_CLASSES.forEach(className => Array.from(document.getElementsByClassName(className)).forEach(node => node.remove()));
      intercomObserver.observe(document.body, { childList: true });
    };

    hideIntercom();

    return () => {
      intercomObserver.disconnect();
    };
  }, [shouldHideIntercom]);
};
