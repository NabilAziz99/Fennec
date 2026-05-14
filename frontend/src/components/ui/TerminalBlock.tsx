import { useState, useEffect, useRef } from 'react'
import { useInView } from 'framer-motion'

interface TerminalBlockProps {
  command: string
  delay?: number
  className?: string
}

export default function TerminalBlock({ command, delay = 0, className = '' }: TerminalBlockProps) {
  const [displayed, setDisplayed] = useState('')
  const [started, setStarted] = useState(false)
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true })
  const indexRef = useRef(0)

  useEffect(() => {
    if (!isInView) return
    const timeout = setTimeout(() => setStarted(true), delay)
    return () => clearTimeout(timeout)
  }, [isInView, delay])

  useEffect(() => {
    if (!started) return

    indexRef.current = 0
    setDisplayed('')

    const interval = setInterval(() => {
      if (indexRef.current >= command.length) {
        clearInterval(interval)
        return
      }
      indexRef.current++
      setDisplayed(command.slice(0, indexRef.current))
    }, 40)

    return () => clearInterval(interval)
  }, [started, command])

  return (
    <div
      ref={ref}
      className={`bg-dark-elevated border border-dark-border rounded-lg p-4 font-mono text-sm ${className}`}
    >
      <div className="flex items-center gap-1.5 mb-3">
        <div className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
        <div className="w-2.5 h-2.5 rounded-full bg-green-500/70" />
        <span className="ml-2 text-text-muted text-xs">terminal</span>
      </div>
      <div className="text-text-secondary">
        <span className="text-fennec-lime">$</span>{' '}
        <span>{displayed}</span>
        {displayed.length < command.length && (
          <span className="inline-block w-[7px] h-[14px] bg-fennec-lime/80 ml-0.5 align-middle animate-blink" />
        )}
      </div>
    </div>
  )
}
