import * as React from 'react';
import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import { Location } from 'history';
import classnames from 'classnames';

import { Button, RouteLeavingGuard } from '../../UI';
import { ERoutes } from '../../../constants/routes';
import { checkSomeRouteMatchesLocation, history } from '../../../utils/history';
import { discardTemplateChanges, patchTemplate, TPatchTemplatePayload } from '../../../redux/actions';
import { getTemplateData } from '../../../redux/selectors/template';
import { getIsUserSubsribed, getSubscriptionPlan } from '../../../redux/selectors/user';
import { ESubscriptionPlan } from '../../../types/account';
import { useTemplateActivation } from '../../../hooks/useTemplateActivation';
import { InfoWarningsModal } from '../InfoWarningsModal';

import styles from './TemplateLeavingGuard.css';

const ALLOWED_ROUTES = [ERoutes.TemplateView, ERoutes.TemplatesEdit, ERoutes.TemplatesCreate, ERoutes.Login];

export interface ITemplateLeavingGuardProps {
  isTemplateDeleted: boolean;
}

/**
 * Blocks navigation away from an unsaved draft. Mounted above the editor views,
 * so the warning behaves identically in the line and graph modes.
 */
export function TemplateLeavingGuard({ isTemplateDeleted }: ITemplateLeavingGuardProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const template = useSelector(getTemplateData);
  const isSubscribed = useSelector(getIsUserSubsribed);
  const billingPlan = useSelector(getSubscriptionPlan);
  const accessConditions = isSubscribed || billingPlan === ESubscriptionPlan.Free;
  const templateId = template.id;

  const handlePatchTemplate = useCallback(
    (payload: TPatchTemplatePayload): void => {
      dispatch(patchTemplate(payload));
    },
    [dispatch],
  );

  const { infoWarnings, isInfoWarningsOpen, closeInfoWarnings, setTemplateActive } = useTemplateActivation({
    template,
    accessConditions,
    patchTemplate: handlePatchTemplate,
  });

  const handleShouldBlockNavigation = useCallback(
    (location: Location): boolean => !checkSomeRouteMatchesLocation(location.pathname, ALLOWED_ROUTES),
    [],
  );

  const handleConfirm = useCallback(
    (path: string): void => {
      setTemplateActive(true, path);
    },
    [setTemplateActive],
  );

  const handleReject = useCallback((path: string): void => {
    history.push(path);
  }, []);

  const renderControlls = useCallback(
    (confirm: () => void, reject: () => void): React.ReactNode => (
      <>
        <Button
          label={formatMessage({ id: 'templates.save-and-enable-button' })}
          onClick={confirm}
          buttonStyle="yellow"
          size="md"
        />

        <Button
          label={formatMessage({ id: 'templates.save-as-draft' })}
          onClick={reject}
          buttonStyle="transparent-black"
          size="md"
        />

        {templateId && (
          <button
            type="button"
            className={classnames('cancel-button', styles['discard-button'])}
            onClick={() => dispatch(discardTemplateChanges({ templateId, onSuccess: reject }))}
          >
            {formatMessage({ id: 'templates.discard-changes' })}
          </button>
        )}
      </>
    ),
    [dispatch, formatMessage, templateId],
  );

  if (!templateId) {
    return null;
  }

  return (
    <>
      <InfoWarningsModal isOpen={isInfoWarningsOpen} onClose={closeInfoWarnings} warnings={infoWarnings} />

      <RouteLeavingGuard
        when={!template.isActive && !isTemplateDeleted}
        title={formatMessage({ id: 'templates.inactive-warning-title' })}
        message={formatMessage({ id: 'templates.inactive-warning-message' })}
        onConfirm={handleConfirm}
        onReject={handleReject}
        shouldBlockNavigation={handleShouldBlockNavigation}
        renderControlls={renderControlls}
      />
    </>
  );
}
