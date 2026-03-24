// Mock for next/font/* — returns a stable object for any font constructor call.
module.exports = new Proxy(
  {},
  {
    get: function (_, fontName) {
      return function () {
        return {
          className: `mock-${String(fontName).toLowerCase()}`,
          variable: `--font-${String(fontName).toLowerCase().replace(/_/g, '-')}`,
          style: { fontFamily: String(fontName) },
        }
      }
    },
  }
)
