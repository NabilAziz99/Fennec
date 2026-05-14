import { useState, useEffect, useRef } from 'react'

interface GlitchTextProps {
  text: string
  speed?: number
  delay?: number
  className?: string
}

const GLITCH_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'

export default function GlitchText({ text, speed = 30, delay = 0, className = '' }: GlitchTextProps) {
  const [displayed, setDisplayed] = useState('')
  const [started, setStarted] = useState(false)
  const indexRef = useRef(0)
  const glitchCountRef = useRef(0)

  useEffect(() => {
    const timeout = setTimeout(() => setStarted(true), delay)
    return () => clearTimeout(timeout)
  }, [delay])

  useEffect(() => {
    if (!started) return

    indexRef.current = 0
    glitchCountRef.current = 0
    setDisplayed('')

    const interval = setInterval(() => {
      if (indexRef.current >= text.length) {
        clearInterval(interval)
        setDisplayed(text)
        return
      }

      const currentChar = text[indexRef.current]

      // Every few characters, do a brief glitch (show random char before resolving)
      if (glitchCountRef.current > 0) {
        glitchCountRef.current--
        const glitchChar = GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)]
        setDisplayed(text.slice(0, indexRef.current) + glitchChar)
        return
      }

      // Randomly trigger a glitch cycle (2-3 frames of random chars)
      if (currentChar !== ' ' && Math.random() < 0.3) {
        glitchCountRef.current = 2 + Math.floor(Math.random() * 2)
        const glitchChar = GLITCH_CHARS[Math.floor(Math.random() * GLITCH_CHARS.length)]
        setDisplayed(text.slice(0, indexRef.current) + glitchChar)
        return
      }

      indexRef.current++
      setDisplayed(text.slice(0, indexRef.current))
    }, speed)

    return () => clearInterval(interval)
  }, [started, text, speed])

  return (
    <span className={className}>
      {displayed}
      {started && displayed.length < text.length && (
        <span className="inline-block w-[2px] h-[0.9em] bg-fennec-lime ml-0.5 align-middle animate-blink" />
      )}
    </span>
  )
}
