import Switch from 'rc-switch';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { useSelector } from 'react-redux';

import { getIsUserSubsribed, getSubscriptionPlan } from '../../../../redux/selectors/user';
import { Tabs } from '../../../UI';
import { ITemplateClient } from '../../../../types/template';
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
  const { values, setValues } = useTemplateField();
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
  const isShared = isPublic || isEmbedded;
  const [activeTab, setActiveTab] = useState<TPublicFormType>(() => (!isPublic && isEmbedded ? 'embedded' : 'shared'));
  const pendingSuccessUrlWriteRef = useRef<{ value: ITemplateClient['publicSuccessUrl'] } | null>(null);

  const embedCode = useMemo(() => {
    if (!embedUrl) return null;

    return generateEmbedCode(embedUrl);
  }, [embedUrl]);

  const editTemplate = (templateFields: Partial<ITemplateClient>) => {
    setValues({ ...values, ...templateFields }, false);
  };

  const editSuccessUrl = (value: ITemplateClient['publicSuccessUrl']) => {
    pendingSuccessUrlWriteRef.current = { value };
    editTemplate({ publicSuccessUrl: value });
  };

  useEffect(() => {
    const pendingSuccessUrlWrite = pendingSuccessUrlWriteRef.current;
    if (pendingSuccessUrlWrite && pendingSuccessUrlWrite.value === publicSuccessUrl) {
      pendingSuccessUrlWriteRef.current = null;
      return;
    }

    setIsSuccessUrlEnabled(Boolean(publicSuccessUrl));
    setSuccessUrlState(publicSuccessUrl || '');
  }, [publicSuccessUrl]);

  useEffect(() => {
    setActiveTab((currentTab) => {
      if (!isShared) return 'shared';
      if (!isPublic && isEmbedded) return 'embedded';
      if (isPublic && !isEmbedded) return 'shared';

      return currentTab;
    });
  }, [isEmbedded, isPublic, isShared]);

  const toggleSuccessUrlEnabled = () => {
    const nextIsSuccessUrlEnabled = !isSuccessUrlEnabled;
    setIsSuccessUrlEnabled(nextIsSuccessUrlEnabled);
    editSuccessUrl(nextIsSuccessUrlEnabled ? successUrlState : null);
  };

  const toogleFormIsShared = () => {
    const newIsShared = !isShared;

    editTemplate({
      isPublic: newIsShared,
      publicUrl: newIsShared ? '' : publicUrl,
      ...(accessSharedForm && {
        isEmbedded: newIsShared,
        embedUrl: newIsShared ? '' : embedUrl,
      }),
    });
    if (newIsShared) trackShareKickoffForm();
  };

  const changeSuccessUrl = (event: FormEvent<HTMLInputElement>) => {
    const newSuccessUrl = event.currentTarget.value;
    setSuccessUrlState(newSuccessUrl);
    editSuccessUrl(newSuccessUrl);
  };

  const renderTabs = () => {
    if (!isShared) return null;

    const onChangeTab = (tabType: TPublicFormType) => {
      const changedFields: Partial<ITemplateClient> = {};
      if (!publicUrl) {
        changedFields.isPublic = true;
        changedFields.publicUrl = '';
      }
      if (!embedUrl && accessSharedForm) {
        changedFields.isEmbedded = true;
        changedFields.embedUrl = '';
      }
      if (Object.keys(changedFields).length) editTemplate(changedFields);

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
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
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
