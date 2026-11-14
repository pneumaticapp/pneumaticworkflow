import { getTeamPageByRoute } from '../getTeamPageByRoute';
import { history } from '../../history';
import { ETeamPages } from '../../../redux/team/types';

describe('getTeamPageByRoute', () => {
  it.each([
    ['/team/groups/', ETeamPages.Groups],
    ['/team/groups/5', ETeamPages.Groups],
    ['/team/ai-agents/', ETeamPages.AIAgents],
    ['/team/', ETeamPages.Users],
  ])('maps %s to its tab', (pathname, page) => {
    history.push(pathname);

    expect(getTeamPageByRoute()).toBe(page);
  });
});
