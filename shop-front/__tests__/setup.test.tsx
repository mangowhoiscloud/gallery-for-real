/**
 * Item 1 acceptance tests:
 * - Jest config initializes without errors
 * - A minimal component snapshot test can run
 * - Path alias @/ resolves correctly
 */
import React from 'react'
import { render } from '@testing-library/react'

// Verify @testing-library/jest-dom matchers are available (from jest.setup.ts)
describe('Jest setup', () => {
  it('initializes @testing-library/jest-dom matchers', () => {
    const { container } = render(<div data-testid="hello">Hello</div>)
    // If jest-dom is loaded, toBeInTheDocument is available
    expect(container.firstChild).toBeInTheDocument()
  })

  it('renders a minimal React component', () => {
    function Greeting({ name }: { name: string }) {
      return <p>Hello, {name}!</p>
    }
    const { getByText } = render(<Greeting name="World" />)
    expect(getByText('Hello, World!')).toBeInTheDocument()
  })

  it('snapshot: minimal component matches snapshot', () => {
    function Badge({ label }: { label: string }) {
      return <span className="badge">{label}</span>
    }
    const { container } = render(<Badge label="Test" />)
    expect(container).toMatchSnapshot()
  })
})

// Verify path alias resolution — import from @/ works
describe('Path alias', () => {
  it('@/ alias resolves — no import error thrown', async () => {
    // Dynamic import via @/ to verify tsconfig paths are mapped in jest
    // We import the style mock which exists at the root
    expect(() => require('@/__mocks__/styleMock')).not.toThrow()
  })
})
