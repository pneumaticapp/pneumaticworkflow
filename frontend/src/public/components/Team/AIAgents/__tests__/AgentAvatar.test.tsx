import React from 'react';
import { render } from '@testing-library/react';

import { AgentAvatar } from '../AgentAvatar';
import { getBackgroundColor } from '../../../UI/Avatar';

describe('AgentAvatar', () => {
  it('renders the photo when the agent has one', () => {
    const { container } = render(
      <AgentAvatar name="Research assistant" photo="https://files.example.com/a.png" size="md" />,
    );

    expect(container.querySelector('img')).toHaveAttribute('src', 'https://files.example.com/a.png');
    expect(container).not.toHaveTextContent('RA');
  });

  it('renders the initials on a name-based color like user avatars', () => {
    const { container } = render(<AgentAvatar name="Research assistant" photo={null} size="lg" />);
    const avatar = container.firstElementChild as HTMLElement;

    expect(container.querySelector('img')).not.toBeInTheDocument();
    expect(container).toHaveTextContent('RA');
    expect(avatar.className).toContain('agent-avatar_lg');
    expect(avatar).toHaveStyle({ backgroundColor: getBackgroundColor('Research assistant') });
  });

  it('renders an empty neutral avatar until the name is typed', () => {
    const { container } = render(<AgentAvatar name="  " size="lg" />);
    const avatar = container.firstElementChild as HTMLElement;

    expect(avatar.className).toContain('agent-avatar_empty');
    expect(avatar.style.backgroundColor).toBe('');
  });
});
