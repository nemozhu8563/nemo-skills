import { describe, expect, it } from 'bun:test';
import { getTemplate, listTemplates } from './styles.js';

describe('Template Styles', () => {
  it('gets default template', () => {
    const template = getTemplate();
    expect(template).toBeTruthy();
    expect(template.css).toBeTruthy();
    expect(template.name).toBeTruthy();
  });

  it('gets specific template', () => {
    const template = getTemplate('template-tech');
    expect(template.name).toBe('科技蓝');
    expect(template.css).toContain('#0066cc');
  });

  it('falls back to default for invalid template', () => {
    const template = getTemplate('invalid-template');
    expect(template.name).toBe('科技蓝');
  });

  it('lists all templates', () => {
    const templates = listTemplates();
    expect(templates.length).toBeGreaterThanOrEqual(8);
    expect(templates.some(t => t.id === 'template-tech')).toBe(true);
  });
});
