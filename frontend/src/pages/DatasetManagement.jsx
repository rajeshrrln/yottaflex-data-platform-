
import { useEffect, useRef, useState } from "react";

import {
  UploadCloud,
  FileSpreadsheet,
  FileJson,
  Database,
  Table,
  Columns3,
  AlertCircle,
  CheckCircle2,
  Trash2,
  FileCheck,
  RefreshCw,
} from "lucide-react";

import {
  getDatasets,
  getDatasetDetails,
} from "../services/api";

const MAX_FILE_SIZE = 5 * 1024 * 1024;
const PREVIEW_LIMIT = 10;

// ------------------------------------------
// CSV Parser
// ------------------------------------------

function parseCSV(text) {
  const rows = [];
  let row = [];
  let value = "";
  let insideQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && insideQuotes && next === '"') {
      value += '"';
      i++;
    } else if (char === '"') {
      insideQuotes = !insideQuotes;
    } else if (char === "," && !insideQuotes) {
      row.push(value);
      value = "";
    } else if (
      (char === "\n" || char === "\r") &&
      !insideQuotes
    ) {
      if (char === "\r" && next === "\n") i++;

      row.push(value);

      if (row.some((cell) => cell.trim() !== "")) {
        rows.push(row);
      }

      row = [];
      value = "";
    } else {
      value += char;
    }
  }

  if (insideQuotes) {
    throw new Error("Malformed CSV: unclosed quoted field.");
  }

  row.push(value);

  if (row.some((cell) => cell.trim() !== "")) {
    rows.push(row);
  }

  if (rows.length === 0) {
    throw new Error("The uploaded file is empty.");
  }

  const headers = rows[0].map((header) => header.trim());

  if (headers.some((header) => !header)) {
    throw new Error("CSV contains an empty column name.");
  }

  const normalizedHeaders = headers.map((header) =>
    header.toLowerCase()
  );

  if (new Set(normalizedHeaders).size !== headers.length) {
    throw new Error("CSV contains duplicate column names.");
  }

  const records = [];
  let malformedCount = 0;

  for (let i = 1; i < rows.length; i++) {
    if (rows[i].length !== headers.length) {
      malformedCount++;
      continue;
    }

    const record = {};

    headers.forEach((header, index) => {
      record[header] = rows[i][index];
    });

    records.push(record);
  }

  return {
    headers,
    records,
    totalRows: rows.length - 1,
    malformedCount,
  };
}

// ------------------------------------------
// Automatic Data Type Detection
// ------------------------------------------

function detectType(values) {
  const nonEmpty = values.filter(
    (value) =>
      value !== null &&
      value !== undefined &&
      String(value).trim() !== ""
  );

  if (nonEmpty.length === 0) return "unknown";

  if (
    nonEmpty.every((value) =>
      /^-?\d+$/.test(String(value).trim())
    )
  ) {
    return "integer";
  }

  if (
    nonEmpty.every(
      (value) =>
        !Number.isNaN(Number(value)) &&
        String(value).trim() !== ""
    )
  ) {
    return "number";
  }

  if (
    nonEmpty.every(
      (value) => !Number.isNaN(Date.parse(value))
    )
  ) {
    return "datetime";
  }

  return "string";
}

// ==========================================
// Dataset Management Component
// ==========================================

export default function DatasetManagement() {
  const fileInputRef = useRef(null);

  // File upload states
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  // Database Explorer states
  const [activeTab, setActiveTab] = useState("upload");
  const [databaseTables, setDatabaseTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [tableDetails, setTableDetails] = useState(null);
  const [databaseLoading, setDatabaseLoading] = useState(false);
  const [databaseError, setDatabaseError] = useState("");

  // ------------------------------------------
  // Fetch Database Tables
  // ------------------------------------------

  const fetchDatabaseTables = async () => {
    try {
      setDatabaseLoading(true);
      setDatabaseError("");

      const result = await getDatasets();

      setDatabaseTables(result.datasets || []);
    } catch (err) {
      setDatabaseError(err.message);
    } finally {
      setDatabaseLoading(false);
    }
  };

  // ------------------------------------------
  // Fetch Selected Table Details
  // ------------------------------------------

  const fetchTableDetails = async (tableName) => {
    try {
      setDatabaseLoading(true);
      setDatabaseError("");
      setSelectedTable(tableName);
      setTableDetails(null);

      const result = await getDatasetDetails(tableName, 10);

      setTableDetails(result);
    } catch (err) {
      setDatabaseError(err.message);
      setTableDetails(null);
    } finally {
      setDatabaseLoading(false);
    }
  };

  // Load tables when Database Explorer opens
  useEffect(() => {
    if (activeTab === "database") {
      fetchDatabaseTables();
    }
  }, [activeTab]);

  // ------------------------------------------
  // Process Uploaded File
  // ------------------------------------------

  const processFile = async (file) => {
    setError("");
    setDataset(null);

    if (!file) return;

    const extension = file.name
      .split(".")
      .pop()
      .toLowerCase();

    if (!["csv", "json"].includes(extension)) {
      setError("Only CSV and JSON files are supported.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size must not exceed 5 MB.");
      return;
    }

    if (file.size === 0) {
      setError("The uploaded file is empty.");
      return;
    }

    setLoading(true);

    try {
      const text = await file.text();

      let headers = [];
      let records = [];
      let totalRows = 0;
      let malformedCount = 0;

      if (extension === "csv") {
        const result = parseCSV(text);

        headers = result.headers;
        records = result.records;
        totalRows = result.totalRows;
        malformedCount = result.malformedCount;
      }

      if (extension === "json") {
        let parsed;

        try {
          parsed = JSON.parse(text);
        } catch {
          throw new Error("Invalid JSON syntax.");
        }

        if (!Array.isArray(parsed)) {
          throw new Error(
            "JSON must contain an array of objects."
          );
        }

        if (
          parsed.some(
            (record) =>
              record === null ||
              typeof record !== "object" ||
              Array.isArray(record)
          )
        ) {
          throw new Error(
            "Every JSON array item must be an object."
          );
        }

        if (parsed.length === 0) {
          throw new Error(
            "JSON dataset contains no records."
          );
        }

        headers = [
          ...new Set(
            parsed.flatMap((record) => Object.keys(record))
          ),
        ];

        if (headers.length === 0) {
          throw new Error(
            "JSON objects contain no columns."
          );
        }

        records = parsed.filter((record) =>
          headers.every((header) =>
            Object.prototype.hasOwnProperty.call(
              record,
              header
            )
          )
        );

        malformedCount = parsed.length - records.length;
        totalRows = parsed.length;
      }

      const missingCounts = {};

      const columnDetails = headers.map((header) => {
        const values = records.map(
          (record) => record[header]
        );

        missingCounts[header] = values.filter(
          (value) =>
            value === null ||
            value === undefined ||
            String(value).trim() === ""
        ).length;

        return {
          name: header,
          type: detectType(values),
          nullable: missingCounts[header] > 0,
          missing: missingCounts[header],
        };
      });

      setDataset({
        name: file.name,
        format: extension.toUpperCase(),
        size: file.size,
        totalRows,
        validRows: records.length,
        malformedCount,
        columns: columnDetails,
        records: records.slice(0, PREVIEW_LIMIT),
      });
    } catch (err) {
      setError(
        err.message || "Unable to process dataset."
      );
    } finally {
      setLoading(false);
    }
  };

  // ------------------------------------------
  // File Input Handlers
  // ------------------------------------------

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    processFile(file);

    event.target.value = "";
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragging(false);

    const file = event.dataTransfer.files?.[0];

    processFile(file);
  };

  const resetDataset = () => {
    setDataset(null);
    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // ------------------------------------------
  // Format File Size
  // ------------------------------------------

  const formatSize = (bytes) => {
    return bytes < 1024 * 1024
      ? `${(bytes / 1024).toFixed(1)} KB`
      : `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // ==========================================
  // UI
  // ==========================================

  return (
    <div className="dataset-page">

      {/* Page Heading */}

      <div className="dataset-heading">
        <div>
          <p className="eyebrow">
            DATA ENGINEERING / INGESTION
          </p>

          <h1>Dataset Management</h1>

          <p>
            Upload, inspect and explore your datasets.
          </p>
        </div>

        <span className="environment-badge">
          SQLITE DATABASE
        </span>
      </div>

      {/* Navigation Tabs */}

      <div className="dataset-tabs">

        <button
          type="button"
          className={
            activeTab === "upload" ? "active" : ""
          }
          onClick={() => setActiveTab("upload")}
        >
          <UploadCloud size={16} />
          File Upload
        </button>

        <button
          type="button"
          className={
            activeTab === "database" ? "active" : ""
          }
          onClick={() => setActiveTab("database")}
        >
          <Database size={16} />
          Database Explorer
        </button>

      </div>

      {/* ======================================
          FILE UPLOAD TAB
      ====================================== */}

      {activeTab === "upload" && (
        <>

          <section className="dataset-upload-card">

            <div className="dataset-card-heading">
              <div className="dataset-heading-icon">
                <UploadCloud size={22} />
              </div>

              <div>
                <h3>Upload Dataset</h3>
                <p>
                  Select a source file for inspection.
                </p>
              </div>
            </div>

            <div
              className={`upload-zone ${
                dragging ? "dragging" : ""
              }`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() =>
                fileInputRef.current?.click()
              }
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" ||
                  event.key === " "
                ) {
                  event.preventDefault();
                  fileInputRef.current?.click();
                }
              }}
            >
              <div className="upload-icon">
                <UploadCloud size={32} />
              </div>

              <h3>
                Drag and drop your dataset here
              </h3>

              <p>or click to browse files</p>

              <div className="supported-formats">
                <span>
                  <FileSpreadsheet size={14} />
                  CSV
                </span>

                <span>
                  <FileJson size={14} />
                  JSON
                </span>
              </div>

              <small>
                Maximum file size: 5 MB
              </small>

              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.json"
                hidden
                onChange={handleFileChange}
              />
            </div>

            {loading && (
              <div className="dataset-message">
                <RefreshCw size={17} />
                Processing dataset...
              </div>
            )}

            {error && (
              <div className="dataset-message dataset-error">
                <AlertCircle size={18} />
                {error}
              </div>
            )}

          </section>

          {/* Uploaded Dataset Results */}

          {dataset && (
            <>

              <section className="dataset-metrics">

                <article className="dataset-metric">
                  <div className="dataset-metric-icon blue">
                    <Database size={19} />
                  </div>

                  <span>Total Records</span>

                  <h3>
                    {dataset.totalRows.toLocaleString()}
                  </h3>
                </article>

                <article className="dataset-metric">
                  <div className="dataset-metric-icon green">
                    <CheckCircle2 size={19} />
                  </div>

                  <span>Structurally Valid</span>

                  <h3>
                    {dataset.validRows.toLocaleString()}
                  </h3>
                </article>

                <article className="dataset-metric">
                  <div className="dataset-metric-icon purple">
                    <Columns3 size={19} />
                  </div>

                  <span>Total Columns</span>

                  <h3>{dataset.columns.length}</h3>
                </article>

                <article className="dataset-metric">
                  <div className="dataset-metric-icon orange">
                    <AlertCircle size={19} />
                  </div>

                  <span>Malformed Rows</span>

                  <h3>{dataset.malformedCount}</h3>
                </article>

              </section>

              <section className="dataset-file-card">

                <div className="dataset-file-info">
                  {dataset.format === "CSV" ? (
                    <FileSpreadsheet
                      size={25}
                      color="#268b69"
                    />
                  ) : (
                    <FileJson
                      size={25}
                      color="#8865ce"
                    />
                  )}

                  <div>
                    <strong>{dataset.name}</strong>

                    <span>
                      {dataset.format} ·{" "}
                      {formatSize(dataset.size)} ·{" "}
                      {dataset.columns.length} columns
                    </span>
                  </div>
                </div>

                <div className="dataset-file-actions">
                  <span className="dataset-valid-badge">
                    <CheckCircle2 size={14} />
                    Parsed
                  </span>

                  <button
                    className="dataset-remove-button"
                    onClick={resetDataset}
                    type="button"
                  >
                    <Trash2 size={15} />
                    Remove
                  </button>
                </div>

              </section>

              <section className="dataset-content-grid">

                <article className="dataset-content-card">

                  <div className="dataset-section-heading">
                    <div>
                      <h3>Detected Schema</h3>
                      <p>Inferred column metadata</p>
                    </div>

                    <Columns3 size={20} />
                  </div>

                  <div className="dataset-table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          <th>Column Name</th>
                          <th>Data Type</th>
                          <th>Nullable</th>
                          <th>Missing</th>
                        </tr>
                      </thead>

                      <tbody>
                        {dataset.columns.map((column) => (
                          <tr key={column.name}>
                            <td className="dataset-column-name">
                              {column.name}
                            </td>

                            <td>
                              <span className="type-badge">
                                {column.type}
                              </span>
                            </td>

                            <td>
                              {column.nullable ? "Yes" : "No"}
                            </td>

                            <td>{column.missing}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                </article>

                <article className="dataset-content-card">

                  <div className="dataset-section-heading">
                    <div>
                      <h3>Dataset Information</h3>
                      <p>File inspection summary</p>
                    </div>

                    <FileCheck size={20} />
                  </div>

                  <div className="dataset-info-row">
                    <span>File format</span>
                    <strong>{dataset.format}</strong>
                  </div>

                  <div className="dataset-info-row">
                    <span>File size</span>
                    <strong>{formatSize(dataset.size)}</strong>
                  </div>

                  <div className="dataset-info-row">
                    <span>Total records</span>
                    <strong>{dataset.totalRows}</strong>
                  </div>

                  <div className="dataset-info-row">
                    <span>Valid records</span>
                    <strong>{dataset.validRows}</strong>
                  </div>

                  <div className="dataset-info-row">
                    <span>Malformed records</span>
                    <strong>{dataset.malformedCount}</strong>
                  </div>

                  <div className="dataset-info-row">
                    <span>Preview limit</span>
                    <strong>{PREVIEW_LIMIT} records</strong>
                  </div>

                  <p className="dataset-info-note">
                    Type inference is based on the uploaded
                    records. Full schema enforcement happens
                    in the backend.
                  </p>

                </article>

              </section>

              <section className="dataset-content-card dataset-preview-card">

                <div className="dataset-section-heading">
                  <div>
                    <h3>Data Preview</h3>

                    <p>
                      Showing {dataset.records.length} of{" "}
                      {dataset.validRows} structurally valid
                      records.
                    </p>
                  </div>

                  <Table size={20} />
                </div>

                <div className="dataset-table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        {dataset.columns.map((column) => (
                          <th key={column.name}>
                            {column.name}
                          </th>
                        ))}
                      </tr>
                    </thead>

                    <tbody>
                      {dataset.records.map((record, index) => (
                        <tr key={index}>
                          {dataset.columns.map((column) => (
                            <td key={column.name}>
                              {record[column.name] === null ||
                              record[column.name] === undefined
                                ? "NULL"
                                : String(record[column.name]) ||
                                  "NULL"}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

              </section>

            </>
          )}

        </>
      )}

      {/* ======================================
          DATABASE EXPLORER TAB
      ====================================== */}

      {activeTab === "database" && (

        <section className="dataset-content-card">

          <div className="dataset-section-heading">
            <div>
              <h3>SQLite Database Explorer</h3>
              <p>
                Browse actual tables and stored records.
              </p>
            </div>

            <button
              type="button"
              className="primary-action"
              onClick={fetchDatabaseTables}
              disabled={databaseLoading}
            >
              <RefreshCw size={16} />
              {databaseLoading ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {databaseError && (
            <div className="dataset-message dataset-error">
              <AlertCircle size={18} />
              {databaseError}
            </div>
          )}

          {databaseLoading && (
            <p>Loading database information...</p>
          )}

          {!databaseLoading && !databaseError && (
            <>
              <h4>Available Database Tables</h4>

              {databaseTables.length === 0 ? (
                <p>No database tables found.</p>
              ) : (
                <div className="database-table-list">
                  {databaseTables.map((table) => (
                    <button
                      type="button"
                      key={table.name}
                      className={`database-table-item ${
                        selectedTable === table.name
                          ? "active"
                          : ""
                      }`}
                      onClick={() =>
                        fetchTableDetails(table.name)
                      }
                    >
                      <Database size={20} />

                      <strong>{table.name}</strong>

                      <span>
                        {table.record_count} records
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}

          {/* Selected Table Details */}

          {tableDetails && (
            <>

              <div className="dataset-section-heading">
                <div>
                  <h3>{tableDetails.name}</h3>
                  <p>
                    {tableDetails.record_count} total records
                  </p>
                </div>
              </div>

              <h4>Table Schema</h4>

              <div className="dataset-table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Data Type</th>
                      <th>Nullable</th>
                      <th>Primary Key</th>
                    </tr>
                  </thead>

                  <tbody>
                    {tableDetails.columns.map((column) => (
                      <tr key={column.name}>
                        <td className="dataset-column-name">
                          {column.name}
                        </td>

                        <td>
                          <span className="type-badge">
                            {column.type || "UNDEFINED"}
                          </span>
                        </td>

                        <td>
                          {column.nullable ? "Yes" : "No"}
                        </td>

                        <td>
                          {column.primary_key ? "Yes" : "No"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="dataset-section-heading">
                <div>
                  <h3>Record Preview</h3>
                  <p>
                    Showing up to 10 records from SQLite.
                  </p>
                </div>

                <Table size={20} />
              </div>

              <div className="dataset-table-wrapper">
                <table>
                  <thead>
                    <tr>
                      {tableDetails.columns.map((column) => (
                        <th key={column.name}>
                          {column.name}
                        </th>
                      ))}
                    </tr>
                  </thead>

                  <tbody>
                    {tableDetails.records.map((record, index) => (
                      <tr key={index}>
                        {tableDetails.columns.map((column) => (
                          <td key={column.name}>
                            {record[column.name] == null
                              ? "NULL"
                              : String(record[column.name])}
                          </td>
                        ))}
                      </tr>
                    ))}

                    {tableDetails.records.length === 0 && (
                      <tr>
                        <td colSpan={tableDetails.columns.length}>
                          No records found.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

            </>
          )}

        </section>

      )}

    </div>
  );
}
