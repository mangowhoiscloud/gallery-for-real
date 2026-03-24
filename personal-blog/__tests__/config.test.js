const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')

describe('TypeScript configuration', () => {
  let tsconfig

  beforeAll(() => {
    const raw = fs.readFileSync(path.join(root, 'tsconfig.json'), 'utf8')
    tsconfig = JSON.parse(raw)
  })

  it('has strict mode enabled', () => {
    expect(tsconfig.compilerOptions.strict).toBe(true)
  })

  it('has noEmit enabled', () => {
    expect(tsconfig.compilerOptions.noEmit).toBe(true)
  })

  it('defines @/* path alias pointing to project root', () => {
    const paths = tsconfig.compilerOptions.paths
    expect(paths).toBeDefined()
    expect(paths['@/*']).toEqual(['./*'])
  })

  it('targets ES2017 or later', () => {
    const target = tsconfig.compilerOptions.target
    expect(['ES2017', 'ES2018', 'ES2019', 'ES2020', 'ES2021', 'ES2022', 'ES2023', 'ESNext']).toContain(target)
  })

  it('uses bundler module resolution for Next.js 15', () => {
    expect(tsconfig.compilerOptions.moduleResolution).toBe('bundler')
  })
})

describe('Next.js configuration', () => {
  it('next.config.ts file exists', () => {
    const exists = fs.existsSync(path.join(root, 'next.config.ts'))
    expect(exists).toBe(true)
  })
})

describe('PostCSS configuration', () => {
  let postcssConfig

  beforeAll(() => {
    // Read the mjs file as text and verify @tailwindcss/postcss is referenced
    const raw = fs.readFileSync(path.join(root, 'postcss.config.mjs'), 'utf8')
    postcssConfig = raw
  })

  it('references @tailwindcss/postcss plugin', () => {
    expect(postcssConfig).toContain('@tailwindcss/postcss')
  })
})
