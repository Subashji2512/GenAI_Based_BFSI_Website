import React, { useEffect, useState } from "react";
import axios from "axios";


function getCSRFToken() {
  const cookie = document.cookie
    .split("; ")
    .find(row => row.startsWith("csrftoken="));
  return cookie ? cookie.split("=")[1] : "";
}

function App() {
  const [message, setMessage] = useState("Loading...");
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [filename, setFilename] = useState("No file selected");

  // Fetch API status
  useEffect(() => {
    axios
      .get("http://127.0.0.1:5000/upload-invoice/")
      .then((response) => setMessage(response.data.message))
      .catch((error) => {
        console.error("Error fetching data: ", error);
        setMessage("Failed to load data.");
      });
  }, []);

  // Handle file selection
  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFilename(selectedFile.name);
    } else {
      setFile(null);
      setFilename("No file selected");
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const csrfToken = getCSRFToken();
      
      const res = await axios.post(
        "http://127.0.0.1:5000/upload-invoice/",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
            "X-CSRFToken": csrfToken,
          },
          withCredentials: true,
        }
      );

      console.log("Response received:", res.data);
      setResponse(res.data);
    } catch (error) {
      console.error("Error uploading file:", error);
      
      if (error.response) {
        setError(`Server error: ${error.response.data.error || error.response.statusText}`);
      } else if (error.request) {
        setError("No response from server. Please check your connection.");
      } else {
        setError(`Error: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // Process vendor details to handle both string and object types
  const processVendorDetails = (vendorDetails) => {
    if (!vendorDetails) return "Unknown Vendor";
    
    // If it's already a string, return it
    if (typeof vendorDetails === 'string') return vendorDetails;
    
    // If vendor_details_str is available, use it
    if (typeof vendorDetails === 'object' && 'vendor_details_str' in vendorDetails) {
      return vendorDetails.vendor_details_str;
    }
    
    // If it's an object, convert it to a readable string
    if (typeof vendorDetails === 'object') {
      try {
        const parts = [];
        for (const [key, value] of Object.entries(vendorDetails)) {
          if (value) {
            parts.push(`${key.replace('_', ' ')}: ${value}`);
          }
        }
        return parts.join(', ');
      } catch (e) {
        console.error("Error formatting vendor details:", e);
        return JSON.stringify(vendorDetails);
      }
    }
    
    // Fallback
    return String(vendorDetails);
  };

  const formatInvoiceData = (data) => {
    if (!data || !data.extracted_data) return null;
    
    const extractedData = data.extracted_data;
    
    // Define the fields we want to display and their labels
    const fieldDefinitions = [
      { key: 'invoice_number', label: 'Invoice Number' },
      { 
        key: 'vendor_details', 
        label: 'Vendor',
        format: value => processVendorDetails(value)
      },
      { key: 'date', label: 'Date' },
      { key: 'total_amount', label: 'Total Amount', format: value => `$${parseFloat(value).toFixed(2)}` },
      { key: 'tax_amount', label: 'Tax', format: value => `$${parseFloat(value).toFixed(2)}` },
      { key: 'subtotal_amount', label: 'Subtotal', format: value => `$${parseFloat(value).toFixed(2)}` },
      { key: 'classification_confidence', label: 'Classification Confidence', format: value => `${(parseFloat(value) * 100).toFixed(1)}%` }
    ];

    return (
      <div className="invoice-data">
        <ul className="invoice-details-list">
          {fieldDefinitions.map(field => {
            if (extractedData[field.key] !== undefined) {
              const displayValue = field.format ? 
                field.format(extractedData[field.key]) : 
                extractedData[field.key];
              
              return (
                <li key={field.key} className="invoice-detail-item">
                  <span className="detail-label">{field.label}:</span>
                  <span className="detail-value">{displayValue}</span>
                </li>
              );
            }
            return null;
          })}
        </ul>

        {/* Display line items if available */}
        {extractedData.line_items && extractedData.line_items.length > 0 && (
          <div className="line-items-section">
            <h4 className="section-title">Line Items:</h4>
            <ul className="line-items-list">
              {extractedData.line_items.map((item, index) => (
                <li key={index} className="line-item">
                  <div className="line-item-details">
                    <span className="item-description">{item.description}</span>
                    <span className="item-quantity">Qty: {item.quantity}</span>
                    <span className="item-price">${parseFloat(item.price).toFixed(2)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="container">
      <div className="card">
        <h1>AI-Powered Invoice Processor</h1>
        <p className="redirect-message">Upload your invoice to know your expense category</p>
        
        <div className="upload-section">
          <div className="file-input-container">
            <input 
              type="file" 
              className="file-input"
              onChange={handleFileChange} 
              accept=".pdf,.jpg,.jpeg,.png" 
            />
            <p>{filename}</p>
          </div>
          
          <button 
            className="upload-btn" 
            onClick={handleUpload}
            disabled={loading || !file}
          >
            {loading ? "Processing..." : "Upload Invoice"}
          </button>
        </div>
        
        <p className="status-message">{message}</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading && <div className="loading">Processing invoice... Please wait</div>}

      {response && (
        <div className="response-container">
          <div className="response-header">
            <h3 className="response-title">Invoice Analysis Results</h3>
            <span className={`response-status ${response.status !== "success" ? "error" : ""}`}>
              {response.status === "success" ? "✓ Success" : "× Failed"}
            </span>
          </div>
          
          {response.extracted_data && (
            <div className="file-info">
              <div className="file-header">
                <p><strong>File:</strong> {response.file_name}</p>
                {response.invoice_id && (
                  <p><strong>Invoice ID:</strong> {response.invoice_id}</p>
                )}
              </div>
              
              {response.extracted_data.category && (
                <div className="category-badge">
                  <span><strong>Category: </strong>{response.extracted_data.category}</span>
                </div>
              )}

              
            </div>
          )}
          
          <h4 className="data-section-title">Extracted Invoice Data:</h4>
          <div className="data-display">
            {formatInvoiceData(response)}
          </div>
        </div>
      )}

      
    </div>
  );
}

export default App;