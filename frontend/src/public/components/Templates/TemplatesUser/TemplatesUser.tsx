/* eslint-disable jsx-a11y/control-has-associated-label */
import React from 'react';
import classnames from 'classnames';
import { Link } from 'react-router-dom';

import { ITemplatesList } from '../../../types/redux';
import { IntlMessages } from '../../IntlMessages';
import { TemplateCard } from './TemplateCard';
import { isArrayWithItems } from '../../../utils/helpers';
import { TCloneTemplatePayload, TDeleteTemplatePayload } from '../../../redux/actions';
import { Header } from '../../UI';
import { AIPlusIcon, RoundDocIcon } from '../../icons';
import { PageTitle } from '../../PageTitle/PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { ERoutes } from '../../../constants/routes';
import { analytics, EAnalyticsCategory, EAnalyticsAction } from '../../../utils/analytics';

import styles from '../Templates.css';
import { isEnvAi } from '../../../constants/enviroment';

export interface ITemplatesUserProps {
  templatesList: ITemplatesList;
  loading?: boolean;
  canEdit: boolean | undefined;
  cloneTemplate(payload: TCloneTemplatePayload): void;
  deleteTemplate(payload: TDeleteTemplatePayload): void;
  loadTemplates(offset: number): void;
  openRunWorkflowModal({ templateId }: { templateId: number }): void;
  setIsAITemplateModalOpened(value: boolean): void;
}

export function TemplatesUser({
  templatesList,
  loading,
  canEdit,
  cloneTemplate,
  deleteTemplate,
  loadTemplates,
  openRunWorkflowModal,
  setIsAITemplateModalOpened,
}: ITemplatesUserProps) {
  const { count, items } = templatesList;
  const isListFullLoaded = count === items.length;

  const handleClickMore = () => {
    if (count > items.length) {
      loadTemplates(items.length);
    }
  };

  const renderGenerateAITemplateButton = () => {
    return (
      <div className={styles['card']}>
        <button type="button" onClick={() => setIsAITemplateModalOpened(true)} className={styles['custom-card']}>
          <div>
            <Header size="6" tag="p" className={styles['custom-card__title']}>
              <IntlMessages id="template.generate-with-ai.title" />
            </Header>
            <p className={styles['custom-card__caption']}>
              <IntlMessages id="template.generate-with-ai.description" />
            </p>
          </div>
          <div className={styles['custom-card__icon']}>
            <AIPlusIcon />
          </div>
        </button>
      </div>
    );
  };

  const renderAddTemplateButton = () => {
    const onClickAddTemplate = () => {
      analytics.send('Add template', {
        category: EAnalyticsCategory.Templates,
        label: 'Templates page',
        action: EAnalyticsAction.Initiated,
      });
    };

    return (
      <Link className={styles['card']} to={ERoutes.TemplatesCreate} onClick={onClickAddTemplate}>
        <div className={classnames(styles['custom-card'])}>
          <div>
            <Header size="6" tag="p" className={styles['custom-card__title']}>
              <IntlMessages id="templates.new-template-name" />
            </Header>
            <p className={styles['custom-card__caption']}>
              <IntlMessages id="templates.new-template-description" />
            </p>
          </div>
          <div className={styles['custom-card__icon']}>
            <RoundDocIcon />
          </div>
        </div>
      </Link>
    );
  };

  return (
    <>
      <PageTitle titleId={EPageTitle.Templates} className={styles['title']} withUnderline={false} />

      <div className={classnames(styles['cards-wrapper'], { [styles['container-loading']]: loading })}>
        {loading && <div className="loading" />}

        {isEnvAi && renderGenerateAITemplateButton()}
        {renderAddTemplateButton()}

        {items.map((template) => (
          <TemplateCard
            {...template}
            key={template.id}
            onRunWorkflow={() => openRunWorkflowModal({ templateId: template.id })}
            canEdit={canEdit}
            cloneTemplate={cloneTemplate}
            deleteTemplate={deleteTemplate}
          />
        ))}
      </div>

      {!isListFullLoaded && isArrayWithItems(items) && (
        <button
          className={classnames('btn btn-active', styles['btn-more'])}
          onClick={handleClickMore}
          disabled={loading}
          data-test-id="show-more-button"
          type="button"
        >
          <IntlMessages id="general.show-more.template" />
        </button>
      )}
    </>
  );
}
