import React from 'react';
import { Link } from 'react-router-dom';
import classNames from 'classnames';

import { ISystemTemplate } from '../../../types/template';
import { sanitizeText } from '../../../utils/strings';
import { ERoutes } from '../../../constants/routes';

import styles from '../Templates.css';

export interface ITemplateSystemCardProps extends ISystemTemplate {
  color?: string;
  icon?: string;
}

export const TemplateSystemCard = ({ id, name, color, description, icon }: ITemplateSystemCardProps) => {
  const route = `${ERoutes.TemplatesCreate}?template=${id}`;
  const cardBackground = { background: color || 'white' };

  return (
    <Link className={classNames(styles['card'], styles['is-system'])} key={id} to={route}>
      <div className={styles['card__content']} style={cardBackground}>
        <div className={styles['card__header']}>
          <div className={styles['card__title']}>{sanitizeText(name)}</div>
        </div>
        <p className={styles['card__description']}>{description}</p>
        {icon && (
          <div className={styles['card__footer']}>
            <div className={styles['card__icon']}>
              <img src={icon} alt={name} />
            </div>
          </div>
        )}
      </div>
    </Link>
  );
};
