import { useEditor, EditorContent } from '@tiptap/react';
import { StarterKit } from '@tiptap/starter-kit';
import { Table } from '@tiptap/extension-table';
import { TableRow } from '@tiptap/extension-table-row';
import { TableCell } from '@tiptap/extension-table-cell';
import { TableHeader } from '@tiptap/extension-table-header';
import { TextStyle } from '@tiptap/extension-text-style';
import { Color } from '@tiptap/extension-color';
import { Highlight } from '@tiptap/extension-highlight';
import { Underline } from '@tiptap/extension-underline';
import { TextAlign } from '@tiptap/extension-text-align';
import { Placeholder } from '@tiptap/extension-placeholder';
import { Link } from '@tiptap/extension-link';
import { Image } from '@tiptap/extension-image';
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Code,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  AlignJustify,
  Heading1,
  Heading2,
  Heading3,
  Heading4,
  Quote,
  Minus,
  Table as TableIcon,
  Undo,
  Redo,
  Link as LinkIcon,
  Image as ImageIcon,
  Highlighter,
  Palette,
  Plus,
  Trash2,
  MoreHorizontal,
  ChevronDown,
  Type,
  Rows,
  Columns,
} from 'lucide-react';
import { useState, useCallback, useEffect } from 'react';

interface RichTextEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  documentType?: string;
}

const COLORS = [
  '#000000', '#374151', '#6b7280', '#9ca3af',
  '#ef4444', '#f97316', '#f59e0b', '#eab308',
  '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
  '#6366f1', '#8b5cf6', '#a855f7', '#ec4899',
  '#1e3a5f', '#14532d', '#7c2d12', '#581c87',
];

const HIGHLIGHT_COLORS = [
  '#fef3c7', '#fce7f3', '#dbeafe', '#dcfce7',
  '#e0e7ff', '#f3e8ff', '#fae8ff', '#fef9c3',
];

// Document type color schemes
const DOCUMENT_COLORS: Record<string, { primary: string; secondary: string }> = {
  DIRECTIVE: { primary: '#1e3a5f', secondary: '#2563eb' },
  POLICY: { primary: '#14532d', secondary: '#16a34a' },
  PROCEDURE: { primary: '#7c2d12', secondary: '#ea580c' },
  REGISTER: { primary: '#581c87', secondary: '#9333ea' },
  ANNEX: { primary: '#1e3a5f', secondary: '#0891b2' },
  DEFAULT: { primary: '#374151', secondary: '#6b7280' },
};

export function RichTextEditor({ content, onChange, placeholder, documentType }: RichTextEditorProps) {
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showHighlightPicker, setShowHighlightPicker] = useState(false);
  const [showTableMenu, setShowTableMenu] = useState(false);
  const [linkUrl, setLinkUrl] = useState('');
  const [showLinkInput, setShowLinkInput] = useState(false);

  const colors = DOCUMENT_COLORS[documentType || 'DEFAULT'] || DOCUMENT_COLORS.DEFAULT;

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3, 4],
        },
      }),
      Table.configure({
        resizable: true,
        HTMLAttributes: {
          class: 'border-collapse border border-gray-300 dark:border-gray-600 w-full',
        },
      }),
      TableRow,
      TableCell.configure({
        HTMLAttributes: {
          class: 'border border-gray-300 dark:border-gray-600 px-4 py-2',
        },
      }),
      TableHeader.configure({
        HTMLAttributes: {
          class: 'border border-gray-300 dark:border-gray-600 px-4 py-2 bg-gray-100 dark:bg-gray-700 font-semibold',
        },
      }),
      TextStyle,
      Color,
      Highlight.configure({
        multicolor: true,
      }),
      Underline,
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Placeholder.configure({
        placeholder: placeholder || 'Commencez à écrire...',
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 dark:text-blue-400 underline',
        },
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'max-w-full h-auto rounded-lg',
        },
      }),
    ],
    content: content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm dark:prose-invert max-w-none focus:outline-none min-h-[500px] px-8 py-6',
      },
    },
  });

  // Update content when prop changes
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  const addLink = useCallback(() => {
    if (linkUrl && editor) {
      editor.chain().focus().setLink({ href: linkUrl }).run();
      setLinkUrl('');
      setShowLinkInput(false);
    }
  }, [editor, linkUrl]);

  const addImage = useCallback(() => {
    const url = window.prompt('URL de l\'image:');
    if (url && editor) {
      editor.chain().focus().setImage({ src: url }).run();
    }
  }, [editor]);

  if (!editor) {
    return null;
  }

  const ToolbarButton = ({
    onClick,
    isActive = false,
    disabled = false,
    children,
    title,
  }: {
    onClick: () => void;
    isActive?: boolean;
    disabled?: boolean;
    children: React.ReactNode;
    title?: string;
  }) => (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`p-2 rounded-lg transition-colors ${
        isActive
          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {children}
    </button>
  );

  const ToolbarDivider = () => (
    <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1" />
  );

  return (
    <div className="rich-text-editor border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-white dark:bg-gray-800">
      {/* Toolbar */}
      <div className="toolbar bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 p-2 flex flex-wrap items-center gap-1">
        {/* Undo/Redo */}
        <ToolbarButton onClick={() => editor.chain().focus().undo().run()} disabled={!editor.can().undo()} title="Annuler">
          <Undo className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().redo().run()} disabled={!editor.can().redo()} title="Refaire">
          <Redo className="w-4 h-4" />
        </ToolbarButton>

        <ToolbarDivider />

        {/* Headings Dropdown */}
        <div className="relative">
          <button
            className="flex items-center gap-1 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
            onClick={() => {}}
          >
            <Type className="w-4 h-4" />
            <span className="text-sm">Style</span>
            <ChevronDown className="w-3 h-3" />
          </button>
          <div className="absolute left-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 w-48 hidden group-hover:block">
            <button
              onClick={() => editor.chain().focus().setParagraph().run()}
              className={`w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 ${editor.isActive('paragraph') ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
            >
              Paragraphe
            </button>
            <button
              onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
              className={`w-full text-left px-4 py-2 text-2xl font-bold hover:bg-gray-100 dark:hover:bg-gray-700 ${editor.isActive('heading', { level: 1 }) ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
            >
              Titre 1
            </button>
            <button
              onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
              className={`w-full text-left px-4 py-2 text-xl font-semibold hover:bg-gray-100 dark:hover:bg-gray-700 ${editor.isActive('heading', { level: 2 }) ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
            >
              Titre 2
            </button>
            <button
              onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
              className={`w-full text-left px-4 py-2 text-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-700 ${editor.isActive('heading', { level: 3 }) ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
            >
              Titre 3
            </button>
          </div>
        </div>

        {/* Heading shortcuts */}
        <ToolbarButton onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()} isActive={editor.isActive('heading', { level: 1 })} title="Titre 1">
          <Heading1 className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()} isActive={editor.isActive('heading', { level: 2 })} title="Titre 2">
          <Heading2 className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()} isActive={editor.isActive('heading', { level: 3 })} title="Titre 3">
          <Heading3 className="w-4 h-4" />
        </ToolbarButton>

        <ToolbarDivider />

        {/* Text formatting */}
        <ToolbarButton onClick={() => editor.chain().focus().toggleBold().run()} isActive={editor.isActive('bold')} title="Gras">
          <Bold className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleItalic().run()} isActive={editor.isActive('italic')} title="Italique">
          <Italic className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleUnderline().run()} isActive={editor.isActive('underline')} title="Souligné">
          <UnderlineIcon className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleStrike().run()} isActive={editor.isActive('strike')} title="Barré">
          <Strikethrough className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleCode().run()} isActive={editor.isActive('code')} title="Code">
          <Code className="w-4 h-4" />
        </ToolbarButton>

        <ToolbarDivider />

        {/* Color picker */}
        <div className="relative">
          <ToolbarButton onClick={() => setShowColorPicker(!showColorPicker)} title="Couleur du texte">
            <Palette className="w-4 h-4" />
          </ToolbarButton>
          {showColorPicker && (
            <div className="absolute left-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 p-2">
              <div className="grid grid-cols-4 gap-1">
                {COLORS.map((color) => (
                  <button
                    key={color}
                    onClick={() => {
                      editor.chain().focus().setColor(color).run();
                      setShowColorPicker(false);
                    }}
                    className="w-6 h-6 rounded border border-gray-300 dark:border-gray-600"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
              <button
                onClick={() => {
                  editor.chain().focus().unsetColor().run();
                  setShowColorPicker(false);
                }}
                className="w-full mt-2 px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                Réinitialiser
              </button>
            </div>
          )}
        </div>

        {/* Highlight picker */}
        <div className="relative">
          <ToolbarButton onClick={() => setShowHighlightPicker(!showHighlightPicker)} isActive={editor.isActive('highlight')} title="Surligner">
            <Highlighter className="w-4 h-4" />
          </ToolbarButton>
          {showHighlightPicker && (
            <div className="absolute left-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 p-2">
              <div className="grid grid-cols-4 gap-1">
                {HIGHLIGHT_COLORS.map((color) => (
                  <button
                    key={color}
                    onClick={() => {
                      editor.chain().focus().setHighlight({ color }).run();
                      setShowHighlightPicker(false);
                    }}
                    className="w-6 h-6 rounded border border-gray-300 dark:border-gray-600"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
              <button
                onClick={() => {
                  editor.chain().focus().unsetHighlight().run();
                  setShowHighlightPicker(false);
                }}
                className="w-full mt-2 px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                Supprimer
              </button>
            </div>
          )}
        </div>

        <ToolbarDivider />

        {/* Alignment */}
        <ToolbarButton onClick={() => editor.chain().focus().setTextAlign('left').run()} isActive={editor.isActive({ textAlign: 'left' })} title="Aligner à gauche">
          <AlignLeft className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().setTextAlign('center').run()} isActive={editor.isActive({ textAlign: 'center' })} title="Centrer">
          <AlignCenter className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().setTextAlign('right').run()} isActive={editor.isActive({ textAlign: 'right' })} title="Aligner à droite">
          <AlignRight className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().setTextAlign('justify').run()} isActive={editor.isActive({ textAlign: 'justify' })} title="Justifier">
          <AlignJustify className="w-4 h-4" />
        </ToolbarButton>

        <ToolbarDivider />

        {/* Lists */}
        <ToolbarButton onClick={() => editor.chain().focus().toggleBulletList().run()} isActive={editor.isActive('bulletList')} title="Liste à puces">
          <List className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleOrderedList().run()} isActive={editor.isActive('orderedList')} title="Liste numérotée">
          <ListOrdered className="w-4 h-4" />
        </ToolbarButton>

        <ToolbarDivider />

        {/* Quote and horizontal rule */}
        <ToolbarButton onClick={() => editor.chain().focus().toggleBlockquote().run()} isActive={editor.isActive('blockquote')} title="Citation">
          <Quote className="w-4 h-4" />
        </ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().setHorizontalRule().run()} title="Ligne horizontale">
          <Minus className="w-4 h-4" />
        </ToolbarButton>

        <ToolbarDivider />

        {/* Table */}
        <div className="relative">
          <ToolbarButton onClick={() => setShowTableMenu(!showTableMenu)} title="Tableau">
            <TableIcon className="w-4 h-4" />
          </ToolbarButton>
          {showTableMenu && (
            <div className="absolute left-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 w-56">
              <button
                onClick={() => {
                  editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
              >
                <Plus className="w-4 h-4" />
                Insérer tableau 3x3
              </button>
              <button
                onClick={() => {
                  editor.chain().focus().insertTable({ rows: 5, cols: 5, withHeaderRow: true }).run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
              >
                <Plus className="w-4 h-4" />
                Insérer tableau 5x5
              </button>
              <hr className="border-gray-200 dark:border-gray-700 my-1" />
              <button
                onClick={() => {
                  editor.chain().focus().addColumnBefore().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
              >
                <Columns className="w-4 h-4" />
                Ajouter colonne avant
              </button>
              <button
                onClick={() => {
                  editor.chain().focus().addColumnAfter().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
              >
                <Columns className="w-4 h-4" />
                Ajouter colonne après
              </button>
              <button
                onClick={() => {
                  editor.chain().focus().addRowBefore().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
              >
                <Rows className="w-4 h-4" />
                Ajouter ligne avant
              </button>
              <button
                onClick={() => {
                  editor.chain().focus().addRowAfter().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-gray-700 dark:text-gray-300"
              >
                <Rows className="w-4 h-4" />
                Ajouter ligne après
              </button>
              <hr className="border-gray-200 dark:border-gray-700 my-1" />
              <button
                onClick={() => {
                  editor.chain().focus().deleteColumn().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-red-600 dark:text-red-400"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer colonne
              </button>
              <button
                onClick={() => {
                  editor.chain().focus().deleteRow().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-red-600 dark:text-red-400"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer ligne
              </button>
              <button
                onClick={() => {
                  editor.chain().focus().deleteTable().run();
                  setShowTableMenu(false);
                }}
                className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2 text-red-600 dark:text-red-400"
              >
                <Trash2 className="w-4 h-4" />
                Supprimer tableau
              </button>
            </div>
          )}
        </div>

        <ToolbarDivider />

        {/* Link */}
        <div className="relative">
          <ToolbarButton onClick={() => setShowLinkInput(!showLinkInput)} isActive={editor.isActive('link')} title="Lien">
            <LinkIcon className="w-4 h-4" />
          </ToolbarButton>
          {showLinkInput && (
            <div className="absolute left-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 p-2 flex gap-2">
              <input
                type="url"
                value={linkUrl}
                onChange={(e) => setLinkUrl(e.target.value)}
                placeholder="https://..."
                className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white w-48"
                onKeyDown={(e) => e.key === 'Enter' && addLink()}
              />
              <button
                onClick={addLink}
                className="px-2 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                OK
              </button>
              {editor.isActive('link') && (
                <button
                  onClick={() => {
                    editor.chain().focus().unsetLink().run();
                    setShowLinkInput(false);
                  }}
                  className="px-2 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Image */}
        <ToolbarButton onClick={addImage} title="Image">
          <ImageIcon className="w-4 h-4" />
        </ToolbarButton>
      </div>


      {/* Editor content */}
      <EditorContent
        editor={editor}
        className="min-h-[500px] bg-white dark:bg-slate-900"
      />

      {/* Editor styles */}
      <style>{`
        .ProseMirror {
          min-height: 500px;
          padding: 2rem;
        }
        .ProseMirror:focus {
          outline: none;
        }
        .ProseMirror p.is-editor-empty:first-child::before {
          content: attr(data-placeholder);
          float: left;
          color: #9ca3af;
          pointer-events: none;
          height: 0;
        }
        .ProseMirror table {
          border-collapse: collapse;
          table-layout: fixed;
          width: 100%;
          margin: 1rem 0;
          overflow: hidden;
        }
        .ProseMirror table td,
        .ProseMirror table th {
          border: 1px solid #d1d5db;
          padding: 0.5rem 1rem;
          vertical-align: top;
          box-sizing: border-box;
          position: relative;
        }
        .dark .ProseMirror table td,
        .dark .ProseMirror table th {
          border-color: #4b5563;
        }
        .ProseMirror table th {
          background-color: ${colors.primary};
          color: white;
          font-weight: 600;
        }
        .ProseMirror table .selectedCell:after {
          z-index: 2;
          position: absolute;
          content: "";
          left: 0;
          right: 0;
          top: 0;
          bottom: 0;
          background: rgba(59, 130, 246, 0.2);
          pointer-events: none;
        }
        .ProseMirror blockquote {
          border-left: 4px solid ${colors.secondary};
          margin: 1rem 0;
          padding-left: 1rem;
          color: #4b5563;
        }
        .dark .ProseMirror blockquote {
          color: #9ca3af;
        }
        .ProseMirror h1 {
          font-size: 2rem;
          font-weight: 700;
          margin-top: 2rem;
          margin-bottom: 1rem;
          padding-bottom: 0.5rem;
          border-bottom: 2px solid ${colors.secondary};
        }
        .ProseMirror h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-top: 1.5rem;
          margin-bottom: 0.75rem;
          color: ${colors.primary};
        }
        .dark .ProseMirror h2 {
          color: ${colors.secondary};
        }
        .ProseMirror h3 {
          font-size: 1.25rem;
          font-weight: 600;
          margin-top: 1.25rem;
          margin-bottom: 0.5rem;
        }
        .ProseMirror ul {
          list-style-type: disc;
          padding-left: 1.5rem;
        }
        .ProseMirror ol {
          list-style-type: decimal;
          padding-left: 1.5rem;
        }
        .ProseMirror li {
          margin: 0.25rem 0;
        }
        .ProseMirror hr {
          border: none;
          border-top: 1px solid #e5e7eb;
          margin: 2rem 0;
        }
        .dark .ProseMirror hr {
          border-color: #4b5563;
        }
        .ProseMirror code {
          background-color: #f3f4f6;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
          font-family: monospace;
          font-size: 0.875em;
        }
        .dark .ProseMirror code {
          background-color: #374151;
        }
        .ProseMirror pre {
          background-color: #1f2937;
          color: #e5e7eb;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
        }
        .ProseMirror img {
          max-width: 100%;
          height: auto;
          border-radius: 0.5rem;
        }
        .ProseMirror p {
          margin: 0.5rem 0;
          line-height: 1.7;
        }
      `}</style>
    </div>
  );
}
