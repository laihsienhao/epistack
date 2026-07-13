import streamlit.components.v1 as components

_IFRAME_TITLE = "streamlit_agraph.agraph"

_HTML = f"""
<div id="zoom-controls">
  <button id="zoom-out" title="Zoom out">−</button>
  <button id="zoom-in" title="Zoom in">+</button>
</div>
<style>
  body {{ margin: 0; }}
  #zoom-controls {{
    display: flex;
    justify-content: flex-end;
    gap: 6px;
    font-family: system-ui, -apple-system, sans-serif;
  }}
  #zoom-controls button {{
    width: 32px;
    height: 32px;
    border-radius: 6px;
    border: 1px solid rgba(49, 51, 63, 0.2);
    background: #ffffff;
    color: #31333f;
    font-size: 16px;
    cursor: pointer;
    line-height: 1;
  }}
  #zoom-controls button:hover {{
    background: #f0f2f6;
  }}
  @media (prefers-color-scheme: dark) {{
    #zoom-controls button {{
      background: #262730;
      color: #fafafa;
      border-color: rgba(250, 250, 250, 0.2);
    }}
    #zoom-controls button:hover {{
      background: #31333f;
    }}
  }}
</style>
<script>
(function() {{
  function getIframeDoc() {{
    var iframe = window.parent.document.querySelector('iframe[title="{_IFRAME_TITLE}"]');
    if (!iframe) return null;
    return iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
  }}

  function getIframeEl() {{
    return window.parent.document.querySelector('iframe[title="{_IFRAME_TITLE}"]');
  }}

  function getCanvas() {{
    var doc = getIframeDoc();
    return doc ? doc.querySelector('.vis-network canvas') : null;
  }}

  // The canvas is much wider than most browser windows, so the user is
  // usually only looking at part of it. Anchoring zoom on the canvas's own
  // geometric center (fixed, off in whatever direction the canvas extends
  // beyond the window) makes it feel like it's zooming into a corner.
  // Anchor on the center of whatever's actually visible on screen instead.
  function computeAnchor(canvas) {{
    var iframeEl = getIframeEl();
    var canvasRect = canvas.getBoundingClientRect(); // relative to the agraph iframe's own viewport
    if (!iframeEl) {{
      return {{x: canvasRect.left + canvasRect.width / 2, y: canvasRect.top + canvasRect.height / 2}};
    }}
    var iframeRect = iframeEl.getBoundingClientRect(); // relative to the parent window's viewport
    var canvasLeftInParent = iframeRect.left + canvasRect.left;
    var canvasTopInParent = iframeRect.top + canvasRect.top;
    var parentWidth = window.parent.innerWidth;
    var parentHeight = window.parent.innerHeight;

    var visLeft = Math.max(canvasLeftInParent, 0);
    var visTop = Math.max(canvasTopInParent, 0);
    var visRight = Math.min(canvasLeftInParent + canvasRect.width, parentWidth);
    var visBottom = Math.min(canvasTopInParent + canvasRect.height, parentHeight);

    if (visRight <= visLeft || visBottom <= visTop) {{
      return {{x: canvasRect.left + canvasRect.width / 2, y: canvasRect.top + canvasRect.height / 2}};
    }}

    var centerParentX = (visLeft + visRight) / 2;
    var centerParentY = (visTop + visBottom) / 2;

    // convert back into the agraph iframe's own local coordinate system,
    // since that's what the dispatched event's clientX/clientY must be in
    return {{x: centerParentX - iframeRect.left, y: centerParentY - iframeRect.top}};
  }}

  // Plain scroll over the graph should scroll the page, not zoom it -- only
  // ctrl/cmd+scroll (or pinch, which browsers report as a ctrlKey wheel
  // event) should reach vis-network's own native zoom handler. Installed on
  // the iframe's document in the capture phase so it runs before
  // vis-network's own listener ever sees the event.
  function installScrollGuard() {{
    var doc = getIframeDoc();
    if (!doc || doc.__zoomScrollGuard) return;
    doc.__zoomScrollGuard = true;
    doc.addEventListener('wheel', function(e) {{
      if (!e.ctrlKey && !e.metaKey) {{
        e.stopPropagation();
      }}
    }}, {{capture: true}});
  }}

  // The +/- buttons dispatch a synthetic wheel event at the visible-viewport
  // anchor with ctrlKey set, so they drive vis-network's own zoom handler
  // directly -- real native zoom, never out of sync with click hit-testing,
  // just triggered by a button instead of a gesture.
  //
  // vis-network applies a *fixed* scale step per wheel event regardless of
  // deltaY's magnitude (confirmed empirically -- -0.1 and -240 produce an
  // identical step), and applies it instantly with no internal animation of
  // its own. So the only way to get a progressive, smooth-looking shift
  // instead of one instant snap is to lower `zoomSpeed` in the graph config
  // (see graph_view.py) and fire *several* real ticks across a few
  // animation frames -- each is a genuine, fully-valid vis-network zoom
  // state (so click hit-testing stays correct throughout), just smaller and
  // spread out rather than one big jump. `zoomSpeed` in graph_view.py sets
  // how much each tick moves; TICKS here sets how many ticks make up one
  // click -- together they set both the smoothness and the total distance
  // covered per click.
  var ZOOM_TICKS = 8;

  function dispatchZoomWheel(direction) {{
    var canvas = getCanvas();
    if (!canvas) return;
    var anchor = computeAnchor(canvas);
    var i = 0;
    function tick() {{
      if (i >= ZOOM_TICKS) return;
      var evt = new WheelEvent('wheel', {{
        deltaY: direction * 120,
        clientX: anchor.x,
        clientY: anchor.y,
        ctrlKey: true,
        bubbles: true,
        cancelable: true,
      }});
      canvas.dispatchEvent(evt);
      i++;
      requestAnimationFrame(tick);
    }}
    tick();
  }}

  document.getElementById('zoom-out').onclick = function() {{ dispatchZoomWheel(1); }};
  document.getElementById('zoom-in').onclick = function() {{ dispatchZoomWheel(-1); }};

  installScrollGuard();
  var retry = setInterval(function() {{
    installScrollGuard();
  }}, 400);
  setTimeout(function() {{ clearInterval(retry); }}, 15000);
}})();
</script>
"""


def render_zoom_controls() -> None:
    """Zoom buttons that drive vis-network's own native zoom via a burst of
    real ctrl+wheel ticks (rather than one big jump, or a CSS transform) --
    native zoom keeps click hit-testing correctly in sync, which a CSS-only
    scale does not, and the multi-tick burst gives a brief smooth shift
    instead of a snap. Pairs with `zoomSpeed` in graph_view.py's Config --
    that must be lowered to roughly 1/ZOOM_TICKS so the compounded effect of
    one full click matches a single default-speed tick. A capture-phase
    guard on the iframe's
    own document keeps plain scrolling (no ctrl/cmd) from being hijacked into
    a zoom, since vis-network's zoomView must stay enabled for the native
    zoom path to work at all."""
    components.html(_HTML, height=42)
