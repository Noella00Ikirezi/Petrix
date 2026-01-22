import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Save,
  RotateCcw,
  History,
  CheckCircle,
  Clock,
  Lock,
  Unlock,
  MessageSquare,
  Eye,
  Edit3,
  Download,
  User,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Check,
  X,
} from 'lucide-react';
import { api } from '../../api/client';
import toast from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface DocumentEditorProps {
  documentId: string;
  onBack: () => void;
}

interface DocumentData {
  id: string;
  code: string;
  name: string;
  document_type: string;
  status: string;
  version: string;
  current_version_number: number;
  content_markdown: string;
  content_html: string;
  owner: string | null;
  is_locked: boolean;
  locked_by: string | null;
  last_validated_version: number | null;
  second_last_validated_version: number | null;
  created_at: string;
  updated_at: string | null;
}

interface VersionEntry {
  id: string;
  version_number: number;
  version_label: string;
  modified_by: string;
  modified_at: string;
  change_summary: string | null;
  change_type: string;
  is_validated: boolean;
  validated_by: string | null;
  is_current: boolean;
}

interface Comment {
  id: string;
  content: string;
  comment_type: string;
  author: string;
  created_at: string;
  is_resolved: boolean;
  resolved_by: string | null;
}

export function DocumentEditor({ documentId, onBack }: DocumentEditorProps) {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [changeSummary, setChangeSummary] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [showComments, setShowComments] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [previewVersion, setPreviewVersion] = useState<number | null>(null);

  // Fetch document
  const { data: document, isLoading } = useQuery<DocumentData>({
    queryKey: ['document-view', documentId],
    queryFn: async () => {
      const response = await api.get(`/smsi/documents/${documentId}/view`);
      return response.data;
    },
  });

  // Fetch version history
  const { data: versions } = useQuery<VersionEntry[]>({
    queryKey: ['document-versions', documentId],
    queryFn: async () => {
      const response = await api.get(`/smsi/documents/${documentId}/versions`);
      return response.data;
    },
    enabled: showHistory,
  });

  // Fetch comments
  const { data: comments, refetch: refetchComments } = useQuery<Comment[]>({
    queryKey: ['document-comments', documentId],
    queryFn: async () => {
      const response = await api.get(`/smsi/documents/${documentId}/comments`);
      return response.data;
    },
    enabled: showComments,
  });

  // Lock mutation
  const lockMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/smsi/documents/${documentId}/lock`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-view', documentId] });
      setIsEditing(true);
      setEditedContent(document?.content_markdown || '');
      toast.success('Document verrouillé pour édition');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Impossible de verrouiller le document');
    },
  });

  // Unlock mutation
  const unlockMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/smsi/documents/${documentId}/lock`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-view', documentId] });
      setIsEditing(false);
      toast.success('Document déverrouillé');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async () => {
      await api.put(`/smsi/documents/${documentId}`, {
        content_markdown: editedContent,
        change_summary: changeSummary || 'Modification du document',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-view', documentId] });
      queryClient.invalidateQueries({ queryKey: ['document-versions', documentId] });
      setIsEditing(false);
      setChangeSummary('');
      toast.success('Document enregistré');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Erreur lors de l'enregistrement");
    },
  });

  // Validate mutation
  const validateMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/smsi/documents/${documentId}/validate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-view', documentId] });
      queryClient.invalidateQueries({ queryKey: ['document-versions', documentId] });
      toast.success('Version validée');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Erreur lors de la validation');
    },
  });

  // Rollback mutation
  const rollbackMutation = useMutation({
    mutationFn: async (versionNumber: number) => {
      await api.post(`/smsi/documents/${documentId}/rollback/${versionNumber}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['document-view', documentId] });
      queryClient.invalidateQueries({ queryKey: ['document-versions', documentId] });
      setPreviewVersion(null);
      toast.success('Document restauré');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Erreur lors du rollback');
    },
  });

  // Add comment mutation
  const addCommentMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/smsi/documents/${documentId}/comments`, {
        content: newComment,
        comment_type: 'general',
      });
    },
    onSuccess: () => {
      refetchComments();
      setNewComment('');
      toast.success('Commentaire ajouté');
    },
  });

  // Resolve comment mutation
  const resolveCommentMutation = useMutation({
    mutationFn: async (commentId: string) => {
      await api.post(`/smsi/comments/${commentId}/resolve`);
    },
    onSuccess: () => {
      refetchComments();
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async (format: string) => {
      const response = await api.post(
        `/smsi/documents/${documentId}/export`,
        { format },
        { responseType: 'blob' }
      );
      return { blob: response.data, format };
    },
    onSuccess: ({ blob, format }) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${document?.code || 'document'}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Document exporté');
    },
    onError: () => {
      toast.error("Erreur lors de l'export");
    },
  });

  const handleStartEdit = () => {
    if (document?.is_locked) {
      toast.error(`Document verrouillé par ${document.locked_by}`);
      return;
    }
    lockMutation.mutate();
  };

  const handleCancelEdit = () => {
    unlockMutation.mutate();
    setEditedContent(document?.content_markdown || '');
  };

  const handleSave = () => {
    updateMutation.mutate();
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
      review: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      approved: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
      published: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    };
    const labels: Record<string, string> = {
      draft: 'Brouillon',
      review: 'En révision',
      approved: 'Validé',
      published: 'Publié',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${styles[status] || styles.draft}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement du document...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="w-12 h-12 mx-auto text-red-500" />
        <p className="mt-2 text-gray-600 dark:text-gray-400">Document introuvable</p>
        <button onClick={onBack} className="mt-4 text-blue-600 dark:text-blue-400 hover:underline">
          Retour
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">{document.name}</h1>
                {getStatusBadge(document.status)}
                {document.is_locked && (
                  <span className="flex items-center gap-1 text-xs text-orange-600 dark:text-orange-400">
                    <Lock className="w-3 h-3" />
                    {document.locked_by}
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {document.code} • Version {document.version} •
                {document.owner && ` Propriétaire: ${document.owner} •`}
                {document.last_validated_version && ` Dernière version validée: v${document.last_validated_version}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* History button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                showHistory ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}
            >
              <History className="w-4 h-4" />
              Historique
            </button>

            {/* Comments button */}
            <button
              onClick={() => setShowComments(!showComments)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                showComments ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Commentaires
            </button>

            {/* Export dropdown */}
            <div className="relative group">
              <button className="flex items-center gap-2 px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-gray-600 dark:text-gray-400">
                <Download className="w-4 h-4" />
                Exporter
                <ChevronDown className="w-3 h-3" />
              </button>
              <div className="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                {['md', 'docx', 'pdf', 'html'].map((format) => (
                  <button
                    key={format}
                    onClick={() => exportMutation.mutate(format)}
                    className="block w-full text-left px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 text-sm text-gray-700 dark:text-gray-300"
                  >
                    {format.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            {/* Edit/Save buttons */}
            {!isEditing ? (
              <button
                onClick={handleStartEdit}
                disabled={document.is_locked}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Edit3 className="w-4 h-4" />
                Modifier
              </button>
            ) : (
              <>
                <button
                  onClick={handleCancelEdit}
                  className="flex items-center gap-2 px-3 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <X className="w-4 h-4" />
                  Annuler
                </button>
                <button
                  onClick={handleSave}
                  disabled={updateMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {updateMutation.isPending ? 'Enregistrement...' : 'Enregistrer'}
                </button>
              </>
            )}

            {/* Validate button */}
            {!isEditing && document.status !== 'approved' && (
              <button
                onClick={() => validateMutation.mutate()}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                <CheckCircle className="w-4 h-4" />
                Valider
              </button>
            )}
          </div>
        </div>

        {/* Change summary input when editing */}
        {isEditing && (
          <div className="mt-4">
            <input
              type="text"
              value={changeSummary}
              onChange={(e) => setChangeSummary(e.target.value)}
              placeholder="Résumé des modifications (optionnel)"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
        )}
      </div>

      {/* Main content area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Document content */}
        <div className={`flex-1 overflow-auto p-6 ${showHistory || showComments ? 'w-2/3' : 'w-full'}`}>
          {isEditing ? (
            <textarea
              value={editedContent}
              onChange={(e) => setEditedContent(e.target.value)}
              className="w-full h-full min-h-[600px] p-4 font-mono text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-8 prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {document.content_markdown}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Side panel - History */}
        {showHistory && (
          <div className="w-1/3 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white">Historique des versions</h3>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {versions?.map((version) => (
                <div
                  key={version.id}
                  className={`p-4 hover:bg-gray-50 dark:hover:bg-gray-700 ${version.is_current ? 'bg-blue-50 dark:bg-blue-900/30' : ''}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 dark:text-white">v{version.version_label}</span>
                      {version.is_validated && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {version.is_current && (
                        <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                          Actuel
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => rollbackMutation.mutate(version.version_number)}
                      disabled={version.is_current}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:underline disabled:opacity-50 disabled:no-underline"
                    >
                      <RotateCcw className="w-3 h-3 inline mr-1" />
                      Restaurer
                    </button>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{version.change_summary || 'Modification'}</p>
                  <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <User className="w-3 h-3 inline mr-1" />
                    {version.modified_by} • {new Date(version.modified_at).toLocaleString('fr-FR')}
                  </div>
                  {version.is_validated && version.validated_by && (
                    <div className="mt-1 text-xs text-green-600 dark:text-green-400">
                      <CheckCircle className="w-3 h-3 inline mr-1" />
                      Validé par {version.validated_by}
                    </div>
                  )}
                </div>
              ))}
              {!versions?.length && (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  Aucune version antérieure
                </div>
              )}
            </div>

            {/* Quick rollback buttons */}
            {(document.last_validated_version || document.second_last_validated_version) && (
              <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Restauration rapide</p>
                <div className="space-y-2">
                  {document.last_validated_version && (
                    <button
                      onClick={() => rollbackMutation.mutate(document.last_validated_version!)}
                      className="w-full text-left px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                    >
                      Dernière version validée (v{document.last_validated_version})
                    </button>
                  )}
                  {document.second_last_validated_version && (
                    <button
                      onClick={() => rollbackMutation.mutate(document.second_last_validated_version!)}
                      className="w-full text-left px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                    >
                      Avant-dernière validée (v{document.second_last_validated_version})
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Side panel - Comments */}
        {showComments && (
          <div className="w-1/3 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-auto">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white">Commentaires</h3>
            </div>

            {/* Add comment */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Ajouter un commentaire..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              />
              <button
                onClick={() => addCommentMutation.mutate()}
                disabled={!newComment.trim()}
                className="mt-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Commenter
              </button>
            </div>

            {/* Comments list */}
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {comments?.map((comment) => (
                <div
                  key={comment.id}
                  className={`p-4 ${comment.is_resolved ? 'bg-gray-50 dark:bg-gray-900 opacity-60' : ''}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white text-sm">{comment.author}</span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                        {new Date(comment.created_at).toLocaleString('fr-FR')}
                      </span>
                    </div>
                    {!comment.is_resolved && (
                      <button
                        onClick={() => resolveCommentMutation.mutate(comment.id)}
                        className="text-xs text-green-600 dark:text-green-400 hover:underline"
                      >
                        <Check className="w-3 h-3 inline mr-1" />
                        Résoudre
                      </button>
                    )}
                  </div>
                  <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">{comment.content}</p>
                  {comment.is_resolved && (
                    <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                      Résolu par {comment.resolved_by}
                    </p>
                  )}
                </div>
              ))}
              {!comments?.length && (
                <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                  Aucun commentaire
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
