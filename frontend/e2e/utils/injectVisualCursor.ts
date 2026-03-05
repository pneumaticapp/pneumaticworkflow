import { Page } from '@playwright/test';

export async function injectVisualCursor(page: Page): Promise<void> {
  await page.evaluate(() => {
    const style = document.createElement('style');
    style.textContent = `
      .pw-cursor {
        position: fixed !important; z-index: 999999 !important;
        width: 28px; height: 28px;
        background: rgba(255, 50, 50, 0.6);
        border: 3px solid red;
        border-radius: 50%;
        pointer-events: none;
        transform: translate(-50%, -50%);
        transition: transform 0.08s, background 0.08s;
      }
      .pw-cursor.click {
        transform: translate(-50%, -50%) scale(0.5) !important;
        background: rgba(255, 165, 0, 0.9) !important;
      }
    `;
    document.head.appendChild(style);

    const cursor = document.createElement('div');
    cursor.className = 'pw-cursor';
    cursor.style.left = '0px';
    cursor.style.top = '0px';
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
      cursor.style.left = e.clientX + 'px';
      cursor.style.top = e.clientY + 'px';
    });
    document.addEventListener('mousedown', () => cursor.classList.add('click'));
    document.addEventListener('mouseup', () => cursor.classList.remove('click'));
  });
}
