// Blocking script injected before page paint to prevent FOUC.
// Reads localStorage 'theme' key; falls back to system prefers-color-scheme.
// Must remain a single-line string — no template literals with line breaks.
export const THEME_SCRIPT =
  "(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||(t===null&&window.matchMedia('(prefers-color-scheme:dark)').matches)){document.documentElement.classList.add('dark');}}catch(e){}})();"
