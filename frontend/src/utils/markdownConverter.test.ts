import { describe, it, expect } from 'vitest'
import {
  markdownToHtml,
  htmlToMarkdown,
  isHtml,
  convertForEditor,
  convertForStorage,
} from './markdownConverter'

describe('markdownToHtml', () => {
  it('converts **bold** to <strong>', () => {
    const result = markdownToHtml('**bold**')
    expect(result).toContain('<strong>bold</strong>')
  })

  it('converts # heading to <h1>', () => {
    const result = markdownToHtml('# heading')
    expect(result).toContain('<h1')
    expect(result).toContain('heading')
    expect(result).toContain('</h1>')
  })

  it('returns empty string for empty input', () => {
    expect(markdownToHtml('')).toBe('')
  })

  it('converts *italic* to <em>', () => {
    const result = markdownToHtml('*italic*')
    expect(result).toContain('<em>italic</em>')
  })

  it('strips YAML frontmatter before converting', () => {
    const markdown = '---\ntitle: Test\n---\n\n# Hello'
    const result = markdownToHtml(markdown)
    expect(result).not.toContain('title: Test')
    expect(result).toContain('<h1')
    expect(result).toContain('Hello')
  })
})

describe('htmlToMarkdown', () => {
  it('converts <strong> back to **bold**', () => {
    const result = htmlToMarkdown('<p><strong>bold</strong></p>')
    expect(result).toContain('**bold**')
  })

  it('converts <em> back to *italic*', () => {
    const result = htmlToMarkdown('<p><em>italic</em></p>')
    expect(result).toContain('*italic*')
  })

  it('returns empty string for empty input', () => {
    expect(htmlToMarkdown('')).toBe('')
  })

  it('removes empty paragraphs', () => {
    const result = htmlToMarkdown('<p>   </p><p>Hello</p>')
    expect(result).toContain('Hello')
  })
})

describe('isHtml', () => {
  it('returns true for HTML strings', () => {
    expect(isHtml('<p>Hello</p>')).toBe(true)
    expect(isHtml('<div class="test">content</div>')).toBe(true)
    expect(isHtml('<strong>bold</strong>')).toBe(true)
    expect(isHtml('<h1>heading</h1>')).toBe(true)
    expect(isHtml('<br/>')).toBe(true)
  })

  it('returns false for plain text', () => {
    expect(isHtml('Hello world')).toBe(false)
    expect(isHtml('Just plain text')).toBe(false)
  })

  it('returns false for markdown', () => {
    expect(isHtml('**bold**')).toBe(false)
    expect(isHtml('# heading')).toBe(false)
    expect(isHtml('- list item')).toBe(false)
  })
})

describe('convertForEditor', () => {
  it('passes through HTML as-is', () => {
    const html = '<p>Hello <strong>world</strong></p>'
    expect(convertForEditor(html)).toBe(html)
  })

  it('converts markdown to HTML', () => {
    const result = convertForEditor('**bold** text')
    expect(result).toContain('<strong>bold</strong>')
    expect(result).toContain('text')
  })

  it('returns empty string for empty input', () => {
    expect(convertForEditor('')).toBe('')
  })
})

describe('convertForStorage', () => {
  it('converts HTML to markdown', () => {
    const result = convertForStorage('<p><strong>bold</strong> text</p>')
    expect(result).toContain('**bold**')
    expect(result).toContain('text')
  })

  it('returns empty string for empty input', () => {
    expect(convertForStorage('')).toBe('')
  })
})

describe('roundtrip conversion', () => {
  it('markdownToHtml then htmlToMarkdown preserves semantics for bold', () => {
    const original = '**bold text**'
    const html = markdownToHtml(original)
    const backToMarkdown = htmlToMarkdown(html)
    expect(backToMarkdown).toContain('**bold text**')
  })

  it('markdownToHtml then htmlToMarkdown preserves semantics for headings', () => {
    const original = '## Second heading'
    const html = markdownToHtml(original)
    const backToMarkdown = htmlToMarkdown(html)
    expect(backToMarkdown).toContain('## Second heading')
  })

  it('markdownToHtml then htmlToMarkdown preserves semantics for lists', () => {
    const original = '- item one\n- item two'
    const html = markdownToHtml(original)
    const backToMarkdown = htmlToMarkdown(html)
    expect(backToMarkdown).toContain('item one')
    expect(backToMarkdown).toContain('item two')
  })
})
