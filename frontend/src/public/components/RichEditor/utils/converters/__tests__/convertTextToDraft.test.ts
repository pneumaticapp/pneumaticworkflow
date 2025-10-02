/* eslint-disable */
/* prettier-ignore */
import { convertTextToDraft } from '..';
import { EExtraFieldType } from '../../../../../types/template';

describe('convertTextToDraft', () => {
  it('converts markdown with variables to draft correctly', () => {
    const text = '**Test! The variable value is** {{field-493af8}}';
    const variables = [
      {
        title: 'Haha',
        subtitle: 'Subtitle',
        richSubtitle: '',
        apiName: 'field-493af8',
        type: EExtraFieldType.String,
      },
    ];

    const conversionResult = convertTextToDraft(text, variables, true);

    expect(conversionResult.blocks[0].text).toEqual('Test! The variable value is Haha');

    const blockOneKey = conversionResult.blocks[0].entityRanges[0].key;
    expect(conversionResult.entityMap[blockOneKey].type).toEqual('variable');
    expect(conversionResult.blocks[0].entityRanges[0].offset).toEqual(28);
    expect(conversionResult.blocks[0].entityRanges[0].length).toEqual(4);
    expect(conversionResult.entityMap[blockOneKey].data.apiName).toEqual('field-493af8');
    expect(conversionResult.entityMap[blockOneKey].data.title).toEqual('Haha');
    expect(conversionResult.entityMap[blockOneKey].data.subtitle).toEqual('Subtitle');
  });
  it('converts markdown with image correctly', () => {
    const text = '![1.jpg](https://storage.googleapis.com/pneumatic-bucket-dev/ijYwaYIljdRJuPbjxa5RUxvQEg2JV8_1.jpg)';

    const conversionResult = convertTextToDraft(text, [], true);

    expect(conversionResult.blocks[0].text).toEqual(' ');

    const blockOneKey = conversionResult.blocks[0].entityRanges[0].key;
    expect(conversionResult.entityMap[blockOneKey].type).toEqual('image');
  });
});
