// <reference types="jest" />
import { escapeMarkdown } from '../escapeMarkdown';

describe('escapeMarkdown', () => {
  describe('plain text without special characters', () => {
    it('returns empty string for no arguments', () => {
      expect(escapeMarkdown()).toBe('');
    });

    it('returns empty string for empty string', () => {
      expect(escapeMarkdown('')).toBe('');
    });

    it('preserves plain text without special characters', () => {
      expect(escapeMarkdown('Hello world')).toBe('Hello world');
    });

    it('preserves numbers', () => {
      expect(escapeMarkdown('Order 12345')).toBe('Order 12345');
    });

    it('preserves whitespace and newlines', () => {
      expect(escapeMarkdown('  spaced  out  ')).toBe('  spaced  out  ');
      expect(escapeMarkdown('line1\nline2')).toBe('line1\nline2');
    });
  });

  describe('dashes are NOT escaped (bug fix)', () => {
    it('does not escape dashes in plain text', () => {
      expect(escapeMarkdown('a-b')).toBe('a-b');
      expect(escapeMarkdown('one-two-three')).toBe('one-two-three');
      expect(escapeMarkdown('-')).toBe('-');
      expect(escapeMarkdown('---')).toBe('---');
    });

    it('does not escape dash between variables', () => {
      expect(escapeMarkdown('{{date}}-{{template-name}}')).toBe('{{date}}-{{template-name}}');
    });

    it('does not escape dash with spaces around', () => {
      expect(escapeMarkdown('value - another')).toBe('value - another');
    });

    it('does not escape em-dash', () => {
      expect(escapeMarkdown('word — word')).toBe('word — word');
    });
  });

  describe('variable preservation', () => {
    it('preserves a single variable', () => {
      expect(escapeMarkdown('{{date}}')).toBe('{{date}}');
    });

    it('preserves variable with dashes in api-name', () => {
      expect(escapeMarkdown('{{template-name}}')).toBe('{{template-name}}');
    });

    it('preserves variable with alphanumeric api-name', () => {
      expect(escapeMarkdown('{{field-8d287d}}')).toBe('{{field-8d287d}}');
    });

    it('preserves variable with spaces inside braces', () => {
      expect(escapeMarkdown('{{ date }}')).toBe('{{ date }}');
    });

    it('preserves multiple variables', () => {
      expect(escapeMarkdown('{{date}} {{template-name}}')).toBe('{{date}} {{template-name}}');
    });

    it('preserves many variables in a row', () => {
      const input = '{{a}}{{b}}{{c}}{{d}}';
      expect(escapeMarkdown(input)).toBe(input);
    });

    it('preserves variables with text between them', () => {
      expect(escapeMarkdown('Start {{date}} middle {{name}} end')).toBe('Start {{date}} middle {{name}} end');
    });

    it('preserves workflow-id variable', () => {
      expect(escapeMarkdown('{{workflow-id}}')).toBe('{{workflow-id}}');
    });

    it('preserves workflow-starter variable', () => {
      expect(escapeMarkdown('{{workflow-starter}}')).toBe('{{workflow-starter}}');
    });
  });

  describe('markdown special characters escaping', () => {
    const cases: [string, string, string][] = [
      ['backslash', 'a\\b', 'a\\\\b'],
      ['backtick', 'a`b', 'a\\`b'],
      ['asterisk', 'a*b', 'a\\*b'],
      ['underscore', 'a_b', 'a\\_b'],
      ['square brackets', 'a[b]c', 'a\\[b\\]c'],
      ['curly braces outside variables', 'a{b}c', 'a\\{b\\}c'],
      ['parentheses', 'a(b)c', 'a\\(b\\)c'],
      ['hash', 'a#b', 'a\\#b'],
      ['plus', 'a+b', 'a\\+b'],
      ['dot', 'a.b', 'a\\.b'],
      ['exclamation mark', 'a!b', 'a\\!b'],
      ['pipe', 'a|b', 'a\\|b'],
      ['tilde', 'a~b', 'a\\~b'],
      ['colon', 'a:b', 'a\\:b'],
      ['double quote', 'a"b', 'a\\"b'],
      ['single quote', "a'b", "a\\'b"],
      ['ampersand', 'a&b', 'a\\&b'],
      ['percent', 'a%b', 'a\\%b'],
      ['equals', 'a=b', 'a\\=b'],
    ];

    test.each(cases)('escapes %s: %s -> %s', (_label, input, expected) => {
      expect(escapeMarkdown(input)).toBe(expected);
    });

    it('escapes multiple special characters in a row', () => {
      expect(escapeMarkdown('**bold**')).toBe('\\*\\*bold\\*\\*');
    });

    it('escapes mixed special characters', () => {
      expect(escapeMarkdown('_italic_ and **bold**')).toBe('\\_italic\\_ and \\*\\*bold\\*\\*');
    });
  });

  describe('combined: variables + dashes + special characters', () => {
    it('real-world wf_name_template with dashes between variables', () => {
      const input = '{{date}} — {{template-name}}-{{field-8d287d}} -{{workflow-id}}';
      expect(escapeMarkdown(input)).toBe('{{date}} — {{template-name}}-{{field-8d287d}} -{{workflow-id}}');
    });

    it('variable followed by dash and text', () => {
      expect(escapeMarkdown('{{date}}-report')).toBe('{{date}}-report');
    });

    it('text with dash followed by variable', () => {
      expect(escapeMarkdown('report-{{date}}')).toBe('report-{{date}}');
    });

    it('variable with special characters around it', () => {
      expect(escapeMarkdown('**{{date}}**')).toBe('\\*\\*{{date}}\\*\\*');
    });

    it('complex template with dashes and special chars', () => {
      const input = '{{date}} — {{template-name}} (v1.0) #{{workflow-id}}';
      const expected = '{{date}} — {{template-name}} \\(v1\\.0\\) \\#{{workflow-id}}';
      expect(escapeMarkdown(input)).toBe(expected);
    });

    it('multiple dashes and variables mixed', () => {
      const input = '{{a}}-{{b}}-{{c}}';
      expect(escapeMarkdown(input)).toBe('{{a}}-{{b}}-{{c}}');
    });

    it('preserves dash in text between two variables with spaces', () => {
      const input = '{{date}} - {{name}}';
      expect(escapeMarkdown(input)).toBe('{{date}} - {{name}}');
    });

    it('template name with underscores gets escaped but variables preserved', () => {
      const input = '{{date}}_{{template-name}}';
      expect(escapeMarkdown(input)).toBe('{{date}}\\_{{template-name}}');
    });
  });

  describe('edge cases', () => {
    it('handles single curly brace (not a variable)', () => {
      expect(escapeMarkdown('{not a var}')).toBe('\\{not a var\\}');
    });

    it('handles triple curly braces', () => {
      expect(escapeMarkdown('{{{var}}}')).toBe('\\{{{var}}\\}');
    });

    it('handles empty variable name', () => {
      expect(escapeMarkdown('{{}}')).toBe('\\{\\{\\}\\}');
    });

    it('handles text that looks like placeholder pattern __VAR_0__', () => {
      const input = '__VAR_0__ some text';
      expect(escapeMarkdown(input)).toBe('\\_\\_VAR\\_0\\_\\_ some text');
    });

    it('handles very long text without escaping dashes', () => {
      const longText = 'a-b '.repeat(1000);
      expect(escapeMarkdown(longText)).toBe(longText);
    });

    it('handles unicode characters', () => {
      expect(escapeMarkdown('Привет-мир')).toBe('Привет-мир');
    });

    it('handles emoji', () => {
      expect(escapeMarkdown('🚀-launch')).toBe('🚀-launch');
    });

    it('preserves tab characters', () => {
      expect(escapeMarkdown('col1\tcol2')).toBe('col1\tcol2');
    });
  });

  describe('idempotency concerns', () => {
    it('double-escaping: already escaped backslash gets double-escaped', () => {
      expect(escapeMarkdown('a\\-b')).toBe('a\\\\-b');
    });

    it('double call produces double escaping for special chars', () => {
      const once = escapeMarkdown('a*b');
      const twice = escapeMarkdown(once);
      expect(once).toBe('a\\*b');
      expect(twice).toBe('a\\\\\\*b');
    });

    it('double call does NOT double-escape dashes', () => {
      const once = escapeMarkdown('a-b');
      const twice = escapeMarkdown(once);
      expect(once).toBe('a-b');
      expect(twice).toBe('a-b');
    });

    it('double call preserves variables both times', () => {
      const once = escapeMarkdown('{{date}}-{{name}}');
      const twice = escapeMarkdown(once);
      expect(once).toBe('{{date}}-{{name}}');
      expect(twice).toBe('{{date}}-{{name}}');
    });
  });
});
