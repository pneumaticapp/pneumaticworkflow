/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count
import * as React from 'react';
import { useIntl } from 'react-intl';
import { useDispatch, useSelector } from 'react-redux';
import classnames from 'classnames';

import { TemplateIntegrationsMenu } from './Menu';
import { ZAPIER_EMBED_CSS_HREF, ZAPIER_EMBED_SCRIPT_SRC } from '../../../constants/defaultValues';
import { useLink } from '../../../hooks/useLink';
import { useScript } from '../../../hooks/useScript';
import { loadApiKey, loadWebhooks } from '../../../redux/actions';
import { getTemplateData } from '../../../redux/selectors/template';
import { getUserApiKey } from '../../../redux/selectors/user';
import { copyToClipboard } from '../../../utils/helpers';
import { mapTemplateRequest } from '../../../utils/template';
import { NotificationManager } from '../../UI/Notifications';
import { Header, InputField, Tabs } from '../../UI';
import { useCheckDevice } from '../../../hooks/useCheckDevice';
import { Webhooks } from './Webhook/Webhooks';
import { useHashLink } from '../../../hooks/useHashLink';
import { ETemplateParts } from '../../../types/template';
import { mapRequestBody } from '../../../utils/mappers';

import styles from './TemplateIntegrations.css';

enum EIntergrationTabs {
  AppDirectory = 'app-directory',
  ZapTemplates = 'zap-templates',
  ZapManager = 'zap-manager',
  API = 'api',
  Webhook = 'webhook',
}

const TABS: { id: EIntergrationTabs; label: string }[] = [
  {
    id: EIntergrationTabs.AppDirectory,
    label: 'App Directory',
  },
  {
    id: EIntergrationTabs.ZapTemplates,
    label: 'Zap Templates',
  },
  {
    id: EIntergrationTabs.ZapManager,
    label: 'Zap Manager',
  },
  {
    id: EIntergrationTabs.API,
    label: 'API',
  },
  {
    id: EIntergrationTabs.Webhook,
    label: 'Webhooks',
  },
];

export function TemplateIntegrations() {
  useScript({ src: ZAPIER_EMBED_SCRIPT_SRC, type: 'module' });
  useLink({ href: ZAPIER_EMBED_CSS_HREF });
  const { isDesktop } = useCheckDevice();

  const { useState, useEffect, useRef } = React;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const templateData = useSelector(getTemplateData);

  const [isExpanded, setIsExpanded] = useState(false);
  const [currentTab, setCurrentTab] = useState<EIntergrationTabs>(EIntergrationTabs.AppDirectory);

  const apiCode = mapRequestBody(mapTemplateRequest(templateData), 'prettify');

  const apiKey = useSelector(getUserApiKey);
  const apiKeyValue = apiKey.isLoading ? formatMessage({ id: 'integrations.loading-api-key' }) : apiKey.data;

  useHashLink([
    {
      element: containerRef,
      hash: ETemplateParts.Integrations,
      handle: () => {
        setIsExpanded(true);
        setCurrentTab(EIntergrationTabs.AppDirectory);
      },
    },
    {
      element: containerRef,
      hash: ETemplateParts.Zapier,
      handle: () => {
        setIsExpanded(true);
        setCurrentTab(EIntergrationTabs.ZapTemplates);
      },
    },
    {
      element: containerRef,
      hash: ETemplateParts.API,
      handle: () => {
        setIsExpanded(true);
        setCurrentTab(EIntergrationTabs.API);
      },
    },
    {
      element: containerRef,
      hash: ETemplateParts.Webhook,
      handle: () => {
        setIsExpanded(true);
        setCurrentTab(EIntergrationTabs.Webhook);
      },
    },
  ]);

  const onToggle = () => setIsExpanded(!isExpanded);

  const handelCopyCode = () => {
    copyToClipboard(apiCode);
    NotificationManager.success({
      message: 'template.intergrations-code-copied',
    });
  };

  const handleCopyApiKey = () => {
    if (!apiKey.data || apiKey.isLoading) {
      return;
    }

    copyToClipboard(apiKey.data);
    NotificationManager.success({ message: 'user.copied-to-clipboard' });
  };

  useEffect(() => {
    if (isExpanded) {
      dispatch(loadApiKey());
      dispatch(loadWebhooks());
    }
  }, [isExpanded]);

  const renderCurrentTab = () => {
    const tabContentMap = {
      [EIntergrationTabs.AppDirectory]: () => (
        <>
          <div className={styles['tab-description']}>
            {formatMessage({ id: 'template.intergrations-app-directory-desc' })}
          </div>
          <zapier-app-directory
            app="pneumatic"
            link-target="new-tab"
            theme="light"
            applimit={10}
            zaplimit={1}
            introcopy="hide"
            create-without-template="hide"
            use-this-zap="show"
          />
        </>
      ),
      [EIntergrationTabs.ZapTemplates]: () => (
        <>
          <div className={styles['tab-description']}>
            {formatMessage({ id: 'template.intergrations-zap-templates-desc' })}
          </div>
          <zapier-zap-templates
            apps="pneumatic"
            create-without-template="hide"
            limit="5"
            use-this-zap="show"
            theme="light"
          />
        </>
      ),
      [EIntergrationTabs.ZapManager]: () => (
        <>
          <div className={styles['tab-description']}>
            {formatMessage({ id: 'template.intergrations-zap-manager-desc' })}
          </div>
          <zapier-zap-manager
            client-id="vnDCQOB29Ak3iQbyyzg7zM0wcUJImgpRFTCR4BuJ"
            link-target="new-tab"
            theme="light"
          ></zapier-zap-manager>
        </>
      ),
      [EIntergrationTabs.API]: () => (
        <>
          <div className={styles['tab-description']}>{formatMessage({ id: 'template.intergrations-api-desc' })}</div>
          <div className={styles['code']}>
            <div className={styles['code-inner']}>{apiCode}</div>

            {isDesktop && (
              <button
                type="button"
                className={classnames(styles['copy-button'], styles['code-copy-button'])}
                onClick={handelCopyCode}
              >
                {formatMessage({ id: 'template.intergrations-copy-code' })}
              </button>
            )}
          </div>
          <div className={styles['api-key']}>
            <p className={styles['api-key__title']}>{formatMessage({ id: 'template.intergrations-api-key' })}</p>
            <div className={styles['api-key__control']}>
              <InputField value={apiKeyValue} fieldSize="md" />

              {isDesktop && (
                <button
                  type="button"
                  className={classnames(styles['copy-button'], styles['api-key-copy-button'])}
                  onClick={handleCopyApiKey}
                >
                  {formatMessage({ id: 'template.intergrations-api-key-copy' })}
                </button>
              )}
            </div>
          </div>
        </>
      ),
      [EIntergrationTabs.Webhook]: () => (
        <>
          <div className={styles['tab-description']}>
            {formatMessage({ id: 'template.intergrations-webhook-desc' })}
          </div>
          <Webhooks />
        </>
      ),
    };

    return tabContentMap[currentTab]();
  };

  return (
    <div className={styles['container']} ref={containerRef}>
      <div className={styles['header']}>
        <Header size="6" tag="button" className={styles['header-title']} onClick={onToggle} type="button">
          {formatMessage({ id: 'template.intergrations-title' })}
        </Header>

        <TemplateIntegrationsMenu isOpen={isExpanded} toggle={onToggle} />
      </div>
      {isExpanded && (
        <div className={styles['contents']}>
          <Tabs
            containerClassName={styles['tabs-labels']}
            tabClassName={styles['tabs-labels__item']}
            values={TABS}
            activeValueId={currentTab}
            onChange={setCurrentTab}
          />
          {renderCurrentTab()}
        </div>
      )}
    </div>
  );
}
