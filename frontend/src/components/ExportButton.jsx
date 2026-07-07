import axios from 'axios';

const API = 'http://localhost:8000';

export default function ExportButton({ docId }) {
  const handleExport = async () => {
    try {
      const res = await axios.get(`${API}/export/${docId}/pdf`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ragged-${docId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  return (
    <button
      className="export-btn"
      onClick={handleExport}
      id="export-btn"
      type="button"
    >
      EXPORT AS PDF →
    </button>
  );
}
