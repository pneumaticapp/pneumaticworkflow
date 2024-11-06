/* eslint-disable jsx-a11y/control-has-associated-label */
import React, { useState, useEffect } from 'react';
import classnames from 'classnames';

import { LogoCircle, LogoWide, UserIcon } from '../../components/icons';
import { Header } from '../../components/UI';
import { history } from '../../utils/history';
import { ERoutes } from '../../constants/routes';
import { IPages } from '../../types/page';

import styles from './UserLayout.css';

export function UserLayout({ children, pages }: IUserLayoutProps) {
  const { pathname } = history.location;
  const [titleState, setTitle] = useState<string | null>(null);
  const [descriptionState, setDescription] = useState<string | null>(null);

  useEffect(() => {
    const slug = SLUG_PAGES_MAP[pathname as ERoutes];
    const page = pages.find((item) => item.slug === slug);

    if (page) {
      setTitle(page.title);
      setDescription(page.description);
    }
  }, [pages, pathname]);

  return (
    <div className={styles['container']}>
      <div className={styles['info']}>
        <div className={styles['info__inner']}>
          {!titleState && !descriptionState && (
            <LogoWide className={classnames(styles['info__logo'], styles['is-empty'])} />
          )}

          {titleState && (
            <>
              <a href="https://www.pneumatic.app/" target="_blank" rel="noreferrer">
                <LogoCircle className={styles['info__logo']} />
              </a>
              <Header tag="h1" size="xl" className={styles['info__title']}>
                {titleState}
              </Header>
            </>
          )}
          {descriptionState && (
            <>
              <div className={styles['info__divider']}>
                <hr />
              </div>
              <p className={styles['info__description']}>{descriptionState}</p>
            </>
          )}
          {(titleState || descriptionState) && (
            <div className={styles['info__user']}>
              <UserIcon />
            </div>
          )}
        </div>
      </div>
      <div className={styles['content']}>
        <div className={styles['card']}>
          <div className={styles['card__inner']}>{children}</div>
        </div>
      </div>
    </div>
  );
}

export interface IUserLayoutProps {
  pages: IPages;
  children?: React.ReactNode;
}

const SLUG_PAGES_MAP: { [key in ERoutes]?: string } = {
  [ERoutes.Register]: 'signup',
  [ERoutes.Login]: 'signin',
  [ERoutes.SignUpInvite]: 'signup-by-invite',
  [ERoutes.ResetPassword]: 'reset-password',
  [ERoutes.ForgotPassword]: 'forgot-password',
};
