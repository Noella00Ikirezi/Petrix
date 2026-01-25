/**
 * Markdown ↔ HTML conversion utilities
 * Used by the WYSIWYG editor to convert between formats
 */

import Showdown from 'showdown';
import TurndownService from 'turndown';

// Configure Showdown (Markdown → HTML)
const showdownConverter = new Showdown.Converter({
  tables: true,
  strikethrough: true,
  tasklists: true,
  ghCodeBlocks: true,
  smoothLivePreview: true,
  simpleLineBreaks: false,
  openLinksInNewWindow: true,
  emoji: false,
  underline: true,
  headerLevelStart: 1,
});

// Configure Turndown (HTML → Markdown)
const turndownService = new TurndownService({
  headingStyle: 'atx',
  hr: '---',
  bulletListMarker: '-',
  codeBlockStyle: 'fenced',
  emDelimiter: '*',
  strongDelimiter: '**',
});

// Add table support to Turndown
turndownService.addRule('table', {
  filter: 'table',
  replacement: function (content, node) {
    const table = node as HTMLTableElement;
    const rows: string[][] = [];

    // Get all rows
    const tableRows = table.querySelectorAll('tr');
    tableRows.forEach((row) => {
      const cells: string[] = [];
      row.querySelectorAll('th, td').forEach((cell) => {
        cells.push(cell.textContent?.trim() || '');
      });
      if (cells.length > 0) {
        rows.push(cells);
      }
    });

    if (rows.length === 0) return '';

    // Build markdown table
    const colCount = Math.max(...rows.map(r => r.length));
    let markdown = '';

    rows.forEach((row, index) => {
      // Pad row to have consistent columns
      while (row.length < colCount) {
        row.push('');
      }
      markdown += '| ' + row.join(' | ') + ' |\n';

      // Add separator after header row
      if (index === 0) {
        markdown += '|' + row.map(() => '---').join('|') + '|\n';
      }
    });

    return '\n' + markdown + '\n';
  }
});

// Handle horizontal rules
turndownService.addRule('hr', {
  filter: 'hr',
  replacement: function () {
    return '\n---\n';
  }
});

// Handle underline (custom extension)
turndownService.addRule('underline', {
  filter: 'u',
  replacement: function (content) {
    return '__' + content + '__';
  }
});

// Handle highlighted text
turndownService.addRule('mark', {
  filter: 'mark',
  replacement: function (content) {
    return '==' + content + '==';
  }
});

/**
 * Convert Markdown to HTML for the WYSIWYG editor
 */
export function markdownToHtml(markdown: string): string {
  if (!markdown) return '';

  // Pre-process: handle YAML frontmatter
  let content = markdown;
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (frontmatterMatch) {
    content = content.replace(frontmatterMatch[0], '').trim();
  }

  // Convert markdown to HTML
  let html = showdownConverter.makeHtml(content);

  return html;
}

/**
 * Convert HTML from the WYSIWYG editor back to Markdown
 */
export function htmlToMarkdown(html: string): string {
  if (!html) return '';

  // Clean up HTML before conversion
  let cleanHtml = html
    // Remove empty paragraphs
    .replace(/<p>\s*<\/p>/g, '')
    // Normalize line breaks
    .replace(/<br\s*\/?>/g, '\n')
    // Handle TipTap specific markup
    .replace(/<p><\/p>/g, '\n');

  // Convert HTML to Markdown
  let markdown = turndownService.turndown(cleanHtml);

  // Post-process: clean up extra whitespace
  markdown = markdown
    // Remove excessive blank lines
    .replace(/\n{3,}/g, '\n\n')
    // Ensure proper spacing around headers
    .replace(/\n(#{1,6})/g, '\n\n$1')
    // Clean up table formatting
    .replace(/\|\n\n\|/g, '|\n|')
    .trim();

  return markdown;
}

/**
 * Check if content appears to be HTML
 */
export function isHtml(content: string): boolean {
  return /<[a-z][\s\S]*>/i.test(content);
}

/**
 * Smart convert: detects format and converts appropriately
 */
export function convertForEditor(content: string): string {
  if (!content) return '';

  // If it's already HTML, return as-is
  if (isHtml(content)) {
    return content;
  }

  // Otherwise convert from Markdown to HTML
  return markdownToHtml(content);
}

/**
 * Convert editor content back to storage format (Markdown)
 */
export function convertForStorage(editorHtml: string): string {
  if (!editorHtml) return '';

  return htmlToMarkdown(editorHtml);
}
