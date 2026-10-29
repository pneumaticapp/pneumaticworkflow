import { getAgentCloneName } from '../utils/getAgentCloneName';

describe('getAgentCloneName', () => {
  it('appends the clone suffix', () => {
    expect(getAgentCloneName('Researcher', 'Clone', ['Researcher'])).toBe('Researcher (Clone)');
  });

  it('numbers the clone when the plain clone name is taken', () => {
    expect(getAgentCloneName('Researcher', 'Clone', ['Researcher', 'researcher (clone)', 'Researcher (Clone 2)'])).toBe(
      'Researcher (Clone 3)',
    );
  });
});
