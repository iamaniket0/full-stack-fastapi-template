import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { Suspense, useState } from "react"

import { ItemsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import DownloadCsv from "@/components/Common/DownloadCsv"
import AddItem from "@/components/Items/AddItem"
import { columns } from "@/components/Items/columns"
import PendingItems from "@/components/Pending/PendingItems"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

function getItemsQueryOptions(includeArchived: boolean) {
  return {
    queryFn: async () =>
      (
        await ItemsService.readItems({
          query: { skip: 0, limit: 100, include_archived: includeArchived },
        })
      ).data,
    queryKey: ["items", { includeArchived }],
  }
}

export const Route = createFileRoute("/_layout/items")({
  component: Items,
  head: () => ({
    meta: [
      {
        title: "Items - FastAPI Template",
      },
    ],
  }),
})

function ItemsTableContent({ includeArchived }: { includeArchived: boolean }) {
  const { data: items } = useSuspenseQuery(
    getItemsQueryOptions(includeArchived),
  )

  if (items.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Search className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">You don't have any items yet</h3>
        <p className="text-muted-foreground">Add a new item to get started</p>
      </div>
    )
  }

  return <DataTable columns={columns} data={items.data} />
}

function ItemsTable({ includeArchived }: { includeArchived: boolean }) {
  return (
    <Suspense fallback={<PendingItems />}>
      <ItemsTableContent includeArchived={includeArchived} />
    </Suspense>
  )
}

function Items() {
  const [showArchived, setShowArchived] = useState(false)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Items</h1>
          <p className="text-muted-foreground">Create and manage your items</p>
        </div>
        <AddItem />
      </div>
      <div className="flex items-center justify-end gap-4">
        <div className="flex items-center gap-2">
          <Checkbox
            id="show-archived"
            checked={showArchived}
            onCheckedChange={(checked) => setShowArchived(checked === true)}
          />
          <Label htmlFor="show-archived" className="font-normal">
            Show archived
          </Label>
        </div>
        <DownloadCsv />
      </div>
      <ItemsTable includeArchived={showArchived} />
    </div>
  )
}
