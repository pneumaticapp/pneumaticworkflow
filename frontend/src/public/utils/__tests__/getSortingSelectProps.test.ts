import { getSortingSelectProps } from '../getSortingSelectProps';
import { intlMock } from '../../__stubs__/intlMock';
import { ETemplatesSorting } from '../../types/workflow';

describe('getSortingSelectProps', () => {
  const values = [ETemplatesSorting.DateDesc, ETemplatesSorting.NameAsc];

  it('builds localized options and the selected option', () => {
    const { options, value } = getSortingSelectProps(
      values,
      ETemplatesSorting.NameAsc,
      jest.fn(),
      intlMock.formatMessage,
    );

    expect(options).toEqual(
      values.map((sorting) => ({ value: sorting, label: intlMock.formatMessage({ id: `sorting.${sorting}` }) })),
    );
    expect(value).toEqual(options[1]);
  });

  it('reports only a changed value', () => {
    const onChange = jest.fn();
    const props = getSortingSelectProps(values, ETemplatesSorting.DateDesc, onChange, intlMock.formatMessage);

    props.onChange(props.options[0]);
    props.onChange(props.options[1]);

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(ETemplatesSorting.NameAsc);
  });
});
