import { useEffect, useState } from "react";
import Loading from "../components/Loading";
import TimeAgo from "timeago-react";
import { Trash2, Upload, ImageOff, Check } from "lucide-react";
import Breadcrumbs from "../components/Breadcrumbs";

interface Document {
  id: number;
  folder_name: string;
  original_filename: string;
  display_name: string | null;
  mime_type: string;
  created_at: string;
}

interface DocumentCardProps {
  document: Document;
  isSelected: boolean;
  onToggleSelect: (id: number) => void;
}

function DocumentCard({ document, isSelected, onToggleSelect }: DocumentCardProps) {
  const [thumbnailError, setThumbnailError] = useState(false);

  return (
    <div
      className="group relative bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden cursor-pointer"
      onClick={() => onToggleSelect(document.id)}
    >
      <div className="aspect-[3/4] bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center overflow-hidden relative">
        {isSelected && (
          <div className="absolute inset-0 bg-zinc-900/50 dark:bg-zinc-900/70 flex items-center justify-center z-10 transition-opacity">
            <Check className="h-8 w-8 text-white" />
          </div>
        )}
        {thumbnailError ? (
          <ImageOff className="h-12 w-12 text-zinc-400 dark:text-zinc-600" />
        ) : (
          <img
            src={`api/frontend/documents/${document.id}/thumbnail`}
            alt={document.original_filename}
            className="w-full h-full object-cover"
            onError={() => setThumbnailError(true)}
          />
        )}
      </div>
      <div className={`p-4 ${isSelected ? "opacity-50" : ""}`}>
        <h3
          className="text-sm font-medium text-zinc-900 dark:text-zinc-100 truncate mb-1"
          title={document.display_name || document.original_filename}
        >
          {document.display_name || document.original_filename}
        </h3>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          <TimeAgo
            title={new Date(document.created_at).toLocaleString()}
            datetime={new Date(document.created_at)}
          />
        </p>
      </div>
    </div>
  );
}

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{
    current: number;
    total: number;
    currentFile: string;
  } | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && selectedIds.size > 0) {
        setSelectedIds(new Set());
      }
    }

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [selectedIds.size]);

  useEffect(() => {
    function handleSelectAll(event: KeyboardEvent) {
      if (
        (event.ctrlKey || event.metaKey) &&
        event.key === "a" &&
        documents.length > 0
      ) {
        event.preventDefault();
        setSelectedIds(new Set(documents.map((doc) => doc.id)));
      }
    }

    window.addEventListener("keydown", handleSelectAll);
    return () => window.removeEventListener("keydown", handleSelectAll);
  }, [documents]);

  async function fetchDocuments() {
    try {
      setLoading(true);
      const response = await fetch("api/frontend/documents");
      if (!response.ok) {
        throw new Error("Failed to fetch documents");
      }
      const data = await response.json();
      setDocuments(data);
      setSelectedIds(new Set());
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const pdfFiles = Array.from(files).filter((file) =>
      file.name.toLowerCase().endsWith(".pdf")
    );

    if (pdfFiles.length === 0) {
      setError("No PDF files selected");
      event.target.value = "";
      return;
    }

    if (pdfFiles.length < files.length) {
      setError(
        `Only ${pdfFiles.length} of ${files.length} files are PDFs. Uploading PDFs only.`
      );
    } else {
      setError(null);
    }

    try {
      setUploading(true);
      setUploadProgress({
        current: 0,
        total: pdfFiles.length,
        currentFile: pdfFiles[0].name,
      });

      const errors: string[] = [];
      let successCount = 0;

      for (let i = 0; i < pdfFiles.length; i++) {
        const file = pdfFiles[i];
        setUploadProgress({
          current: i + 1,
          total: pdfFiles.length,
          currentFile: file.name,
        });

        try {
          const formData = new FormData();
          formData.append("file", file);

          const response = await fetch("api/frontend/documents", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            errors.push(`${file.name}: ${errorData.detail || "Upload failed"}`);
          } else {
            successCount++;
          }
        } catch (err) {
          errors.push(
            `${file.name}: ${err instanceof Error ? err.message : "Upload failed"}`
          );
        }
      }

      setUploadProgress(null);

      if (errors.length > 0) {
        setError(
          `Uploaded ${successCount} of ${pdfFiles.length} files. Errors: ${errors.join("; ")}`
        );
      } else {
        setError(null);
      }

      await fetchDocuments();
      event.target.value = "";
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
      setUploadProgress(null);
    } finally {
      setUploading(false);
    }
  }

  function handleToggleSelect(documentId: number) {
    setSelectedIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(documentId)) {
        newSet.delete(documentId);
      } else {
        newSet.add(documentId);
      }
      return newSet;
    });
  }

  async function handleDelete(documentId: number) {
    if (!confirm("Are you sure you want to delete this document?")) {
      return;
    }

    try {
      const response = await fetch(`api/frontend/documents/${documentId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete document");
      }

      await fetchDocuments();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  }

  async function handleBulkDelete() {
    if (selectedIds.size === 0) return;

    const count = selectedIds.size;
    if (
      !confirm(
        `Are you sure you want to delete ${count} document${count > 1 ? "s" : ""}?`
      )
    ) {
      return;
    }

    try {
      const errors: string[] = [];
      let successCount = 0;

      for (const id of selectedIds) {
        try {
          const response = await fetch(`api/frontend/documents/${id}`, {
            method: "DELETE",
          });

          if (!response.ok) {
            errors.push(`Document ${id}: Delete failed`);
          } else {
            successCount++;
          }
        } catch (err) {
          errors.push(
            `Document ${id}: ${err instanceof Error ? err.message : "Delete failed"}`
          );
        }
      }

      if (errors.length > 0) {
        setError(
          `Deleted ${successCount} of ${count} documents. Errors: ${errors.join("; ")}`
        );
      } else {
        setError(null);
      }

      setSelectedIds(new Set());
      await fetchDocuments();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    }
  }

  if (loading) {
    return <Loading />;
  }

  return (
    <>
      <div className="flex justify-between items-center mb-4 min-h-10">
        <Breadcrumbs />
        <div className="flex gap-2">
          <button
            onClick={handleBulkDelete}
            disabled={selectedIds.size === 0}
            className={`inline-flex items-center justify-center rounded-md border px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              selectedIds.size === 0
                ? "border-zinc-300 bg-white text-zinc-700 opacity-50 cursor-not-allowed dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:focus:ring-zinc-700 dark:focus:ring-offset-zinc-950"
                : "border-red-300 bg-red-50 text-red-700 hover:bg-red-100 hover:cursor-pointer focus:ring-red-300 dark:border-red-700 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30 dark:focus:ring-red-700 dark:focus:ring-offset-zinc-950"
            }`}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </button>
          <label
            className={`inline-flex items-center justify-center rounded-md border px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-zinc-300 focus:ring-offset-2 dark:focus:ring-zinc-700 dark:focus:ring-offset-zinc-950 ${
              uploading
                ? "border-zinc-300 bg-white text-zinc-700 opacity-50 cursor-not-allowed dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300"
                : "border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50 cursor-pointer dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900"
            }`}
          >
            <Upload className="h-4 w-4 mr-2" />
            {uploading ? "Uploading..." : "Upload PDF(s)"}
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {uploadProgress && (
        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
          <div className="text-sm text-blue-800 dark:text-blue-200">
            Uploading {uploadProgress.current} of {uploadProgress.total}:{" "}
            {uploadProgress.currentFile}
          </div>
          <div className="mt-2 w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
            <div
              className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${(uploadProgress.current / uploadProgress.total) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md text-red-800 dark:text-red-200">
          {error}
        </div>
      )}

      {documents.length === 0 ? (
        <div className="text-center py-12 text-zinc-500 dark:text-zinc-400">
          No documents uploaded yet. Click "Upload PDF(s)" to add your first manual.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {documents.map((document) => (
            <DocumentCard
              key={document.id}
              document={document}
              isSelected={selectedIds.has(document.id)}
              onToggleSelect={handleToggleSelect}
            />
          ))}
        </div>
      )}
    </>
  );
}
