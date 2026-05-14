import { motion, useInView } from 'framer-motion'
import { useRef, createElement } from 'react'

interface RedactedTextProps {
  text: string
  as?: 'h1' | 'h2' | 'h3' | 'p' | 'span'
  className?: string
  staggerDelay?: number
}

export default function RedactedText({ text, as = 'h2', className = '', staggerDelay = 0.12 }: RedactedTextProps) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-80px' })

  const words = text.split(' ')

  const content = (
    <span ref={ref} className="inline">
      {words.map((word, i) => (
        <span key={i} className="relative inline-block mr-[0.3em]">
          <span className="invisible">{word}</span>
          <motion.span
            className="absolute inset-0 flex items-center"
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : {}}
            transition={{ delay: i * staggerDelay, duration: 0.01 }}
          >
            {word}
          </motion.span>
          <motion.span
            className="absolute inset-0 bg-fennec-lime rounded-sm"
            initial={{ scaleX: 1 }}
            animate={isInView ? { scaleX: 0 } : {}}
            transition={{ delay: i * staggerDelay, duration: 0.4, ease: 'easeInOut' }}
            style={{ transformOrigin: 'right' }}
          />
        </span>
      ))}
    </span>
  )

  return createElement(as, { className }, content)
}
