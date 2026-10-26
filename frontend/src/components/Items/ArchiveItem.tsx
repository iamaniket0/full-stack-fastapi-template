import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Archive, ArchiveRestore } from "lucide-react"

import { type ItemPublic, ItemsService } from "@/client"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ArchiveItemProps {
  item: ItemPublic
  onSuccess: () => void
}

const ArchiveItem = ({ item, onSuccess }: ArchiveItemProps) => {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const archived = item.archived ?? false

  const mutation = useMutation({
    mutationFn: async () => {
      const options = { path: { id: item.id } }
      if (archived) {
        await ItemsService.unarchiveItem(options)
      } else {
        await ItemsService.archiveItem(options)
      }
    },
    onSuccess: () => {
      showSuccessToast(
        archived
          ? "The item was unarchived successfully"
          : "The item was archived successfully",
      )
      onSuccess()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  return (
    <DropdownMenuItem
      disabled={mutation.isPending}
      onSelect={(e) => e.preventDefault()}
      onClick={() => mutation.mutate()}
    >
      {archived ? <ArchiveRestore /> : <Archive />}
      {archived ? "Unarchive" : "Archive"}
    </DropdownMenuItem>
  )
}

export default ArchiveItem
