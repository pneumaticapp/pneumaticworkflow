import { Remarkable } from 'remarkable';
import { /*checklistsRemarkablePlugin,*/ checklistsRemarkablePlugin } from '../customMarkdownPlugins';

describe('checklists', () => {
  it('checklists', () => {
    const testData = `[clist:aaa|bbb]First check[/clist]\n[clist:aaa|ccc]\n*Second check*\n[/clist]`;
    const md = new Remarkable().use(checklistsRemarkablePlugin, {});

    const data = md.parse(testData, {});

    expect(data).toStrictEqual([
      {
        type: 'clist_open',
        lines: [0, 1],
        level: 0,
        listApiName: 'aaa',
        itemApiName: 'bbb',
      },
      {
        type: 'inline',
        content: 'First check',
        level: 1,
        lines: [0, 0],
        children: [
          {
            type: 'text',
            content: 'First check',
            level: 0,
          },
        ],
      },
      {
        type: 'clist_close',
        level: 0,
      },
      {
        type: 'clist_open',
        lines: [1, 4],
        level: 0,
        listApiName: 'aaa',
        itemApiName: 'ccc',
      },
      {
        type: 'inline',
        content: '*Second check*',
        level: 1,
        lines: [1, 3],
        children: [
          {
            type: 'em_open',
            level: 0,
          },
          {
            type: 'text',
            content: 'Second check',
            level: 1,
          },
          {
            type: 'em_close',
            level: 0,
          },
        ],
      },
      {
        type: 'clist_close',
        level: 0,
      },
    ]);
  });
});
