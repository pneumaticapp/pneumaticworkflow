import React, { useEffect, useState } from 'react';
import Switch from 'rc-switch';
import { Link } from 'react-router-dom';
import classnames from 'classnames';
import { useIntl } from 'react-intl';

import { useDispatch } from 'react-redux';
import { TemplateOwners } from '../TemplateOwners';
import { ActivityIcon, BoxesIcon, EnableIcon, TrashIcon, UnionIcon, WarningIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';
import { ShowMore } from '../../UI/ShowMore';
import { getLinkToWorkflows } from '../../../utils/routes/getLinkToWorkflows';
import { getLinkToHighlightsByTemplate } from '../../../utils/routes/getLinkToHighlightsByTemplate';
import { Button } from '../../UI/Buttons/Button';
import { IntegrateButton } from '../../IntegrateButton';
import { ITemplate } from '../../../types/template';
import { TCloneTemplatePayload, TDeleteTemplatePayload, TPatchTemplatePayload, discardTemplateChanges } from '../../../redux/actions';
import { getRunnableWorkflow } from '../utils/getRunnableWorkflow';
import { ETemplateStatus } from '../../../types/redux';
import { IRunWorkflow } from '../../WorkflowEditPopup/types';
import { WarningPopup } from '../../UI/WarningPopup';
import { validateTemplate } from '../utils/validateTemplate';
import { isArrayWithItems } from '../../../utils/helpers';
import { NotificationManager } from '../../UI/Notifications';
import { IInfoWarningProps } from '../InfoWarningsModal';
import { isCreateTemplate, history, checkSomeRouteMatchesLocation } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { RouteLeavingGuard } from '../../UI';
import { useTemplateIntegrationsList } from '../../TemplateIntegrationsStats';
import { checkShowDraftTemplateWarning } from '../../Templates';

import styles from './TemplateControlls.css';

export interface ITemplateControllsProps {
  template: ITemplate;
  templateStatus: ETemplateStatus;
  isSubscribed: boolean;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  patchTemplate(payload: TPatchTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  openRunWorkflowModal(payload: IRunWorkflow): void;
  setInfoWarnings(infoWarnings: ((props: IInfoWarningProps) => JSX.Element)[]): void;
}

export function TemplateControlls({
  template,
  templateStatus,
  isSubscribed,
  patchTemplate,
  cloneTemplate,
  deleteTemplate,
  openRunWorkflowModal,
  setInfoWarnings,
}: ITemplateControllsProps) {
  const intl = useIntl();
  const { formatMessage } = intl;
  const dispatch = useDispatch();

  const templateIntegrations = useTemplateIntegrationsList(template.id);
  const [showDraftWarning, setShowDraftWarning] = useState(
    checkShowDraftTemplateWarning(template.isActive, template.isPublic, templateIntegrations),
  );
  const [areIntegrationsVisible, setIntegrationsVisible] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isTemplateActivating, setIsTemplateActivating] = useState(false);
  const [isTemplateDeleted, setIsTemplateDeleted] = useState(false);

  useEffect(() => {
    // sets warning only when integrations are initially loaded
    setShowDraftWarning(checkShowDraftTemplateWarning(template.isActive, template.isPublic, templateIntegrations));
  }, [JSON.stringify(templateIntegrations)]);

  useEffect(() => {
    if (template.isActive) {
      setShowDraftWarning(false);
    }
  }, [template.isActive]);

  const {
    id: templateId,
    name: templateName,
    templateOwners,
    isActive: isTemplateActive,
    finalizable: isTemplateFinalizable,
  } = template;

  const runnableWorkflow = getRunnableWorkflow(template);
  const isSavedTemplate = React.useMemo(() => Boolean(templateId), [templateId]);

  const handleChangeIsActive = (value: ITemplate['isActive'], redirectUrl?: string) => {
    if (!value) {
      patchTemplate({ changedFields: { isActive: false } });
      return;
    }

    const { commonWarnings, infoWarnings } = validateTemplate(template, isSubscribed, intl);
    if (isArrayWithItems(infoWarnings)) {
      setInfoWarnings(infoWarnings);
      return;
    }
    if (isArrayWithItems(commonWarnings)) {
      commonWarnings.forEach((message) => NotificationManager.warning({ message }));
      return;
    }

    setIsTemplateActivating(true);

    patchTemplate({
      changedFields: {
        isActive: true,
      },
      onSuccess: () => {
        setIsTemplateActivating(false);

        if (redirectUrl) {
          history.push(redirectUrl);
        }
      },
      onFailed: () => {
        setIsTemplateActivating(false);
      },
    });
  };

  const renderDeleteTemplateModal = () => {
    if (!templateId) {
      return null;
    }

    const onDeleteTemplate = () => {
      setIsTemplateDeleted(true);
      deleteTemplate({ templateId });
    };

    return (
      <WarningPopup
        acceptTitle={formatMessage({ id: 'template.remove-accept' })}
        declineTitle={formatMessage({ id: 'template.remove-cancel' })}
        title={formatMessage({ id: 'template.remove-title' })}
        message={formatMessage({ id: 'template.remove-message' }, { template: <strong>{templateName}</strong> })}
        closeModal={() => setIsDeleteModalOpen(false)}
        isOpen={isDeleteModalOpen}
        onConfirm={onDeleteTemplate}
        onReject={() => setIsDeleteModalOpen(false)}
      />
    );
  };

  const renderLeavingGuard = () => {
    const showLeavingGuard = !template.isActive && !isTemplateDeleted;

    return (
      <RouteLeavingGuard
        when={showLeavingGuard}
        title={formatMessage({ id: 'templates.inactive-warning-title' })}
        message={formatMessage({ id: 'templates.inactive-warning-message' })}
        onConfirm={(path) => {
          handleChangeIsActive(true, path);
        }}
        onReject={(path) => {
          history.push(path);
        }}
        shouldBlockNavigation={(location) => {
          return !checkSomeRouteMatchesLocation(location.pathname, [
            ERoutes.TemplateView,
            ERoutes.TemplatesEdit,
            ERoutes.TemplatesCreate,
            ERoutes.Login,
          ]);
        }}
        renderControlls={(confirm, reject) => {
          return (
            <>
              <Button
                label={formatMessage({ id: 'templates.enable-button' })}
                onClick={confirm}
                buttonStyle="yellow"
                size="md"
              />

              {templateId && (
                <Button
                  label={formatMessage({ id: 'templates.discard-changes' })}
                  onClick={() => dispatch(discardTemplateChanges({ templateId, onSuccess: reject }))}
                  buttonStyle="transparent-black"
                  size="md"
                />
              )}

              <button type="button" className={classnames('cancel-button', styles['keep-draf-button'])} onClick={reject}>
                {formatMessage({ id: 'templates.keep-draft' })}
              </button>
            </>
          );
        }}
      />
    );
  };

  const renderControllButtons = () => {
    const showEnableTemplateButton = !isTemplateActive || isTemplateActivating;

    return (
      <div className={styles['control-buttons']}>
        <div className={styles['control-buttons_adjacents']}>
          <Button
            size="md"
            className={classnames(
              styles['control-button'],
              styles['enable-button'],
              showEnableTemplateButton ? styles['enable-button_enable'] : styles['enable-button_disable'],
            )}
            type="button"
            onClick={() => handleChangeIsActive(!isTemplateActive)}
            label={showEnableTemplateButton ? formatMessage({ id: 'templates.enable-button' }) : ''}
            buttonStyle="yellow"
            icon={EnableIcon}
            isLoading={isTemplateActivating}
          />
          <Button
            size="md"
            className={classnames(
              styles['control-button'],
              styles['run-button'],
              showEnableTemplateButton && styles['run-button_non-active'],
            )}
            type="button"
            onClick={() => runnableWorkflow && openRunWorkflowModal(runnableWorkflow)}
            disabled={templateStatus !== ETemplateStatus.Saved || !runnableWorkflow}
            label={formatMessage({ id: 'templates.run-workflow' })}
            buttonStyle="transparent-black"
          />
        </div>

        <IntegrateButton
          isVisible={areIntegrationsVisible}
          toggle={() => setIntegrationsVisible(!areIntegrationsVisible)}
          buttonSize="md"
          buttonClassname={styles['control-button']}
          linksType="anchors"
        />
      </div>
    );
  };

  return (
    <>
      {renderDeleteTemplateModal()}
      {templateId && renderLeavingGuard()}
      <div className={styles['settings-block']}>
        <ShowMore label={formatMessage({ id: 'template.owners' })} isInitiallyVisible={isCreateTemplate()}>
          <TemplateOwners
            templateOwners={templateOwners}
            onChangeTemplateOwners={(newTemplateOwners) =>
              patchTemplate({ changedFields: { templateOwners: newTemplateOwners } })
            }
          />
        </ShowMore>
      </div>

      <div className={styles['settings-block']}>
        <ShowMore
          label={formatMessage({ id: 'template.more' })}
          toggleClassName={classnames(!isSavedTemplate && styles['more_disabled'])}
        >
          {templateId && (
            <>
              <Link
                to={getLinkToWorkflows({ templateId })}
                className={styles['more-setting']}
              >
                <BoxesIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-show-workflows' })}</p>
              </Link>
              <Link to={getLinkToHighlightsByTemplate(templateId)} className={styles['more-setting']}>
                <ActivityIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-show-activity' })}</p>
              </Link>
              <button type="button" onClick={() => cloneTemplate({ templateId })} className={styles['more-setting']}>
                <UnionIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-clone-template' })}</p>
              </button>
              <button
                type="button"
                onClick={() => setIsDeleteModalOpen(true)}
                className={classnames(styles['more-setting'], styles['more-setting_warning'])}
              >
                <TrashIcon className={styles['more-setting__icon']} />
                <p className={styles['more-setting__text']}>{formatMessage({ id: 'template.more-delete-template' })}</p>
              </button>
            </>
          )}
        </ShowMore>
      </div>

      <div className={styles['info-controls-switch']}>
        <div className={styles['info-control']}>
          <div className={styles['switch-label']}>
            <IntlMessages id="templates.enable-to-complete-workflow" />
          </div>
          <Switch
            className={classnames(
              'custom-switch custom-switch-primary custom-switch-small ml-auto',
              styles['info-control_switch'],
            )}
            checked={isTemplateFinalizable}
            checkedChildren={null}
            unCheckedChildren={null}
            onChange={(value) => patchTemplate({ changedFields: { finalizable: value } })}
          />
        </div>
      </div>

      {showDraftWarning && (
        <div className={styles['external-links-warning']}>
          <div className={styles['external-links-warning__icon']}>
            <WarningIcon />
          </div>
          <p className={styles['external-links-warning__text']}>{formatMessage({ id: 'templates.draft-warning' })}</p>
        </div>
      )}

      {renderControllButtons()}
    </>
  );
}
