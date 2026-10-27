import React, { useEffect } from 'react';
import { useIntl } from 'react-intl';
import { matchPath } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';

import { TopNavContainer } from '../../components/TopNav';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { getTeamPageByRoute } from '../../utils/team/getTeamPageByRoute';
import { GroupListSorting } from './GroupListSorting';
import { UserListSorting } from './UserListSorting';
import { ReturnLink, Tabs } from '../../components/UI';
import { resetUsers } from '../../redux/accounts/slice';
import { TeamPages } from '../../redux/team/types';
import { updateTeamActiveTab, setTeamActivePage } from '../../redux/team/slice';
import { getTeamPage } from '../../redux/selectors/team';

import styles from './TeamLayout.css';

export interface ITeamLayoutProps {
  children: React.ReactNode;
}

export function TeamLayout({ children }: ITeamLayoutProps) {
  const dispatch = useDispatch();
  const { formatMessage } = useIntl();
  const page = useSelector(getTeamPage);

  useEffect(() => {
    dispatch(updateTeamActiveTab(getTeamPageByRoute()));

    return () => {
      dispatch(resetUsers());
    };
  }, [history.location.pathname]);

  const renderTeamLeftContent = () => {
    return (
      <div className={styles['top-nav']}>
        <div className={styles['top-nav__item']}>
          <Tabs
            values={[
              { id: TeamPages.Users, label: formatMessage({ id: 'team.users' }) },
              { id: TeamPages.Groups, label: formatMessage({ id: 'team.groups' }) },
              { id: TeamPages.AIAgents, label: formatMessage({ id: 'team.ai-agents' }) },
            ]}
            activeValueId={page}
            onChange={(activeTab) => dispatch(setTeamActivePage(activeTab))}
          />
        </div>
        {page !== TeamPages.AIAgents && (
          <div className={styles['top-nav__item']}>
            {page === TeamPages.Users ? <UserListSorting /> : <GroupListSorting />}
          </div>
        )}
      </div>
    );
  };

  const renderGroupDetailsLeftContent = () => {
    return <ReturnLink label={formatMessage({ id: 'menu.groups' })} route={ERoutes.Groups} />;
  };

  const mapLeftContent: Partial<Record<ERoutes, React.ReactNode>> = {
    [ERoutes.GroupDetails]: renderGroupDetailsLeftContent(),
    [ERoutes.Groups]: renderTeamLeftContent(),
    [ERoutes.AIAgents]: renderTeamLeftContent(),
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
