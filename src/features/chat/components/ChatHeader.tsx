import { RotateCcw, Settings, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

type ChatHeaderProps = {
  sessionId: string
  loading: boolean
  onReset: () => void
  onOpenSettings?: () => void
}

export function ChatHeader({ sessionId, loading, onReset, onOpenSettings }: ChatHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b bg-background/95 backdrop-blur px-4 py-3">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-bold flex items-center gap-2">✨ Gemini 图像创作</h1>
        {loading && (
          <Badge variant="secondary" className="gap-1 animate-pulse">
            <Loader2 className="h-3 w-3 animate-spin" />
            <span className="text-xs">生成中…</span>
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span className="hidden sm:inline-block text-xs">
          会话: {sessionId.slice(0, 8)}
        </span>
        {onOpenSettings && (
          <Button variant="ghost" size="icon" onClick={onOpenSettings} title="设置" className="h-8 w-8">
            <Settings className="h-4 w-4" />
          </Button>
        )}
        <Button variant="ghost" size="icon" onClick={onReset} title="重置对话" disabled={loading} className="h-8 w-8">
          <RotateCcw className="h-4 w-4" />
        </Button>
      </div>
    </header>
  )
}
