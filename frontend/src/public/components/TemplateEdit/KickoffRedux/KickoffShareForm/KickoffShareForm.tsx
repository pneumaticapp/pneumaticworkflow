import Switch from 'rc-switch';
import * as React from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector } from 'react-redux';
import { useMemo, useState } from 'react';

import { getIsUserSubsribed, getSubscriptionPlan } from '../../../../redux/selectors/user';
import { Tabs } from '../../../UI';
import { useDidUpdateEffect } from '../../../../hooks/useDidUpdateEffect';
import { ITemplate } from '../../../../types/template';
import { trackShareKickoffForm } from '../../../../utils/analytics';
import { TPublicFormType } from '../../../../types/publicForms';
import { generateEmbedCode } from './utils/generateEmbedCode';
import { ESubscriptionPlan } from '../../../../types/account';
import { useTemplateField } from '../../useTemplateForm';
import { IKickoffShareFormProps } from './types';
import { EmbeddedFormTab, SharedFormTab } from './KickoffShareTabs';

import styles from './KickoffShareForm.css';

export function KickoffShareForm({ className }: IKickoffShareFormProps) {
  const { formatMessage } = useIntl();
  const { values, setFieldValue } = useTemplateField();
  const isSubscribed = useSelector(getIsUserSubsribed);
  const subcriptionPlan = useSelector(getSubscriptionPlan);
  const accessSharedForm = isSubscribed || subcriptionPlan === ESubscriptionPlan.Free;
  const { publicUrl, isPublic, publicSuccessUrl, embedUrl, isEmbedded } = values;

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

  const [isSuccessUrlEnabled, setIsSuccessUrlEnabled] = useState(Boolean(publicSuccessUrl));
  const [successUrlState, setSuccessUrlState] = useState(publicSuccessUrl || '');
  const [isShared, setIsShared] = useState(isPublic || isEmbedded);
  const [activeTab, setActiveTab] = useState<TPublicFormType>('shared');

  const embedCode = useMemo(() => {
    if (!embedUrl) return null;

    return generateEmbedCode(embedUrl);
  }, [embedUrl]);

  const editTemplate = (templateFields: Partial<ITemplate>) => {
    (Object.keys(templateFields) as (keyof ITemplate)[]).forEach((key) => {
      setFieldValue(key as string, templateFields[key], false);
    });
  };

  useDidUpdateEffect(() => {
    if (!isSuccessUrlEnabled) {
      editTemplate({ publicSuccessUrl: null });
    } else {
      editTemplate({ publicSuccessUrl: successUrlState });
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
    if (newIsShared) trackShareKickoffForm();
  };

  const updateIsFormPublic = (isEnabled: boolean) => {
    editTemplate({
      isPublic: isEnabled,
      publicUrl: isEnabled
        ? '' // clear publicUrl in case the form is just shared, new value will be set on the backend
        : publicUrl,
    });
  };

  const updateIsFormEmbedded = (isEnabled: boolean) => {
    if (!accessSharedForm) return;

    editTemplate({
      isEmbedded: isEnabled,
      embedUrl: isEnabled
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
    if (!isShared) return null;

    const onChangeTab = (tabType: TPublicFormType) => {
      if (!publicUrl) updateIsFormPublic(true);
      if (!embedUrl) updateIsFormEmbedded(true);

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

        <div className={styles['tabs']}>
          {activeTab === 'shared' ? (
            <SharedFormTab
              publicUrl={publicUrl}
              isSuccessUrlEnabled={isSuccessUrlEnabled}
              successUrl={successUrlState}
              onToggleSuccessUrl={toggleSuccessUrlEnabled}
              onChangeSuccessUrl={changeSuccessUrl}
            />
          ) : (
            <EmbeddedFormTab
              hasAccess={accessSharedForm}
              embedUrl={embedUrl}
              embedCode={embedCode}
            />
          )}
        </div>
      </>
    );
  };

  return (
    <div className={classnames(styles['share-wrapper'], className)}>
      <div
        className={styles['share-control']}
        role="button"
        tabIndex={0}
        onClick={toogleFormIsShared}
        onKeyDown={({ key }) => {
          if (key === 'Enter' || key === ' ') {
            toogleFormIsShared();
          }
        }}
      >
        <Switch
          className="custom-switch custom-switch-primary custom-switch-small"
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
