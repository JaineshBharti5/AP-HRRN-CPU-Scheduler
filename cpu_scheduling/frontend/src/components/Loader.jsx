import './loader.css'

// Speeder loader. overlay=true covers the parent (which must be position: relative);
// overlay=false renders it inline in a fixed-height box.
export default function Loader({ overlay = true, text = 'Running simulation' }) {
  return (
    <div className={`loader-wrap ${overlay ? 'overlay' : 'inline'}`} role="status" aria-live="polite">
      <div className="longfazers" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>

      <div className="speeder" aria-hidden="true">
        <span>
          <span />
          <span />
          <span />
          <span />
        </span>
        <div className="base">
          <span />
          <div className="face" />
        </div>
      </div>

      <div className="loader-text">
        <strong>{text}</strong>
        <div className="loader-bar">
          <div />
        </div>
      </div>
    </div>
  )
}
