import { getTeamPageByRoute } from '../getTeamPageByRoute';
import { history } from '../../history';
import { TeamPages } from '../../../redux/team/types';

describe('getTeamPageByRoute', () => {
  it.each([
    ['/team/groups/', TeamPages.Groups],
    ['/team/groups/5', TeamPages.Groups],
    ['/team/ai-agents/', TeamPages.AIAgents],
    ['/team/', TeamPages.Users],
  ])('maps %s to its tab', (pathname, page) => {
    history.push(pathname);

    expect(getTeamPageByRoute()).toBe(page);
  });
});
