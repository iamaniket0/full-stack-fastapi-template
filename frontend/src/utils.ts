import { AxiosError } from "axios"

function extractErrorMessage(err: Error): string {
  if (err instanceof AxiosError) {
    const errDetail = (err.response?.data as any)?.detail
    if (Array.isArray(errDetail) && errDetail.length > 0) {
      return errDetail[0].msg
    }
    if (typeof errDetail === "string") {
      return errDetail
    }
    return err.message
  }
  return "Something went wrong."
}

export const handleError = function (this: (msg: string) => void, err: Error) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}

const escapeCsvValue = (value: unknown): string => {
  if (value === null || value === undefined) return ""
  const str = String(value)
  if (/[",\r\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

export const toCsv = <T extends Record<string, unknown>>(
  rows: T[],
  columns: (keyof T & string)[],
): string => {
  const header = columns.map(escapeCsvValue).join(",")
  const body = rows.map((row) =>
    columns.map((col) => escapeCsvValue(row[col])).join(","),
  )
  return [header, ...body].join("\r\n")
}

export const downloadCsv = (filename: string, csv: string) => {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
