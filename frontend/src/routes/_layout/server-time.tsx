import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import { UtilsService } from "@/client"
import { Skeleton } from "@/components/ui/skeleton"

// Re-sync with the server periodically; tick locally in between
const SYNC_INTERVAL_MS = 30_000

function getServerTimeQueryOptions() {
  return {
    queryFn: async () => {
      const { data } = await UtilsService.serverTime()
      // Offset between server and client clocks, so we can tick locally
      return new Date(data.server_time).getTime() - Date.now()
    },
    queryKey: ["server-time"],
    refetchInterval: SYNC_INTERVAL_MS,
  }
}

export const Route = createFileRoute("/_layout/server-time")({
  component: ServerTime,
  head: () => ({
    meta: [
      {
        title: "Server Time - FastAPI Template",
      },
    ],
  }),
})

function ServerTimeClock() {
  const { data: offset, isError } = useQuery(getServerTimeQueryOptions())
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  if (isError) {
    return <p className="text-destructive">Could not load the server time.</p>
  }

  if (offset === undefined) {
    return <Skeleton className="h-24 w-full max-w-md" />
  }

  const serverNow = new Date(now + offset)

  return (
    <div className="rounded-xl border p-6 max-w-md" data-testid="server-time">
      <p className="text-4xl font-semibold tabular-nums">
        {serverNow.toLocaleTimeString()}
      </p>
      <p className="text-muted-foreground">
        {serverNow.toLocaleDateString(undefined, { dateStyle: "full" })}
      </p>
      <p className="text-sm text-muted-foreground mt-4">
        UTC: {serverNow.toISOString()}
      </p>
    </div>
  )
}

function ServerTime() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Server Time</h1>
        <p className="text-muted-foreground">
          The current time on the server, shown in your local time zone
        </p>
      </div>
      <ServerTimeClock />
    </div>
  )
}
