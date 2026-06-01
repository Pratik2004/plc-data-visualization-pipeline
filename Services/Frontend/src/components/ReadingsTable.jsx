import { useEffect, useMemo, useState } from "react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import client from "../api/client";

export default function ReadingsTable() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [pageIndex, setPageIndex] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const [sortBy, setSortBy] = useState("time");
  const [sortOrder, setSortOrder] = useState("DESC");
  const [search, setSearch] = useState("");

  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    async function fetchReadings() {
      setLoading(true);
      setError("");

      try {
        const response = await client.get("/api/v1/readings", {
          params: {
            page: pageIndex + 1,
            pagesize: pageSize,
            sortby: sortBy,
            sortorder: sortOrder,
            search: search || undefined,
          },
        });

        const payload = response.data?.data || {};
        setRows(payload.readings || []);
        setTotalCount(payload.totalcount || 0);
        setTotalPages(payload.totalpages || 0);
      } catch (err) {
        console.error("Error fetching readings:", err);
        setError(err.response?.data?.detail || err.message || "Failed to fetch readings");
        setRows([]);
        setTotalCount(0);
        setTotalPages(0);
      } finally {
        setLoading(false);
      }
    }

    fetchReadings();
  }, [pageIndex, pageSize, sortBy, sortOrder, search]);

  const columns = useMemo(
    () => [
      {
        id: "asset",
        header: "Asset",
        accessorFn: (row) => row.asset?.name ?? "",
        enableSorting: false,
      },
      {
        id: "tag",
        header: "Tag",
        accessorFn: (row) => row.tag?.name ?? "",
        enableSorting: false,
      },
      {
        id: "time",
        header: "Time",
        accessorFn: (row) => row.time ?? "",
        enableSorting: true,
        sortKey: "time",
        cell: ({ getValue }) => {
          const value = getValue();
          return value ? new Date(value).toLocaleString() : "-";
        },
      },
      {
        id: "value",
        header: "Value",
        accessorFn: (row) => row.value ?? "",
        enableSorting: true,
        sortKey: "value",
        cell: ({ getValue }) => {
          const value = getValue();
          return value !== null && value !== undefined ? Number(value).toFixed(2) : "-";
        },
      },
      {
        id: "unit",
        header: "Unit",
        accessorFn: (row) => row.tag?.unit ?? "",
        enableSorting: false,
      },
      {
        id: "quality",
        header: "Quality",
        accessorFn: (row) => row.quality ?? "",
        enableSorting: true,
        sortKey: "quality",
        cell: ({ getValue }) => {
          const value = getValue();
          const className =
            value === "GOOD"
              ? "bg-green-100 text-green-800"
              : value === "UNCERTAIN"
              ? "bg-yellow-100 text-yellow-800"
              : "bg-red-100 text-red-800";

          return (
            <span className={`rounded px-2 py-1 text-xs font-medium ${className}`}>
              {value || "UNKNOWN"}
            </span>
          );
        },
      },
      {
        id: "source",
        header: "Source",
        accessorFn: (row) => row.source ?? "",
        enableSorting: false,
      },
    ],
    []
  );

  const table = useReactTable({
    data: rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  function handleSort(columnDef) {
    if (!columnDef.enableSorting || !columnDef.sortKey) return;

    const nextSortBy = columnDef.sortKey;

    if (sortBy === nextSortBy) {
      setSortOrder((prev) => (prev === "ASC" ? "DESC" : "ASC"));
    } else {
      setSortBy(nextSortBy);
      setSortOrder("ASC");
    }

    setPageIndex(0);
  }

  return (
    <div className="p-6">
      <h1 className="mb-6 text-3xl font-bold">Readings History</h1>

      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPageIndex(0);
          }}
          placeholder="Search by asset or tag..."
          className="w-full max-w-md rounded border px-3 py-2"
        />

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Rows per page</label>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPageIndex(0);
            }}
            className="rounded border px-3 py-2"
          >
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {loading && (
        <div className="mb-4 rounded bg-blue-50 p-3 text-blue-700">Loading readings...</div>
      )}

      {error && (
        <div className="mb-4 rounded bg-red-50 p-3 text-red-700">{error}</div>
      )}

      {!loading && !error && rows.length === 0 && (
        <div className="mb-4 rounded bg-yellow-50 p-3 text-yellow-800">
          No readings found.
        </div>
      )}

      <div className="overflow-x-auto rounded border">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className={`border-b px-4 py-2 text-left select-none ${
                      header.column.columnDef.enableSorting ? "cursor-pointer" : "cursor-default"
                    }`}
                    onClick={() => handleSort(header.column.columnDef)}
                  >
                    <span className="inline-flex items-center gap-1">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}

                      {header.column.columnDef.enableSorting &&
                      header.column.columnDef.sortKey === sortBy ? (
                        <span>{sortOrder === "ASC" ? "↑" : "↓"}</span>
                      ) : null}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>

          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="border-b px-4 py-2">
                    {flexRender(
                      cell.column.columnDef.cell ?? (() => cell.getValue?.() ?? "-"),
                      cell.getContext()
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="text-sm text-gray-600">
          Total {totalCount} records | Page {pageIndex + 1} of {totalPages || 1}
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setPageIndex((prev) => Math.max(0, prev - 1))}
            disabled={pageIndex === 0 || loading}
            className="rounded border px-4 py-2 disabled:opacity-50"
          >
            Previous
          </button>

          <button
            type="button"
            onClick={() =>
              setPageIndex((prev) =>
                totalPages > 0 ? Math.min(totalPages - 1, prev + 1) : prev + 1
              )
            }
            disabled={loading || totalPages === 0 || pageIndex >= totalPages - 1}
            className="rounded border px-4 py-2 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}