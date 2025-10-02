/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';

import { isArrayWithItems } from '../../../utils/helpers';
import { BoldPlusIcon, ModalCloseIcon } from '../../icons';
import { IntlMessages } from '../../IntlMessages';

import styles from './AddEntityButton.css';

export enum EEntityTitle {
  Task = 'task',
  Delay = 'delay',
}

export interface ITemplateEntity {
  previousTaskapiName?: string;
  title: EEntityTitle;
  onAddEntity(previousTaskapiName?: string): void;
}

export interface IAddEntityButtonProps {
  entities: ITemplateEntity[];
}

export function AddEntityButton({ entities }: IAddEntityButtonProps) {
  if (!isArrayWithItems(entities)) {
    return null;
  }
  const [{ onAddEntity, previousTaskapiName }] = entities;
  const { messages } = useIntl();
  const { useCallback, useState } = React;

  const [areOptionsOpened, setAreOptionsOpened] = useState(false);

  const closeOptions = useCallback(() => setAreOptionsOpened(false), [areOptionsOpened]);
  const toggleOptions = useCallback(() => setAreOptionsOpened(!areOptionsOpened), [areOptionsOpened]);

  const handleClickAddButton = () => {
    if (entities.length === 1) {
      onAddEntity(previousTaskapiName);
      closeOptions();

      return;
    }

    toggleOptions();
  };

  const handleAddEntity = (onAddEntity: ITemplateEntity['onAddEntity']) => () => {
    onAddEntity(previousTaskapiName);
    closeOptions();
  };

  const renderAddButton = () => {
    return (
      <button
        type="button"
        aria-label={messages['templates.show-options'] as string}
        className={styles['add-entity-button']}
        onClick={handleClickAddButton}
      >
        <BoldPlusIcon />
      </button>
    );
  };

  const renderEntities = () => {
    return (
      <div className={styles['entities']}>
        <button
          type="button"
          aria-label={messages['templates.hide-options'] as string}
          className={styles['entities-close-button']}
          onClick={closeOptions}
        >
          <ModalCloseIcon />
        </button>

        {entities.map(({ title, onAddEntity }) => (
          <button key={title} type="button" className={styles['entity']} onClick={handleAddEntity(onAddEntity)}>
            <IntlMessages id={`template.add-entity-button-${title}`} />
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className={styles['container']}>
      <div className={styles['inner-wrapper']}>{areOptionsOpened ? renderEntities() : renderAddButton()}</div>
    </div>
  );
}
