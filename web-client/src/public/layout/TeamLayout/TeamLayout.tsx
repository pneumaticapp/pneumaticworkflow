import React, { useEffect } from 'react';
import { useIntl } from 'react-intl';
import { matchPath } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';

import { IApplicationState } from '../../types/redux';
import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { checkSomeRouteIsActive, history } from '../../utils/history';
import { GroupListSortingContainer } from './GroupListSortingContainer';
import { UserListSortingContainer } from './UserListSortingContainer';
import { ReturnLink, Tabs } from '../../components/UI';
import { ETeamPages } from '../../types/team';
import { resetUsers, setTeamActivePage, updateTeamActiveTab } from '../../redux/actions';

import styles from './TeamLayout.css';

export interface ITeamLayoutProps {
  children: React.ReactNode;
}

export function TeamLayout({ children }: ITeamLayoutProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const page = useSelector((state: IApplicationState) => state.teamInvites.page);

  useEffect(() => {
    dispatch(
      updateTeamActiveTab(
        checkSomeRouteIsActive(ERoutes.Groups) || checkSomeRouteIsActive(ERoutes.GroupDetails)
          ? ETeamPages.Groups
          : ETeamPages.Users,
      ),
    );

    return () => {
      dispatch(resetUsers());
    };
  }, []);

  const renderTeamLeftContent = () => {
    return (
      <div className={styles['top-nav']}>
        <div className={styles['top-nav__item']}>
          <Tabs
            values={[
              { id: ETeamPages.Users, label: formatMessage({ id: 'team.users' }) },
              { id: ETeamPages.Groups, label: formatMessage({ id: 'team.groups' }) },
            ]}
            activeValueId={page}
            onChange={(activeTab) => dispatch(setTeamActivePage(activeTab))}
          />
        </div>
        <div className={styles['top-nav__item']}>
          {page === ETeamPages.Users ? <UserListSortingContainer /> : <GroupListSortingContainer />}
        </div>
      </div>
    );
  };

  const renderGroupDetailsLeftContent = () => {
    return <ReturnLink label={formatMessage({ id: 'menu.groups' })} route={ERoutes.Groups} />;
  };

  const mapLeftContent: Partial<Record<ERoutes, React.ReactNode>> = {
    [ERoutes.GroupDetails]: renderGroupDetailsLeftContent(),
    [ERoutes.Groups]: renderTeamLeftContent(),
    [ERoutes.Team]: renderTeamLeftContent(),
  };

  const leftContent = () => {
    const { pathname } = history.location;
    const currentRoute = Object.keys(mapLeftContent).find((route) => matchPath(pathname, route)) as ERoutes;
    return mapLeftContent[currentRoute];
  };

  return (
    <>
      <TopNavContainer leftContent={leftContent()} />
      <main>
        <div className="container-fluid">{children}</div>
      </main>
    </>
  );
}
