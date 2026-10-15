import { useMutation } from "@tanstack/react-query"
import { Download } from "lucide-react"

import { ItemsService } from "@/client"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { downloadCsv, handleError } from "@/utils"

const DownloadCsv = () => {
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const mutation = useMutation({
    mutationFn: async () => (await ItemsService.exportItems()).data as string,
    onSuccess: (csv) => {
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
