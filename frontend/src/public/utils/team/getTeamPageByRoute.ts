import { checkSomeRouteIsActive } from '../history';
import { ERoutes } from '../../constants/routes';
import { ETeamPages } from '../../redux/team/types';

export const getTeamPageByRoute = () => {
  if (checkSomeRouteIsActive(ERoutes.Groups, ERoutes.GroupDetails)) return ETeamPages.Groups;
  if (checkSomeRouteIsActive(ERoutes.AIAgents)) return ETeamPages.AIAgents;

  return ETeamPages.Users;
};
