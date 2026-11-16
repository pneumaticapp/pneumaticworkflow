import * as React from 'react';
import { render } from '@testing-library/react';
import { useDispatch, useSelector } from 'react-redux';
import { Location } from 'history';

import { TemplateLeavingGuard } from '../TemplateLeavingGuard';
import { ERoutes } from '../../../../constants/routes';
import { ITemplateClient } from '../../../../types/template';

interface IGuardProps {
  when: boolean;
  shouldBlockNavigation(location: Location): boolean;
}

const guardProps: { current: IGuardProps | null } = { current: null };

jest.mock('../../../UI', () => ({
  Button: () => null,
  RouteLeavingGuard: (props: IGuardProps) => {
    guardProps.current = props;

    return null;
  },
}));

jest.mock('../../InfoWarningsModal', () => ({
  InfoWarningsModal: () => null,
}));

const mockTemplate = (overrides: Partial<ITemplateClient> = {}): ITemplateClient =>
  ({
    id: 42,
    name: 'Draft template',
    isActive: false,
    owners: [],
    kickoff: { description: '', fields: [], fieldsets: [] },
    tasks: [],
    ...overrides,
  }) as ITemplateClient;

const renderGuard = (template: ITemplateClient, isTemplateDeleted = false) => {
  (useDispatch as jest.Mock).mockReturnValue(jest.fn());
  (useSelector as jest.Mock).mockImplementation((selector: (state: unknown) => unknown) =>
    selector({
      template: { data: template },
      authUser: { account: { isSubscribed: false, billingPlan: 'free' } },
    }),
  );

  return render(<TemplateLeavingGuard isTemplateDeleted={isTemplateDeleted} />);
};

describe('TemplateLeavingGuard', () => {
  beforeEach(() => {
    guardProps.current = null;
    jest.clearAllMocks();
  });

  it('should guard an unsaved draft regardless of the active editor view', () => {
    renderGuard(mockTemplate());

    expect(guardProps.current?.when).toBe(true);
  });

  it('should stop guarding once the template is deleted', () => {
    renderGuard(mockTemplate(), true);

    expect(guardProps.current?.when).toBe(false);
  });

  it('should stop guarding an active template', () => {
    renderGuard(mockTemplate({ isActive: true }));

    expect(guardProps.current?.when).toBe(false);
  });

  it('should not render for a template that has never been saved', () => {
    renderGuard(mockTemplate({ id: undefined }));

    expect(guardProps.current).toBeNull();
  });

  it('should block navigation outside the template routes only', () => {
    renderGuard(mockTemplate());

    expect(guardProps.current?.shouldBlockNavigation({ pathname: ERoutes.Workflows } as Location)).toBe(true);
    expect(guardProps.current?.shouldBlockNavigation({ pathname: '/templates/edit/42/' } as Location)).toBe(false);
  });
});
