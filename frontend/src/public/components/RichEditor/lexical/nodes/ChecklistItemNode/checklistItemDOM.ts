import { CHECKBOX_CLASS } from './constants';

import checkboxStyles from '../../../../UI/Fields/Checkbox/Checkbox.css';



export function createCheckboxElement(): HTMLDivElement {
  const container = document.createElement('div');
  container.className = `${checkboxStyles['checkbox__container']} ${CHECKBOX_CLASS}`;
  container.setAttribute('contenteditable', 'false');
  container.setAttribute('tabindex', '-1');

  const label = document.createElement('label');
  label.className = checkboxStyles['checkbox'];

  const input = document.createElement('input');
  input.type = 'checkbox';
  input.className = checkboxStyles['checkbox__input'];
  input.checked = false;

  const box = document.createElement('div');
  box.className = `${checkboxStyles['checkbox__box']} ${checkboxStyles['checkbox__box--has-margin']}`;

  label.append(input, box);
  container.appendChild(label);
  return container;
}
