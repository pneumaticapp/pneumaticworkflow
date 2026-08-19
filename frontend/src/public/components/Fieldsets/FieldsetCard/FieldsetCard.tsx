import * as React from 'react';
import { useDispatch } from 'react-redux';
import { useIntl } from 'react-intl';
import classnames from 'classnames';

import { ModifyDropdown } from '../../UI';
import { EModifyDropdownToggle } from '../../UI/ModifyDropdown/types';

import { openEditModal, deleteFieldsetAction, cloneFieldsetAction, setCurrentFieldset } from '../../../redux/fieldsets/slice';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';
import { sanitizeText } from '../../../utils/strings';
import { IFieldsetCatalogItem } from '../../../types/fieldset';

import styles from './FieldsetCard.css';

export function FieldsetCard({
  id,
  apiName,
  name,
  description,
  labelPosition,
  layout,
  order,
  title,
  rules,
  fields,
  usage,
}: IFieldsetCatalogItem) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();



  const handleEditName = () => {
    dispatch(setCurrentFieldset({
      id,
      apiName,
      name,
      description,
      labelPosition,
      layout,
      order,
      title,
      rules,
      fields,
      usage,
    }));
    dispatch(openEditModal());
  };

  const handleCardClick = () => {
    history.push(
      ERoutes.FieldsetDetail
        .replace(':id', id.toString()),
    );
  };

  const handleCloneFieldset = () => {
    dispatch(cloneFieldsetAction({ id }));
  };

  const isLinked = Boolean(usage && usage.length > 0);
  const hasContent = fields.length > 0 || rules.length > 0;

  return (
    <div className={styles['card']} key={id}>


      <div className={styles['card__content']}>
        <div className={styles['card__header']}>
          <div
            className={styles['card__title']}
            onClick={handleCardClick}
            onKeyDown={(e) => e.key === 'Enter' && handleCardClick()}
            role="link"
            tabIndex={0}
          >
            {sanitizeText(name)}
          </div>

          <ModifyDropdown
            onEdit={handleEditName}
            onClone={handleCloneFieldset}
            onDelete={() => dispatch(deleteFieldsetAction({ id }))}
            editLabel={formatMessage({ id: 'fieldsets.edit' })}
            cloneLabel={formatMessage({ id: 'fieldsets.clone' })}
            deleteLabel={formatMessage({ id: 'fieldsets.delete' })}
            isReadOnly={isLinked}
            toggleType={EModifyDropdownToggle.More}
            className={styles['card__more']}
          />
        </div>

        {hasContent && (
          <div className={styles['card__footer']}>
            {fields.length > 0 && (
              <div className={classnames(styles['card-stats'], styles['card-stats--items'])}>
                {formatMessage(
                  { id: 'fieldsets.stats.fields' },
                  { count: fields.length },
                )}
              </div>
            )}
            {rules.length > 0 && (
              <div className={classnames(styles['card-stats'], styles['card-stats--rules'])}>
                {formatMessage(
                  { id: 'fieldsets.stats.rules' },
                  { count: rules.length },
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
