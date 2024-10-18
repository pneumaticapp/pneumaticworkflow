/* eslint-disable */
/* prettier-ignore */
import Switch from 'rc-switch';
import * as React from 'react';
import { useIntl } from 'react-intl';
import * as classnames from 'classnames';
import { useDispatch, useSelector } from 'react-redux';
import { default as TextareaAutosize } from 'react-textarea-autosize';

import { useMemo } from 'react';
import { patchTemplate } from '../../../../redux/actions';
import { getTemplateData } from '../../../../redux/selectors/template';
import { getIsUserSubsribed } from '../../../../redux/selectors/user';
import { copyToClipboard } from '../../../../utils/helpers';
import { NotificationManager } from '../../../UI/Notifications';
import { Button, InputField, Loader, Tabs } from '../../../UI';
import { useDidUpdateEffect } from '../../../../hooks/useDidUpdateEffect';
import { ITemplate } from '../../../../types/template';
import { noop } from '../../../../utils/noop';
import { trackShareKickoffForm } from '../../../../utils/analytics';
import { TPublicFormType } from '../../../../types/publicForms';
import { generateEmbedCode } from './utils/generateEmbedCode';

import styles from './KickoffShareForm.css';

interface IKickoffShareFormProps {
  className?: string;
}

export function KickoffShareForm({ className }: IKickoffShareFormProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const isSubscribed = useSelector(getIsUserSubsribed);
  const { publicUrl, isPublic, publicSuccessUrl, embedUrl, isEmbedded } = useSelector(getTemplateData);

  const TABS: { id: TPublicFormType; label: string }[] = useMemo(
    () => [
      {
        id: 'shared',
        label: formatMessage({ id: 'kickoff.share-form' }),
      },
      {
        id: 'embedded',
        label: formatMessage({ id: 'kickoff.embed-code' }),
      },
    ],
    [formatMessage],
  );

  const [isSuccessUrlEnabled, setIsSuccessUrlEnabled] = React.useState(Boolean(publicSuccessUrl));
  const [successUrlState, setSuccessUrlState] = React.useState(publicSuccessUrl || '');
  const [isShared, setIsShared] = React.useState(isPublic || isEmbedded);
  const [activeTab, setActiveTab] = React.useState<TPublicFormType>('shared');

  const embedCode = React.useMemo(() => {
    if (!embedUrl) {
      return null;
    }

    return generateEmbedCode(embedUrl);
  }, [embedUrl]);

  const editTemplate = (templateFields: Partial<ITemplate>) => {
    dispatch(patchTemplate({ changedFields: templateFields }));
  };

  useDidUpdateEffect(() => {
    if (!isSuccessUrlEnabled) {
      editTemplate({ publicSuccessUrl: null });
    }
  }, [isSuccessUrlEnabled]);

  const toggleSuccessUrlEnabled = () => {
    setIsSuccessUrlEnabled(!isSuccessUrlEnabled);
  };

  const toogleFormIsShared = () => {
    const newIsShared = !isShared;

    setIsShared(newIsShared);

    updateIsFormPublic(newIsShared);
    updateIsFormEmbedded(newIsShared);

    if (newIsShared) {
      trackShareKickoffForm();
    }
  };

  const updateIsFormPublic = (isPublic: boolean) => {
    editTemplate({
      isPublic,
      publicUrl: isPublic
        ? '' // clear publicUrl in case the form is just shared, new value will be set on the backend
        : publicUrl,
    });
  };

  const updateIsFormEmbedded = (isEmbedded: boolean) => {
    if (!isSubscribed) {
      return;
    }

    editTemplate({
      isEmbedded,
      embedUrl: isEmbedded
        ? '' // clear embedUrl in case the form is just shared, new value will be set on the backend
        : embedUrl,
    });
  };

  const changeSuccessUrl = (event: React.FormEvent<HTMLInputElement>) => {
    const newSuccessUrl = event.currentTarget.value;
    editTemplate({ publicSuccessUrl: newSuccessUrl });
    setSuccessUrlState(newSuccessUrl);
  };

  const renderTabs = () => {
    if (!isShared) {
      return null;
    }

    const onChangeTab = (tabType: TPublicFormType) => {
      if (!publicUrl) {
        updateIsFormPublic(true);
      }

      if (!embedUrl) {
        updateIsFormEmbedded(true);
      }

      setActiveTab(tabType);
    };

    return (
      <>
        <Tabs
          containerClassName={styles['tabs-labels']}
          values={TABS}
          activeValueId={activeTab}
          onChange={onChangeTab}
        />

        <div className={styles['tabs']}>{renderActiveTab()}</div>
      </>
    );
  };

  const renderActiveTab = () => {
    const renderSharedFormTab = () => {
      const handleCopyShareLink = () => {
        if (!publicUrl) {
          return;
        }

        copyToClipboard(publicUrl);
        NotificationManager.success({ message: 'kickoff.share-link-copied' });
      };

      return (
        <>
          <p className={styles['description']}>{formatMessage({ id: 'kickoff.share-description' })}</p>

          {!publicUrl ? (
            <Loader isLoading isCentered={false} containerClassName={styles['loader']} />
          ) : (
            <>
              <p className={classnames(styles['field-title'], styles['field-title_indent'])}>
                {formatMessage({ id: 'kickoff.shared-link-title' })}
              </p>
              <InputField value={publicUrl || ''} onChange={noop} className={styles['public-url']} fieldSize="md" />

              <div className={styles['redirect-url-container']}>
                <div className={styles['redirect-url-header']}>
                  <p className={styles['field-title']}>{formatMessage({ id: 'kickoff.redirect-url-title' })}</p>

                  <div className={styles['redirect-url__toggle']}>
                    <p className={styles['redirect-url-toggle__label']}>
                      {formatMessage({ id: 'kickoff.redirect-url-toggle' })}
                    </p>
                    <Switch
                      className={classnames('custom-switch custom-switch-primary custom-switch-small ml-auto')}
                      checked={isSuccessUrlEnabled}
                      checkedChildren={null}
                      unCheckedChildren={null}
                      onChange={toggleSuccessUrlEnabled}
                    />
                  </div>
                </div>
                <InputField
                  value={successUrlState}
                  onChange={changeSuccessUrl}
                  className={styles['redirect-url__field']}
                  fieldSize="md"
                  disabled={!isSuccessUrlEnabled}
                  placeholder={formatMessage({ id: 'kickoff.url-placeholder' })}
                />
              </div>

              <Button
                type="button"
                onClick={handleCopyShareLink}
                className={styles['copy-button']}
                label={formatMessage({ id: 'kickoff.copy-link' })}
                buttonStyle="transparent-orange"
                size="md"
              />
            </>
          )}
        </>
      );
    };

    const renderEmbeddedFormTab = () => {
      if (!isSubscribed) {
        return null;
      }

      const handleCopyEmbedCode = () => {
        if (!embedCode) {
          return;
        }

        copyToClipboard(embedCode);
        NotificationManager.success({ message: 'kickoff.embed-code-copied' });
      };

      return (
        <>
          <p className={styles['description']}>{formatMessage({ id: 'kickoff.embed-description' })}</p>

          {!embedUrl ? (
            <Loader isLoading isCentered={false} containerClassName={styles['loader']} />
          ) : (
            <>
              <TextareaAutosize value={embedCode!} onChange={noop} className={styles['embed-code-field']} />

              <Button
                type="button"
                onClick={handleCopyEmbedCode}
                className={styles['copy-button']}
                label={formatMessage({ id: 'kickoff.copy-embed-code' })}
                buttonStyle="transparent-orange"
                size="md"
              />
            </>
          )}
        </>
      );
    };

    const renderTabMethodsMap: { [key in TPublicFormType]: () => JSX.Element | null } = {
      shared: renderSharedFormTab,
      embedded: renderEmbeddedFormTab,
    };

    return renderTabMethodsMap[activeTab]();
  };

  return (
    <div className={classnames(styles['share-wrapper'], className)}>
      <div className={styles['share-control']} role="button" onClick={toogleFormIsShared}>
        <Switch
          className={'custom-switch custom-switch-primary custom-switch-small'}
          checked={isShared}
          checkedChildren={null}
          unCheckedChildren={null}
        />
        <p className={styles['share-control__text']}>{formatMessage({ id: 'kickoff.share-control' })}</p>
      </div>

      {renderTabs()}
    </div>
  );
}
