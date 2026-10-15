import { useMutation } from "@tanstack/react-query"
import { Download } from "lucide-react"

import { ItemsService } from "@/client"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { downloadCsv, handleError, toCsv } from "@/utils"

const CSV_COLUMNS = [
  "id",
  "title",
  "description",
  "owner_id",
  "created_at",
] as const

const DownloadCsv = () => {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: async () =>
      (await ItemsService.readItems({ query: { skip: 0, limit: 1000 } })).data,
    onSuccess: (items) => {
      const csv = toCsv(items.data, [...CSV_COLUMNS])
      downloadCsv("items.csv", csv)
      showSuccessToast("CSV downloaded successfully")
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <LoadingButton
      variant="outline"
      loading={mutation.isPending}
      onClick={() => mutation.mutate()}
    >
      <Download />
      Download CSV
    </LoadingButton>
  )
}

export default DownloadCsv
