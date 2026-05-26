/* eslint-disable jsx-a11y/control-has-associated-label */
import * as React from 'react';
import classnames from 'classnames';

import { IntlMessages } from '../../IntlMessages';
import { TemplateCard } from './TemplateCard';
import { isArrayWithItems } from '../../../utils/helpers';
import { AddCardButton } from '../../UI';
import { AIPlusIcon, RoundDocIcon } from '../../icons';
import { PageTitle } from '../../PageTitle/PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { ERoutes } from '../../../constants/routes';
import { analytics, EAnalyticsCategory, EAnalyticsAction } from '../../../utils/analytics';
import { ITemplatesUserProps } from './types';

import styles from '../Templates.css';
import { isEnvAi } from '../../../constants/enviroment';

export function TemplatesUser({
  templatesList,
  loading,
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

  const renderAddTemplateButton = () => {
    const onClickAddTemplate = () => {
      analytics.send('Add template', {
        category: EAnalyticsCategory.Templates,
        label: 'Templates page',
        action: EAnalyticsAction.Initiated,
      });
    };

    return (
      <AddCardButton
        className={styles['card']}
        to={ERoutes.TemplatesCreate}
        onClick={onClickAddTemplate}
        title={<IntlMessages id="templates.new-template-name" />}
        caption={<IntlMessages id="templates.new-template-description" />}
        icon={<RoundDocIcon />}
      />
    );
  };

  return (
    <>
      <PageTitle titleId={EPageTitle.Templates} className={styles['title']} withUnderline={false} />

      <div className={classnames(styles['cards-wrapper'], { [styles['container-loading']]: loading })}>
        {loading && <div className="loading" />}

        {isEnvAi && (
          <AddCardButton
            className={styles['card']}
            onClick={() => setIsAITemplateModalOpened(true)}
            title={<IntlMessages id="template.generate-with-ai.title" />}
            caption={<IntlMessages id="template.generate-with-ai.description" />}
            icon={<AIPlusIcon />}
          />
        )}
        {renderAddTemplateButton()}

        {items.map((template) => (
          <TemplateCard
            {...template}
            key={template.id}
            onRunWorkflow={() => openRunWorkflowModal({ templateId: template.id })}
            canEdit={template.isEditable}
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
