import * as React from 'react';
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useIntl } from 'react-intl';
import classnames from 'classnames';
import { RouteComponentProps } from 'react-router-dom';

import InfiniteScroll from 'react-infinite-scroll-component';
import { IFieldsetListItem } from '../../types/fieldset';

import { PageTitle } from '../PageTitle';
import { EPageTitle } from '../../constants/defaultValues';
import { openCreateModal, loadFieldsets, setTemplateId } from '../../redux/fieldsets/slice';
import { getFieldsetsListSelection, getFieldsetsIsLoading, getFieldsetsSorting } from '../../redux/selectors/fieldsets';
import { AddCardButton } from '../UI';
import { AIPlusIcon } from '../icons';
import { FieldsetModal } from './FieldsetModal/FieldsetModal';
import { EFieldsetModalType } from './FieldsetModal/types';
import { FieldsetCard } from './FieldsetCard';

import styles from './Fieldsets.css';

interface IFieldsetsRouteParams {
  templateId: string;
}

type TFieldsetsProps = RouteComponentProps<IFieldsetsRouteParams>;

export function Fieldsets({ match }: TFieldsetsProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const numericTemplateId = Number(match.params.templateId);

  const { items: fieldsetsList, count, offset } = useSelector(getFieldsetsListSelection) || { items: [], count: 0, offset: 0 };
  const isLoading = useSelector(getFieldsetsIsLoading);
  const fieldsetsSorting = useSelector(getFieldsetsSorting);

  useEffect(() => {
    if (numericTemplateId) {
      dispatch(setTemplateId(numericTemplateId));
      dispatch(loadFieldsets({ offset: 0, templateId: numericTemplateId }));
    }
  }, [dispatch, fieldsetsSorting, numericTemplateId]);

  const handleOpenCreateModal = () => {
    dispatch(openCreateModal());
  };

  return (
    <div className={styles['container']}>
      <PageTitle titleId={EPageTitle.Fieldsets} withUnderline={false} />
      <InfiniteScroll
        dataLength={fieldsetsList.length}
        next={() => dispatch(loadFieldsets({ offset: offset + 1, templateId: numericTemplateId }))}
        loader={null}
        hasMore={count > fieldsetsList.length || isLoading}
        className={classnames(styles['cards-wrapper'], { [styles['container-loading']]: isLoading })}
        scrollableTarget="app-container"
      >
        {isLoading && fieldsetsList.length === 0 && <div className="loading" />}
        <AddCardButton
          className={styles['card']}
          onClick={handleOpenCreateModal}
          title={formatMessage({ id: 'fieldsets.new-fieldset.title' })}
          caption={formatMessage({ id: 'fieldsets.new-fieldset.caption' })}
          icon={<AIPlusIcon />}
        />
        {fieldsetsList.map((fieldset: IFieldsetListItem) => (
          <FieldsetCard key={fieldset.id} {...fieldset} templateId={numericTemplateId} />
        ))}
      </InfiniteScroll>
      <FieldsetModal type={EFieldsetModalType.Create} templateId={numericTemplateId} />
      <FieldsetModal type={EFieldsetModalType.Edit} />
    </div>
  );
}

export default Fieldsets;
