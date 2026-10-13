import * as React from 'react';
import classnames from 'classnames';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';

import { IntlMessages } from '../../IntlMessages';
import { TemplateCard } from './TemplateCard';
import { isArrayWithItems } from '../../../utils/helpers';
import { AddCardButton } from '../../UI';
import { AIPlusIcon, RoundDocIcon } from '../../icons';
import { PageTitle } from '../../PageTitle/PageTitle';
import { EPageTitle } from '../../../constants/defaultValues';
import { ERoutes } from '../../../constants/routes';
import { analytics, EAnalyticsCategory, EAnalyticsAction } from '../../../utils/analytics';
import { isEnvAi } from '../../../constants/enviroment';
import {
  cloneTemplate,
  deleteTemplate,
  loadTemplates,
  openRunWorkflowModalByTemplateId,
  setIsAITemplateModalOpened,
} from '../../../redux/actions';
import { getIsAdmin } from '../../../redux/selectors/user';
import { getTemplatesIsListLoading, getTemplatesList } from '../../../redux/selectors/templates';

import styles from '../Templates.css';

export function TemplatesUser() {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const canCreateTemplates = useSelector(getIsAdmin);
  const templatesList = useSelector(getTemplatesList);
  const loading = useSelector(getTemplatesIsListLoading);

  const { count, items } = templatesList;
  const isListFullLoaded = count === items.length;
  const showMoreLabel = formatMessage({ id: 'general.show-more.template' });

  const handleClickMore = () => {
    if (count > items.length) {
      dispatch(loadTemplates(items.length));
    }
  };

  const renderAddTemplateButton = () => {
    if (!canCreateTemplates) {
      return null;
    }

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

        {canCreateTemplates && isEnvAi && (
          <AddCardButton
            className={styles['card']}
            onClick={() => dispatch(setIsAITemplateModalOpened(true))}
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
            onRunWorkflow={() => dispatch(openRunWorkflowModalByTemplateId({ templateId: template.id }))}
            canEdit={template.isEditable}
            cloneTemplate={(payload) => dispatch(cloneTemplate(payload))}
            deleteTemplate={(payload) => dispatch(deleteTemplate(payload))}
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
          aria-label={showMoreLabel}
        >
          {showMoreLabel}
        </button>
      )}
    </>
  );
}
