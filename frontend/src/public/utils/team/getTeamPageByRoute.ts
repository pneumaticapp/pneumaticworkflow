import { checkSomeRouteIsActive } from '../history';
import { ERoutes } from '../../constants/routes';
import { TeamPages } from '../../redux/team/types';

export const getTeamPageByRoute = () => {
  if (checkSomeRouteIsActive(ERoutes.Groups, ERoutes.GroupDetails)) return TeamPages.Groups;
  if (checkSomeRouteIsActive(ERoutes.AIAgents)) return TeamPages.AIAgents;

  return TeamPages.Users;
};
