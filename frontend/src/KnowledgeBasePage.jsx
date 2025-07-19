import React, { useState, useEffect } from "react";
import { kbAPI } from "./api";

export default function KnowledgeBasePage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [kbList, setKbList] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [selectedKb, setSelectedKb] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  // Fetch KB list
  const fetchKbList = async () => {
    setLoadingList(true);
    try {
      const response = await kbAPI.list();
      setKbList(response.data.files || []);
    } catch (err) {
      console.error('Error fetching KB list:', err);
      setKbList([]);
    }
    setLoadingList(false);
  };

  // Fetch chunks for a specific KB
  const fetchChunks = async (kbId) => {
    setLoadingChunks(true);
    try {
      const response = await kbAPI.getChunks(kbId);
      setChunks(response.data.chunks || []);
      setSelectedKb(response.data);
    } catch (err) {
      console.error('Error fetching chunks:', err);
      setChunks([]);
      setSelectedKb(null);
    }
    setLoadingChunks(false);
  };

  useEffect(() => {
    fetchKbList();
  }, []);

  // Handle file upload
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await kbAPI.upload(formData);
      setUploadResult(response.data);
      fetchKbList();
    } catch (err) {
      console.error('Upload error:', err);
      setUploadResult({ error: "Upload failed" });
    }
    setUploading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto" }}>
      <h2>Knowledge Base Upload</h2>
      <form onSubmit={handleUpload}>
        <div style={{ marginBottom: "16px" }}>
          <label>
            File (XLSX, XLS, CSV with TAB delimiter):
            <br />
            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={(e) => setFile(e.target.files[0])}
            />
          </label>
        </div>
        
        <div style={{ marginBottom: "16px", fontSize: "14px", color: "#666" }}>
          <strong>Note:</strong> Each row in the table will become a separate chunk automatically.
        </div>
        
        <button type="submit" disabled={uploading || !file}>
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {uploadResult && (
        <div style={{ marginTop: 16 }}>
          <b>Upload result:</b>
          <pre style={{ background: "#f5f5f5", padding: 8 }}>
            {JSON.stringify(uploadResult, null, 2)}
          </pre>
        </div>
      )}

      <hr style={{ margin: "32px 0" }} />
      <h3>Knowledge Base Files</h3>
      {loadingList ? (
        <div>Loading...</div>
      ) : (
        <table border="1" cellPadding="8" style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Filename</th>
              <th>Num Chunks</th>
              <th>Size (bytes)</th>
              <th>Uploaded At</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {kbList.length === 0 ? (
              <tr>
                <td colSpan={6}>No files found.</td>
              </tr>
            ) : (
              kbList.map((f) => (
                <tr key={f.id}>
                  <td>{f.id}</td>
                  <td>{f.filename}</td>
                  <td>{f.num_chunks}</td>
                  <td>{f.file_size}</td>
                  <td>{f.uploaded_at}</td>
                  <td>
                    <button 
                      onClick={() => fetchChunks(f.id)}
                      style={{ marginRight: '8px' }}
                    >
                      View Chunks
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      )}

      {/* Chunks Display Section */}
      {selectedKb && (
        <div style={{ marginTop: "32px" }}>
          <h3>Chunks for: {selectedKb.filename}</h3>
          <p>Total chunks: {selectedKb.total_chunks}</p>
          
          {loadingChunks ? (
            <div>Loading chunks...</div>
          ) : (
            <div style={{ maxHeight: "500px", overflowY: "auto", border: "1px solid #ccc", padding: "16px" }}>
              {chunks.length === 0 ? (
                <div>No chunks found.</div>
              ) : (
                chunks.map((chunk, index) => (
                  <div 
                    key={chunk.id} 
                    style={{ 
                      border: "1px solid #ddd", 
                      margin: "8px 0", 
                      padding: "12px", 
                      borderRadius: "4px",
                      backgroundColor: "#f9f9f9"
                    }}
                  >
                    <div style={{ fontWeight: "bold", marginBottom: "8px", color: "#333" }}>
                      Chunk #{chunk.id} (Row {chunk.row_index})
                    </div>
                    <div style={{ 
                      fontFamily: "monospace", 
                      fontSize: "14px", 
                      lineHeight: "1.4",
                      wordBreak: "break-word"
                    }}>
                      {chunk.text}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
} 