import { X } from 'lucide-react'
import type { UploadItem } from '@/features/chat/types'

type UploadStripProps = {
  uploads: UploadItem[]
  onRemove: (id: string) => void
}

export function UploadStrip({ uploads, onRemove }: UploadStripProps) {
  // 条件渲染:无上传时不显示
  if (uploads.length === 0) return null

  return (
    <div className="flex overflow-x-auto gap-2 pb-2 px-1 custom-scrollbar">
      {uploads.map((img) => (
        <div key={img.id} className="relative shrink-0 group">
          <img
            src={img.dataUrl}
            className="h-16 w-16 object-cover rounded-lg border shadow-sm"
            alt={img.name}
          />
          <button
            onClick={() => onRemove(img.id)}
            className="absolute -top-1.5 -right-1.5 bg-destructive text-destructive-foreground rounded-full p-0.5 shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
            aria-label="删除图片"
          >
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
    </div>
  )
}
