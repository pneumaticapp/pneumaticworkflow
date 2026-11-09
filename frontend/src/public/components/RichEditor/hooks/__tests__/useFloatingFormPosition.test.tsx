import React from 'react';
import { render, screen } from '@testing-library/react';

import { useFloatingFormPosition } from '../useFloatingFormPosition';

const rect = (left: number, top: number, width: number, height: number): DOMRect =>
  ({ left, top, right: left + width, bottom: top + height, width, height }) as DOMRect;

describe('floating link form coordinate system', () => {
  afterEach(() => jest.restoreAllMocks());

  it('keeps the form centered at its anchor inside an RTL scroller', () => {
    const container = document.createElement('div');
    container.dir = 'rtl';
    jest.spyOn(container, 'getBoundingClientRect').mockReturnValue(rect(100, 80, 400, 300));
    Object.defineProperties(container, {
      clientLeft: { value: 18 },
      clientTop: { value: 2 },
      scrollLeft: { value: -80 },
      scrollTop: { value: 30 },
    });
    const anchor = document.createElement('span');
    jest.spyOn(anchor, 'getBoundingClientRect').mockReturnValue(rect(240, 140, 40, 20));
    const form = document.createElement('div');
    Object.defineProperties(form, { offsetHeight: { value: 30 }, offsetWidth: { value: 160 } });
    const formRef = { current: form };
    const containerRef = { current: container };

    function Probe() {
      const result = useFloatingFormPosition(formRef, {
        anchorElement: anchor,
        containerRef,
        isVisible: true,
        offsetPx: 8,
      });
      return <output data-testid="position">{JSON.stringify(result)}</output>;
    }

    render(<Probe />);
    const result = JSON.parse(screen.getByTestId('position').textContent!);
    expect(result.positionMode).toBe('absolute');
    expect(100 + 18 + result.position.left - container.scrollLeft).toBe(260);
    expect(80 + 2 + result.position.top - container.scrollTop + 30).toBe(132);
  });
});
