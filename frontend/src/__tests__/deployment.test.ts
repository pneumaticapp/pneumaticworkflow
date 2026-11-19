import deployment from '../../pm2.json';

describe('frontend deployment', () => {
  it('starts in production when no PM2 environment is selected', () => {
    expect(deployment.env.NODE_ENV).toBe('production');
  });

  it('keeps development available through an explicit PM2 environment', () => {
    expect(deployment.env_development.NODE_ENV).toBe('development');
  });
});
