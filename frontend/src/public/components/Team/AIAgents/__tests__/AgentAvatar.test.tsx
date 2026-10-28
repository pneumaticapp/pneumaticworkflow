import * as React from 'react';
import { render } from '@testing-library/react';

import { AgentAvatar } from '../AgentAvatar';

describe('AgentAvatar', () => {
  it('renders the photo when the agent has one', () => {
    const { container } = render(
      <AgentAvatar name="Research assistant" photo="https://files.example.com/a.png" size="md" />,
    );

    expect(container.querySelector('img')).toHaveAttribute('src', 'https://files.example.com/a.png');
    expect(container).not.toHaveTextContent('RA');
  });

  it('renders the initials without a photo', () => {
    const { container } = render(<AgentAvatar name="Research assistant" photo={null} size="lg" />);

    expect(container.querySelector('img')).not.toBeInTheDocument();
    expect(container).toHaveTextContent('RA');
    expect(container.firstElementChild?.className).toContain('agent-avatar_lg');
  });
});
