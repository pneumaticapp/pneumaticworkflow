import { useCallback, useState } from 'react';
import { useIntl } from 'react-intl';

import { ITemplateClient } from '../types/template';
import { TPatchTemplatePayload } from '../redux/actions';
import { NotificationManager } from '../components/UI/Notifications';
import { IInfoWarningProps } from '../components/TemplateEdit/InfoWarningsModal';
import { validateTemplate } from '../components/TemplateEdit/utils/validateTemplate';
import { isArrayWithItems } from '../utils/helpers';
import { history } from '../utils/history';

export type TInfoWarningRenderer = (props: IInfoWarningProps) => JSX.Element;

export interface IUseTemplateActivationOptions {
  template: ITemplateClient;
  accessConditions: boolean;
  patchTemplate(payload: TPatchTemplatePayload): void;
}

export interface ITemplateActivation {
  isActivating: boolean;
  infoWarnings: TInfoWarningRenderer[];
  isInfoWarningsOpen: boolean;
  closeInfoWarnings(): void;
  setTemplateActive(isActive: boolean, redirectUrl?: string): void;
}

export function useTemplateActivation({
  template,
  accessConditions,
  patchTemplate,
}: IUseTemplateActivationOptions): ITemplateActivation {
  const intl = useIntl();
  const [isActivating, setIsActivating] = useState(false);
  const [infoWarnings, setInfoWarnings] = useState<TInfoWarningRenderer[]>([]);
  const [isInfoWarningsOpen, setIsInfoWarningsOpen] = useState(false);

  const closeInfoWarnings = useCallback((): void => {
    setIsInfoWarningsOpen(false);
  }, []);

  const setTemplateActive = useCallback(
    (isActive: boolean, redirectUrl?: string): void => {
      if (!isActive) {
        patchTemplate({ changedFields: { isActive: false } });

        return;
      }

      const { commonWarnings, infoWarnings: nextInfoWarnings } = validateTemplate(template, accessConditions, intl);

      if (isArrayWithItems(nextInfoWarnings)) {
        setInfoWarnings(nextInfoWarnings);
        setIsInfoWarningsOpen(true);

        return;
      }

      if (isArrayWithItems(commonWarnings)) {
        commonWarnings.forEach((message) => NotificationManager.warning({ message }));

        return;
      }

      setIsActivating(true);

      patchTemplate({
        changedFields: { isActive: true },
        onSuccess: () => {
          setIsActivating(false);

          if (redirectUrl) {
            history.push(redirectUrl);
          }
        },
        onFailed: () => {
          setIsActivating(false);
        },
      });
    },
    [accessConditions, intl, patchTemplate, template],
  );

  return { isActivating, infoWarnings, isInfoWarningsOpen, closeInfoWarnings, setTemplateActive };
}
